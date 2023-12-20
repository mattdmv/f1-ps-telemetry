import ctypes

from packets import PacketHeader as PacketHeader
from packets import HeaderFieldsToPacketType
from packed_little_endian import PackedLittleEndianStructure

class UnpackError(Exception):
    pass


class UDPUnpacker():
    def __init__(self):
        self._PacketHeader = PacketHeader
        self._HeaderFieldsToPacketType = HeaderFieldsToPacketType

    @property
    def udp_spec(self):
        return self._udp_spec 
    
    def unpack_udp_packet(self, packet: bytes) -> PackedLittleEndianStructure:
        """Convert raw UDP packet to an appropriately-typed telemetry packet.

        Args:
            packet: the contents of the UDP packet to be unpacked.

        Returns:
            The decoded packet structure.

        Raises:
            UnpackError if a problem is detected.
        """
        actual_packet_size = len(packet)

        header_size = ctypes.sizeof(self._PacketHeader)

        if actual_packet_size < header_size:
            raise UnpackError(
                "Bad telemetry packet: too short ({} bytes).".format(actual_packet_size)
            )

        header = self._PacketHeader.from_buffer_copy(packet)
        key = (header.packetFormat, header.packetVersion, header.packetId)

        if key not in self._HeaderFieldsToPacketType:
            raise UnpackError(
                "Bad telemetry packet: no match for key fields {!r}.".format(key)
            )

        packet_type = self._HeaderFieldsToPacketType[key]

        expected_packet_size = ctypes.sizeof(packet_type)

        if actual_packet_size != expected_packet_size:
            raise UnpackError(
                "Bad telemetry packet: bad size for {} packet; expected {} bytes but received {} bytes.".format(
                    packet_type.__name__, expected_packet_size, actual_packet_size
                )
            )

        return packet_type.from_buffer_copy(packet)
