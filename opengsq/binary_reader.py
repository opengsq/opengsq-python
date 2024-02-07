import struct


class BinaryReader:
    def __init__(self, data: bytes):
        self.__data = data
        self.stream_position = 0

    def remaining_bytes(self) -> int:
        return len(self.__data) - self.stream_position

    def is_end(self) -> bool:
        return self.stream_position >= len(self.__data)

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

    def read_short(self, unsigned=True) -> int:
        format = 'H' if unsigned else 'h'
        data = struct.unpack(f'<{format}', self.__data[self.stream_position:self.stream_position + 2])[0]
        self.stream_position += 2

        return data

    def read_long(self, unsigned=False) -> int:
        format = 'L' if unsigned else 'l'
        data = struct.unpack(f'<{format}', self.__data[self.stream_position:self.stream_position + 4])[0]
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

        while self.remaining_bytes() > 0:
            stream_byte = bytes([self.read_byte()])

            if stream_byte in delimiters:
                break

            bytes_string += stream_byte

        return str(bytes_string, encoding=encoding, errors=errors)

    def read_pascal_string(self, encoding='utf-8', errors='ignore'):
        length = self.read_byte()
        pascal_string = str(self.read_bytes(length - 1), encoding=encoding, errors=errors)
        return pascal_string

