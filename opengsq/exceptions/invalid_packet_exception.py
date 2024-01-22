class InvalidPacketException(Exception):
    """Represents errors that occur during application execution when a packet is invalid."""

    def __init__(self, message: str):
        """
        Initializes a new instance of the InvalidPacketException class with a specified error message.

        Args:
            message (str): The message that describes the error.
        """
        super().__init__(message)

    @staticmethod
    def throw_if_not_equal(received, expected):
        """
        Checks if the received value is equal to the expected value.

        Args:
            received: The received value.
            expected: The expected value.

        Raises:
            InvalidPacketException: Thrown when the received value does not match the expected value.
        """
        if isinstance(received, bytes) and isinstance(expected, bytes):
            if received != expected:
                raise InvalidPacketException(
                    InvalidPacketException.get_message(received, expected)
                )
        elif received != expected:
            raise InvalidPacketException(
                InvalidPacketException.get_message(received, expected)
            )

    @staticmethod
    def get_message(received, expected):
        """
        Returns a formatted error message.

        Args:
            received: The received value.
            expected: The expected value.

        Returns:
            str: The formatted error message.
        """
        if isinstance(received, bytes) and isinstance(expected, bytes):
            received_str = " ".join(format(x, "02x") for x in received)
            expected_str = " ".join(format(x, "02x") for x in expected)
        else:
            received_str = str(received)
            expected_str = str(expected)

        return f"Packet header mismatch. Received: {received_str}. Expected: {expected_str}."
