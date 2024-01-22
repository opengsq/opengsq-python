from __future__ import annotations

from dataclasses import asdict, dataclass, field

from opengsq.responses.ase.player import Player


@dataclass
class Status:
    """
    Represents the status of a game server.

    Attributes:
        gamename (str): The name of the game.
        gameport (int): The port number of the game server.
        hostname (str): The hostname of the game server.
        gametype (str): The type of the game.
        map (str): The current map of the game.
        version (str): The version of the game.
        password (bool): Whether a password is required to join the game.
        numplayers (int): The number of players currently in the game.
        maxplayers (int): The maximum number of players allowed in the game.
        rules (dict[str, str]): The rules of the game. Defaults to an empty dictionary.
        players (list[Player]): The players currently in the game. Defaults to an empty list.
    """

    gamename: str
    gameport: int
    hostname: str
    gametype: str
    map: str
    version: str
    password: bool
    numplayers: int
    maxplayers: int
    rules: dict[str, str] = field(default_factory=dict)
    players: list[Player] = field(default_factory=list)

    @property
    def __dict__(self):
        return asdict(self)
