# OpenGSQ Python Library

[![Python Package](https://github.com/opengsq/opengsq-python/actions/workflows/python-package.yml/badge.svg)](https://github.com/opengsq/opengsq-python/actions/workflows/python-package.yml)
[![GitHub license](https://img.shields.io/github/license/opengsq/opengsq-python)](https://github.com/opengsq/opengsq-python/blob/main/LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/opengsq.svg)](https://pypi.org/project/opengsq/)
[![Python versions](https://img.shields.io/pypi/pyversions/opengsq.svg)](https://pypi.org/project/opengsq/)
[![Downloads](https://pepy.tech/badge/opengsq)](https://pepy.tech/project/opengsq)

The OpenGSQ Python library provides a convenient way to query servers
from applications written in the Python language.

## Supported Protocols

The library supports a wide range of protocols. Here are some examples:

```py
from opengsq.protocols import (
    ASE,
    Battlefield,
    Doom3,
    EOS,
    FiveM,
    GameSpy1,
    GameSpy2,
    GameSpy3,
    GameSpy4,
    Kaillera,
    KillingFloor,
    Minecraft,
    Nadeo,
    Palworld,
    Quake1,
    Quake2,
    Quake3,
    RakNet,
    Samp,
    Satisfactory,
    Scum,
    Source,
    TeamSpeak3,
    Unreal2,
    Vcmp,
    WON,
)
```

## Requirements

- Python 3.7 or higher

## Installation

The recommended installation method is using [pip](http://pip-installer.org/):

```sh
pip install --upgrade opengsq
```

## Usage

Here’s an example of how to query a server using the Source protocol:

```py
import asyncio
from opengsq.protocols import Source

async def main():
    source = Source(host='45.147.5.5', port=27015)
    info = await source.get_info()
    print(info)

asyncio.run(main())
```

You can also use the Source Remote Console:

```py
import asyncio
from opengsq.exceptions import AuthenticationException
from opengsq.rcon_protocols.source_rcon import SourceRcon

async def main():
    with SourceRcon("123.123.123.123", 27015) as source_rcon:
        try:
            await source_rcon.authenticate("serverRconPassword")
        except AuthenticationException:
            print('Failed to authenticate')

        response = await source_rcon.send_command("cvarlist")
        print(response)

asyncio.run(main())
```

### Command-line interface

This library additionally provides an `opengsq` command-line utility
which makes it easy to query game servers from your terminal. Run
`opengsq -h` for usage.

```sh
# query server using source protocol
opengsq source --host 123.123.123.123 --port 27015 --function get_info
```

## Tests and Results

You can find information about tests and results at [https://python.opengsq.com/tests/protocols](https://python.opengsq.com/tests/protocols)

## Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues.

![https://github.com/opengsq/opengsq-python/graphs/contributors](https://contrib.rocks/image?repo=opengsq/opengsq-python)

## Stargazers over time

[![Stargazers over time](https://starchart.cc/opengsq/opengsq-python.svg?variant=adaptive)](https://starchart.cc/opengsq/opengsq-python)
