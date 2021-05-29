import argparse
import inspect
import os
import re
from functools import partial
from pydoc import locate
from typing import Mapping, Sequence

from opengsq.protocols.protocol_interface import IProtocol


class CLI:
    def __init__(self):
        self.__paths = {}

    def register(self, parser: argparse.ArgumentParser):
        opengsq_path = os.path.abspath(os.path.dirname(__file__))
        subparsers = parser.add_subparsers(dest='subparser_name')
        pattern = re.compile(r'from\s+(\S+)\s+import\s+(.+,?\S)')

        # Load all protocols from __init__.py
        with open(os.path.join(opengsq_path, 'protocols', '__init__.py')) as f:
            for (protocol_path, protocol_classnames) in re.findall(pattern, f.read()):
                for protocol_classname in protocol_classnames.split(','):
                    name, fullpath, parameters = self.__extract(protocol_path, protocol_classname)
                    subparser_name = 'protocol-{}'.format(name)

                    # Save to self.__paths dictionary
                    # Example: subparser_name = 'protocol-a2s', fullpath = 'opengsq.protocols.a2s.A2S'
                    self.__paths[subparser_name] = fullpath

                    # Add parser and arguments
                    sub = subparsers.add_parser(subparser_name, help='{} protocol'.format(protocol_classname))
                    self.__add_arguments(sub, parameters)

        # Load all servers from __init__.py
        with open(os.path.join(opengsq_path, 'servers', '__init__.py')) as f:
            for (server_path, server_classnames) in re.findall(pattern, f.read()):
                for server_classname in server_classnames.split(','):
                    name, fullpath, parameters = self.__extract(server_path, server_classname)

                    # Save to self.__paths dictionary
                    # Example: name = 'csgo', fullpath = 'opengsq.servers.csgo.CSGO'
                    self.__paths[name] = fullpath

                    # Add parser and arguments
                    sub = subparsers.add_parser(name, help=locate(fullpath).full_name)
                    self.__add_arguments(sub, parameters)

    # Get the query response in json format
    def run(self, args: Sequence[str]) -> str:
        # Load the obj from path
        obj = locate(self.__paths[args.subparser_name])
        del args.subparser_name

        # Bind values to obj parameters
        for value in vars(args).values():
            obj = partial(obj, value)

        # Create obj()
        server: IProtocol = obj()

        return server.query().to_json()

    # Extract name, fullpath, parameters from path, classname
    def __extract(self, path: str, classname: str):
        name = path.split('.')[-1]
        fullpath = '{}.{}'.format(path, classname.strip())
        parameters = inspect.signature(locate(fullpath).__init__).parameters

        return name, fullpath, parameters

    def __add_arguments(self, sub: argparse.ArgumentParser, parameters: Mapping[str, inspect.Parameter]):
        for key in parameters:
            if parameters[key].name == 'self':
                continue

            name_or_flags = '--{}'.format(parameters[key].name)
            required = parameters[key].default == inspect._empty
            default = None if required else parameters[key].default
            type = parameters[key].annotation
            help = None if required else '(default: %(default)s)'

            sub.add_argument(name_or_flags, default=default, required=required, type=type, help=help)
