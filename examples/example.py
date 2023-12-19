import socket

from src.f1_ps_telemetry.unpack_udp import UDPUnpacker

udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp_socket.bind(("", 20777))

unpacker = UDPUnpacker()

while True:
    udp_packet = udp_socket.recv(2048)
    packet = unpacker.unpack_udp_packet(udp_packet)
    print("Received:", packet)
    print(type(packet))
    print()
