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

Query Mordhau server

```py
from opengsq import Mordhau

mordhau = Mordhau(address='123.123.123.123', query_port=27015)
server = mordhau.query()

print(server.to_json())
```
  
```json
{
    "name": "Duke of York - USA - Duel/Roleplay - Rp Feitoria♛",
    "map": "RP Feitoria",
    "players": 33,
    "max_players": 55,
    "bots": 0,
    "player_list": [],
    "latency": 0.7420244216918945
}
```

Query server using `A2S`

```py
from opengsq.protocols import A2S

a2s = A2S(address='123.123.123.123', query_port=27015)
server = a2s.query()

print(server.to_json())
```

```json
{
    "name": "[HK] Doctor server | Dodgeball Practice | 歡樂躲避球",
    "map": "tfdb_spacebox_a2",
    "players": 2,
    "max_players": 14,
    "bots": 1,
    "player_list": [
        {
            "name": "[BOT] DUCK's BOT",
            "score": 5,
            "time": 58525.1640625
        },
        {
            "name": "✅BattlefieldDuck",
            "score": 0,
            "time": 253.934814453125
        }
    ],
    "latency": 0.05097603797912598
}
```

### Command-line interface

This library additionally provides an `opengsq` command-line utility
which makes it easy to query game servers from your terminal. Run
`opengsq -h` for usage.

```sh
# query server using protocol-a2s
opengsq protocol-a2s --address 123.123.123.123 --query_port 27015

# query csgo server
opengsq csgo --address 123.123.123.123 --query_port 27015
```

## Requirements

-   Python 3.6+

## Credit

This library is based from the [OpenAI Python Library](https://github.com/openai/openai-python).
