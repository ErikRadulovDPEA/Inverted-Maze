import enum
from dpea_p2p import Server

class PacketType(enum.Enum):
    NULL = 0
    COMMAND1 = 1
    COMMAND2 = 2

#         |Bind IP       |Port |Packet enum
s = Server("172.17.21.2", 5001, PacketType)
s.open_server()
s.wait_for_connection()

assert s.recv_packet() == (PacketType.COMMAND1, b"Hello!")
s.send_packet(PacketType.COMMAND2, b"Hello back!")

s.close_connection()
s.close_server()