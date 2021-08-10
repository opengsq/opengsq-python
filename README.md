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

Query server using Source

```py
import asyncio
from opengsq.protocols import Source

async def main():
    source = Source(address='45.147.5.5', query_port=27015)
    info = await source.get_info()
    print(info)

asyncio.run(main())
```

```json
{
    "Protocol": 17,
    "Name": "▟█▙ ZOMBIE ESCAPE AC ▟█ Otaku.TF █▙           ▟",
    "Map": "ze_voodoo_islands_v8_2_tf2",
    "Folder": "tf",
    "Game": "▟ZOMBIE ESCAPE▙ 𒈙𒈙𒈙𒈙BASE𒈙𒈙𒈙𒈙𒈙",
    "ID": 440,
    "Players": 29,
    "MaxPlayers": 32,
    "Bots": 0,
    "ServerType": "d",
    "Environment": "l",
    "Visibility": 0,
    "VAC": 1,
    "Version": "6623512",
    "EDF": 177,
    "GamePort": 27015,
    "SteamID": 85568392923229220,
    "Keywords": "!,a FREE TAUNTS,a FREE UNUSUALS,a OTAKUGAMING.TF,a ZOMBIE ESCAPE,a ZOMBIEMOD,alltalk,escpcreaplayersape,increased_maxplayers,otak,respawnti",
    "GameID": 440
}
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
