# OpenGSQ Python Library

The OpenGSQ Python library provides a convenient way to query servers
from applications written in the Python language.

## Installation

The recommended installation method is using [pip](http://pip-installer.org/):

```sh
pip install --upgrade opengsq
```

Install from source with:

```sh
python setup.py install
```

## Usage

Query server using Source, example output: [tests/results/test_source/test_get_info.json](/tests/results/test_source/test_get_info.json)
```py
import asyncio
from opengsq.protocols import Source

async def main():
    source = Source(address='45.147.5.5', query_port=27015)
    info = await source.get_info()
    print(info)

asyncio.run(main())
```

Rcon server using Source Remote Console, example output: [tests/results/test_source/test_remote_console.txt](/tests/results/test_source/test_remote_console.txt)
```py
import asyncio
from opengsq.protocols import Source

async def main():
    with Source.RemoteConsole('123.123.123.123', 27015) as rcon:
        try:
            await rcon.authenticate('serverRconPassword')
            result = await rcon.send_command('cvarlist')
            print(result)
        except:
            print('Fail to authenticate')
        
asyncio.run(main())
```

### Command-line interface

This library additionally provides an `opengsq` command-line utility
which makes it easy to query game servers from your terminal. Run
`opengsq -h` for usage.

```sh
# query server using source protocol
opengsq source --address 123.123.123.123 --query_port 27015 --function get_info
```

## Supported Protocols
```py
from opengsq.protocols.gamespy1 import GameSpy1
from opengsq.protocols.gamespy2 import GameSpy2
from opengsq.protocols.gamespy3 import GameSpy3
from opengsq.protocols.gamespy4 import GameSpy4
from opengsq.protocols.quake1 import Quake1
from opengsq.protocols.quake2 import Quake2
from opengsq.protocols.quake3 import Quake3
from opengsq.protocols.source import Source # Both Source and Goldsource supported
```
You can import all protocols using the following code.
```py
from opengsq.protocols import *
```
or
```py
import opengsq
```

## Requirements

-   Python 3.6+


See [tests/protocols](/tests/protocols) for the tests.

See [tests/results](/tests/results) for tests outputs.
