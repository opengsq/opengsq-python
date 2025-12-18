from opengsq.protocols.directplay import DirectPlay
from opengsq.binary_reader import BinaryReader


class StrongholdCrusader(DirectPlay):
    """
    Stronghold Crusader DirectPlay Protocol

    Erweitert das DirectPlay Basis-Protokoll um spezifische
    Stronghold Crusader Implementierungsdetails.

    Wichtig: Stronghold Crusader verwendet TCP Port 2301 statt 2300!
    """

    full_name = "Stronghold Crusader DirectPlay Protocol"

    # Stronghold Crusader spezifische Konstanten und Payload
    STRONGHOLD_CRUSADER_UDP_PAYLOAD = bytes.fromhex(
        "3400b0fa020008fd000000000000000000000000706c617902000e00482f5e1dc0e8e549aed8b124da9e30590000000091000000"
    )

    # DirectPlay Payload-Struktur für Stronghold Crusader:
    # Bytes 0-27:  Gemeinsamer DirectPlay Header (identisch mit AoE1/AoE2)
    # Bytes 20-23: "play" - DirectPlay Identifikation
    # Bytes 28-43: Spiel-spezifische GUID: 482f5e1d-c0e8-e549-aed8-b124da9e3059
    # Bytes 44-47: Padding/Reserved (00 00 00 00)
    # Bytes 48-51: Version/Type ID: 91 00 00 00 (145 dezimal)
    STRONGHOLD_CRUSADER_GAME_GUID = "482f5e1d-c0e8-e549-aed8-b124da9e3059"

    # Stronghold Crusader verwendet TCP Port 2301 statt 2300
    STRONGHOLD_CRUSADER_TCP_PORT = 2301

    def __init__(
        self,
        host: str,
        port: int = DirectPlay.DIRECTPLAY_UDP_PORT,
        timeout: float = 5.0,
    ):
        super().__init__(host, port, timeout)
        # Überschreibe den TCP Listen Port für Stronghold Crusader
        self._tcp_listen_port = self.STRONGHOLD_CRUSADER_TCP_PORT

    def _build_query_packet(self) -> bytes:
        """
        Erstellt das Stronghold Crusader-spezifische UDP Query Packet.

        Verwendet den echten DirectPlay-Payload für Stronghold Crusader:
        3400b0fa020008fd000000000000000000000000706c617902000e00482f5e1dc0e8e549aed8b124da9e30590000000091000000

        Returns:
            bytes: Das Stronghold Crusader Query Packet
        """
        return self.STRONGHOLD_CRUSADER_UDP_PAYLOAD

    def _parse_response(self, buffer: bytes) -> dict:
        """
        Parsed die TCP-Antwort vom Stronghold Crusader Server.

        Erweitert die Basis-DirectPlay-Parsing um Stronghold Crusader-spezifische Logik.

        Args:
            buffer: Die rohen TCP-Antwortdaten

        Returns:
            dict: Geparste Stronghold Crusader Server-Informationen
        """
        # Nutze die Basis-DirectPlay-Parsing-Logik
        result = super()._parse_response(buffer)

        # Stronghold Crusader-spezifische Anpassungen
        result["game_type"] = "Stronghold Crusader"
        result["game_version"] = "1.41"  # Stronghold Crusader Version

        # Versuche Stronghold Crusader-spezifische Daten zu parsen
        try:
            stronghold_data = self._parse_stronghold_crusader_specific_data(buffer)
            result.update(stronghold_data)
        except Exception as e:
            result["raw"]["stronghold_crusader_parse_error"] = str(e)

        # Debug-Informationen hinzufügen
        result["raw"]["game_guid"] = self.STRONGHOLD_CRUSADER_GAME_GUID
        result["raw"]["tcp_port"] = self.STRONGHOLD_CRUSADER_TCP_PORT
        result["raw"]["buffer_size"] = len(buffer)
        result["raw"]["buffer_preview"] = (
            buffer[:50].hex() if len(buffer) > 50 else buffer.hex()
        )

        return result

    def _parse_stronghold_crusader_specific_data(self, buffer: bytes) -> dict:
        """
        Parsed Stronghold Crusader-spezifische Daten aus der DirectPlay-Antwort.

        Args:
            buffer: Die rohen Antwortdaten

        Returns:
            dict: Stronghold Crusader-spezifische Daten
        """
        result = {}

        if len(buffer) < 10:
            return result

        br = BinaryReader(buffer)

        try:
            # Skip DirectPlay Header (4 bytes)
            br.read_bytes(4)

            # Versuche, Stronghold Crusader-spezifische Strukturen zu erkennen
            remaining_data = br.read_bytes(br.remaining_bytes())

            # Suche nach Spielnamen (Stronghold Crusader verwendet UTF-16LE Strings)
            game_name = self._extract_stronghold_crusader_game_name(remaining_data)
            if game_name:
                result["name"] = game_name

            # Versuche Spieleranzahl zu ermitteln
            player_count = self._extract_stronghold_crusader_player_count(
                remaining_data
            )
            if player_count >= 0:
                result["num_players"] = player_count

            # Versuche Max Players zu ermitteln
            max_players = self._extract_stronghold_crusader_max_players(remaining_data)
            if max_players > 0:
                result["max_players"] = max_players

        except Exception as e:
            result["stronghold_crusader_specific_error"] = str(e)

        return result

    def _extract_stronghold_crusader_game_name(self, data: bytes) -> str:
        """
        Versucht, den Spielnamen aus den Stronghold Crusader-Daten zu extrahieren.

        Stronghold Crusader verwendet UTF-16LE Strings mit 32-bit Length-Prefix,
        ähnlich wie Age of Empires und Stronghold CE.

        Args:
            data: Die Daten nach dem DirectPlay-Header

        Returns:
            str: Der Spielname oder leer
        """
        try:
            # Suche nach dem UTF-16LE String-Pattern
            # Der Spielname ist typischerweise am Ende des DirectPlay-Pakets

            # Suche nach 32-bit Length-Prefix für UTF-16LE String
            search_start = max(0, len(data) - 200)  # Starte weiter hinten

            for i in range(search_start, len(data) - 8, 4):
                if i + 4 < len(data):
                    # Lese 32-bit Längenwert (little-endian)
                    potential_length = int.from_bytes(data[i : i + 4], "little")

                    # Plausible Länge für einen Spielnamen (12-400 bytes für UTF-16LE)
                    if 12 <= potential_length <= 400:
                        name_start = i + 4

                        # Begrenze auf verfügbare Daten
                        available_length = len(data) - name_start
                        effective_length = min(potential_length, available_length)

                        if effective_length > 0:
                            name_bytes = data[
                                name_start : name_start + effective_length
                            ]

                            try:
                                # Stronghold Crusader verwendet UTF-16LE encoding
                                decoded = name_bytes.decode("utf-16le", errors="strict")

                                # Finde den ersten null-terminierten String
                                null_pos = decoded.find("\x00")
                                if null_pos >= 0:
                                    clean_name = decoded[:null_pos].strip()
                                else:
                                    clean_name = decoded.strip()

                                # Validierung: Name sollte druckbare Zeichen enthalten
                                if (
                                    len(clean_name) >= 3
                                    and all(
                                        ord(c) >= 32 or c.isspace() for c in clean_name
                                    )
                                    and any(c.isalnum() for c in clean_name)
                                ):
                                    return clean_name
                            except UnicodeDecodeError:
                                continue

        except Exception:
            pass

        return ""

    def _extract_stronghold_crusader_player_count(self, data: bytes) -> int:
        """
        Versucht, die Spieleranzahl aus den Stronghold Crusader-Daten zu extrahieren.

        Args:
            data: Die Daten nach dem DirectPlay-Header

        Returns:
            int: Die Spieleranzahl oder 0
        """
        try:
            # DirectPlay Session Data beginnt nach dem GUID
            # Die Spielerzahl steht typischerweise bei festen Offsets

            # Bei Stronghold Crusader sind die Session-Daten strukturiert:
            # Ähnlich wie bei AoE, aber mit möglicherweise anderen Offsets

            if len(data) >= 48:
                session_start = 40

                if len(data) >= session_start + 28:
                    max_players_offset = session_start + 24
                    current_players_offset = session_start + 28

                    max_players = int.from_bytes(
                        data[max_players_offset : max_players_offset + 4], "little"
                    )
                    current_players = int.from_bytes(
                        data[current_players_offset : current_players_offset + 4],
                        "little",
                    )

                    # Validierung der Werte (Stronghold Crusader unterstützt bis zu 8 Spieler)
                    if 1 <= max_players <= 8 and 0 <= current_players <= max_players:
                        return current_players

            # Fallback: Suche nach plausiblen Werten
            for i in range(len(data) - 8):
                value = int.from_bytes(data[i : i + 4], "little")
                next_value = int.from_bytes(data[i + 4 : i + 8], "little")

                # Suche nach dem Muster: current_players, max_players
                if 0 <= value <= 8 and 1 <= next_value <= 8 and value <= next_value:
                    return value

        except Exception:
            pass

        return 0

    def _extract_stronghold_crusader_max_players(self, data: bytes) -> int:
        """
        Versucht, die maximale Spieleranzahl aus den Stronghold Crusader-Daten zu extrahieren.

        Args:
            data: Die Daten nach dem DirectPlay-Header

        Returns:
            int: Die maximale Spieleranzahl oder 0
        """
        try:
            # Verwende dieselbe Logik wie bei player_count, aber für max_players
            if len(data) >= 48:
                session_start = 40

                if len(data) >= session_start + 28:
                    max_players_offset = session_start + 24
                    current_players_offset = session_start + 28

                    max_players = int.from_bytes(
                        data[max_players_offset : max_players_offset + 4], "little"
                    )
                    current_players = int.from_bytes(
                        data[current_players_offset : current_players_offset + 4],
                        "little",
                    )

                    if 1 <= max_players <= 8 and 0 <= current_players <= max_players:
                        return max_players

            # Fallback: Suche nach dem zweiten Wert im Spieler-Paar
            for i in range(len(data) - 8):
                value = int.from_bytes(data[i : i + 4], "little")
                next_value = int.from_bytes(data[i + 4 : i + 8], "little")

                if 0 <= value <= 8 and 1 <= next_value <= 8 and value <= next_value:
                    return next_value

        except Exception:
            pass

        return 8  # Standard für Stronghold Crusader
