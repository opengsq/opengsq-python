"""
This module provides interfaces to various game server query protocols.

The following protocols are supported:
- ASE (All-Seeing Eye)
- Battlefield
- Doom3
- EOS (Epic Online Services)
- FiveM
- GameSpy1
- GameSpy2
- GameSpy3
- GameSpy4
- KillingFloor
- Minecraft
- Quake1
- Quake2
- Quake3
- RakNet
- Samp (San Andreas Multiplayer)
- Satisfactory
- Scum
- Source (Source Engine)
- TeamSpeak3
- Unreal2
- Vcmp (Vice City Multiplayer)
- WON (World Opponent Network)

Each protocol is implemented as a separate module and can be imported individually.
"""

from opengsq.protocols.ase import ASE
from opengsq.protocols.battlefield import Battlefield
from opengsq.protocols.doom3 import Doom3
from opengsq.protocols.eos import EOS
from opengsq.protocols.fivem import FiveM
from opengsq.protocols.gamespy1 import GameSpy1
from opengsq.protocols.gamespy2 import GameSpy2
from opengsq.protocols.gamespy3 import GameSpy3
from opengsq.protocols.gamespy4 import GameSpy4
from opengsq.protocols.killingfloor import KillingFloor
from opengsq.protocols.minecraft import Minecraft
from opengsq.protocols.quake1 import Quake1
from opengsq.protocols.quake2 import Quake2
from opengsq.protocols.quake3 import Quake3
from opengsq.protocols.raknet import RakNet
from opengsq.protocols.samp import Samp
from opengsq.protocols.satisfactory import Satisfactory
from opengsq.protocols.scum import Scum
from opengsq.protocols.source import Source
from opengsq.protocols.teamspeak3 import TeamSpeak3
from opengsq.protocols.unreal2 import Unreal2
from opengsq.protocols.vcmp import Vcmp
from opengsq.protocols.won import WON
