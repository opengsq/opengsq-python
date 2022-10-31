import struct


class BinaryReader:
    def __init__(self, data: bytes):
        self.__data = data
        self.stream_position = 0

    def length(self) -> int:
        return len(self.__data) - self.stream_position

    def is_end(self) -> int:
        return self.stream_position >= len(self.__data) - 1

    def prepend_bytes(self, data):
        self.__data = data + self.__data

    def read(self) -> bytes:
        return self.__data[self.stream_position:]

    def read_byte(self) -> int:
        data = self.__data[self.stream_position]
        self.stream_position += 1

        return data

    def read_bytes(self, count: int) -> bytes:
        data = self.__data[self.stream_position:self.stream_position + count]
        self.stream_position += count

        return data

    def read_short(self) -> int:
        data = struct.unpack('<h', self.__data[self.stream_position:self.stream_position + 2])[0]
        self.stream_position += 2

        return data

    def read_long(self) -> int:
        data = struct.unpack('<l', self.__data[self.stream_position:self.stream_position + 4])[0]
        self.stream_position += 4

        return data

    def read_long_long(self) -> int:
        data = struct.unpack('<q', self.__data[self.stream_position:self.stream_position + 8])[0]
        self.stream_position += 8

        return data

    def read_float(self) -> float:
        data = struct.unpack('<f', self.__data[self.stream_position:self.stream_position + 4])[0]
        self.stream_position += 4

        return data

    def read_string(self, delimiters=[b'\x00'], encoding='utf-8', errors='ignore') -> str:
        bytes_string = b''

        while self.length() > 0:
            stream_byte = bytes([self.read_byte()])

            if stream_byte in delimiters:
                break

            bytes_string += stream_byte

        return str(bytes_string, encoding=encoding, errors=errors)
