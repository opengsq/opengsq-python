import pytest
from unittest.mock import AsyncMock, patch

from opengsq.protocols.flatout2 import Flatout2
from opengsq.exceptions import InvalidPacketException
from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

@pytest.mark.asyncio
async def test_flatout2_get_status():
    """Test successful server status query via broadcast"""
    # Example response packet based on actual server response
    response_data = bytes.fromhex(
        "5900"                  # Response header
        "9972cc8f"             # Session ID
        "00000000"             # Padding pre-identifier
        "464f3134"             # "FO14" Game Identifier
        "0000000000000000"     # Padding post-identifier
        "19437312"             # Command
        "0000"                 # Additional data
        "2e5519b4e14f814a"     # Packet end marker
        "47006f006d00620069000000"  # Server name "Gombi" in UTF-16
        "0eb518737997"         # Timestamp
        "2cc8fc0a80281000"     # Server flags
        "0000000000000000"     # Reserved bytes
        "05ccc000"             # Status flags
        "000000000810000861240400101440"  # Configuration data
    )

    print(f"\nTest packet structure:")
    print(f"Header: {response_data[:2].hex()}")
    print(f"Session ID: {response_data[2:6].hex()}")
    print(f"Game ID: {response_data[10:14]}")
    print(f"Full packet: {response_data.hex()}")

    # Mock the UdpClient.communicate method
    mock_communicate = AsyncMock(return_value=response_data)

    with patch("opengsq.protocol_socket.UdpClient.communicate", mock_communicate):
        flatout2 = Flatout2(host="255.255.255.255")
        status = await flatout2.get_status()

        # Verify the mock was called with broadcast parameters
        mock_communicate.assert_called_once()
        call_args = mock_communicate.call_args
        assert call_args is not None
        args, kwargs = call_args
        assert kwargs.get('source_port') == Flatout2.FLATOUT2_PORT

        # Verify server info
        assert "hostname" in status.info
        assert status.info["hostname"]  # Check that hostname is not empty
        assert "timestamp" in status.info
        assert "flags" in status.info
        assert "status" in status.info
        assert "config" in status.info

        # Save the result for documentation
        await handler.save_result("test_flatout2_get_status", status)


@pytest.mark.asyncio
async def test_flatout2_invalid_header():
    """Test handling of invalid packet header"""
    # Response with invalid header (0x22 instead of 0x59)
    invalid_response = bytes.fromhex(
        "2200"                  # Wrong header
        "9972cc8f"             # Session ID
        "00000000"             # Padding pre-identifier
        "464f3134"             # "FO14" Game Identifier
        "0000000000000000"     # Padding post-identifier
        "19437312"             # Command
        "0000"                 # Additional data
        "2e5519b4e14f814a"     # Packet end marker
        "47006f006d00620069000000"  # Server name "Gombi" in UTF-16
        "0eb518737997"         # Rest of the data...
        "2cc8fc0a802810000000000000000000000005ccc00000000000"
        "081000086124040010144000"
    )

    # Mock the UdpClient.communicate method
    mock_communicate = AsyncMock(return_value=invalid_response)

    with patch("opengsq.protocol_socket.UdpClient.communicate", mock_communicate):
        flatout2 = Flatout2(host="255.255.255.255")
        with pytest.raises(InvalidPacketException):
            await flatout2.get_status()


@pytest.mark.asyncio
async def test_flatout2_invalid_game_id():
    """Test handling of invalid game identifier"""
    # Response with wrong game ID (BADID instead of FO14)
    invalid_game_id = bytes.fromhex(
        "5900"                  # Response header
        "9972cc8f"             # Session ID
        "00000000"             # Padding pre-identifier
        "42414449"             # Wrong game ID "BADI"
        "0000000000000000"     # Padding post-identifier
        "19437312"             # Command
        "0000"                 # Additional data
        "2e5519b4e14f814a"     # Packet end marker
        "47006f006d00620069000000"  # Server name "Gombi" in UTF-16
        "0eb518737997"         # Rest of the data...
        "2cc8fc0a802810000000000000000000000005ccc00000000000"
        "081000086124040010144000"
    )

    # Mock the UdpClient.communicate method
    mock_communicate = AsyncMock(return_value=invalid_game_id)

    with patch("opengsq.protocol_socket.UdpClient.communicate", mock_communicate):
        flatout2 = Flatout2(host="255.255.255.255")
        with pytest.raises(InvalidPacketException):
            await flatout2.get_status()


@pytest.mark.asyncio
async def test_flatout2_wrong_port():
    """Test handling of wrong port number"""
    with pytest.raises(ValueError) as exc_info:
        Flatout2(host="255.255.255.255", port=27015)  # Wrong port
    assert str(exc_info.value) == f"Flatout 2 protocol requires port {Flatout2.FLATOUT2_PORT}"


def test_status_string_representation():
    """Test the string representation of the Status class"""
    from opengsq.responses.flatout2 import Status

    # Create a test status object
    info = {
        "hostname": "Test Server",
        "timestamp": "123456789",
        "flags": "1234",
        "status": "5678",
        "config": "abcdef"
    }

    status = Status(info=info)
    str_repr = str(status)

    # Verify the string representation
    assert "Server Information:" in str_repr
    assert "hostname:" in str_repr  # Just check that the hostname field exists 