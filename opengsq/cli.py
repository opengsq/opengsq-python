import argparse
import asyncio
import inspect
import json
import os
import re
import sys
from functools import partial
from pydoc import locate
from typing import Mapping, Sequence

from opengsq.protocol_base import ProtocolBase
from opengsq.version import __version__


class CLI:
    def __init__(self):
        self.__paths = {}

    def register(self, parser: argparse.ArgumentParser):
        # Add version argument
        parser.add_argument(
            "-V",
            "--version",
            action="store_true",
            help="print the opengsq version number and exit",
        )

        opengsq_path = os.path.abspath(os.path.dirname(__file__))
        subparsers = parser.add_subparsers(dest="subparser_name")
        pattern = re.compile(r"from\s+(\S+)\s+import\s+(.+,?\S)")

        # Load all protocols from __init__.py
        with open(os.path.join(opengsq_path, "protocols", "__init__.py")) as f:
            for protocol_path, protocol_classnames in re.findall(pattern, f.read()):
                for protocol_classname in protocol_classnames.split(","):
                    name, fullpath, parameters = self.__extract(
                        protocol_path, protocol_classname
                    )

                    # Save to self.__paths dictionary
                    # Example: name = 'source', fullpath = 'opengsq.protocols.source.Source'
                    self.__paths[name] = fullpath

                    # Add parser and arguments
                    obj: ProtocolBase = locate(fullpath)
                    sub = subparsers.add_parser(name, help=obj.full_name)
                    self.__add_arguments(sub, parameters)

                    method_names = [
                        func
                        for func in dir(obj)
                        if callable(getattr(obj, func)) and func.startswith("get_")
                    ]

                    sub.add_argument(
                        "--function",
                        default=method_names[0],
                        type=str,
                        help="(default: %(default)s)",
                    )
                    sub.add_argument("--indent", default=None, type=int, nargs="?")

    # Get the query response in json format
    async def run(self, args: Sequence[str]) -> str:
        # Return version if -V or --version
        if args.version:
            return "v" + __version__
        else:
            del args.version

        # Load the obj from path
        obj = locate(self.__paths[args.subparser_name])
        del args.subparser_name

        function = args.function
        del args.function

        indent = args.indent
        del args.indent

        # Bind values to obj parameters
        for value in vars(args).values():
            obj = partial(obj, value)

        # Create obj()
        protocol: ProtocolBase = obj()
        func = getattr(protocol, function)

        return json.dumps(
            await func(),
            ensure_ascii=False,
            indent=indent,
            default=lambda o: o.__dict__,
        )

    # Extract name, fullpath, parameters from path, classname
    def __extract(self, path: str, classname: str):
        name = path.split(".")[-1]
        fullpath = "{}.{}".format(path, classname.strip())
        parameters = inspect.signature(locate(fullpath).__init__).parameters

        return name, fullpath, parameters

    def __add_arguments(
        self, sub: argparse.ArgumentParser, parameters: Mapping[str, inspect.Parameter]
    ):
        for key in parameters:
            if parameters[key].name == "self":
                continue

            name_or_flags = "--{}".format(parameters[key].name)
            required = parameters[key].default == inspect._empty
            default = None if required else parameters[key].default

            type_mapping = {"str": str, "int": int, "float": float}
            type_func = type_mapping.get(
                parameters[key].annotation, parameters[key].annotation
            )

            help = None if required else "(default: %(default)s)"

            sub.add_argument(
                name_or_flags,
                default=default,
                required=required,
                type=type_func,
                help=help,
            )


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()


async def main_async():
    cli = CLI()

    parser = argparse.ArgumentParser()
    cli.register(parser)

    if len(sys.argv) <= 1:
        parser.print_help(sys.stderr)
        sys.exit(-1)

    try:
        args = parser.parse_args()
        result = await cli.run(args)
        sys.stdout.write(result)
    except asyncio.exceptions.TimeoutError:
        sys.stderr.write("opengsq: error: timed out\n")
        sys.exit(-2)

    sys.exit(0)


if __name__ == "__main__":
    main()
