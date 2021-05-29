import struct


class BinaryReader:
    def __init__(self, data: bytes):
        self.__data = data

    def read(self) -> bytes:
        return self.__data

    def read_byte(self) -> int:
        data = self.__data[0]
        self.__data = self.__data[1:]

        return data

    def read_short(self) -> int:
        data = struct.unpack('<h', self.__data[:2])[0]
        self.__data = self.__data[2:]

        return data

    def read_long(self) -> int:
        data = struct.unpack('<l', self.__data[:4])[0]
        self.__data = self.__data[4:]

        return data

    def read_long_long(self) -> int:
        data = struct.unpack('<q', self.__data[:8])[0]
        self.__data = self.__data[8:]

        return data

    def read_float(self) -> float:
        data = struct.unpack('<f', self.__data[:4])[0]
        self.__data = self.__data[4:]

        return data

    def read_string(self, encoding='utf-8', errors='ignore') -> str:
        s = self.__data.split(b'\x00')[0]
        self.__data = self.__data[len(s) + 1:]

        return str(s, encoding=encoding, errors=errors)
