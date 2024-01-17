import enum
from dpea_p2p import Client

class PacketType(enum.Enum):
    NULL = 0
    COMMAND1 = 1
    COMMAND2 = 2

#         |Server IP     |Port |Packet enum
c = Client("172.17.21.2", 5001, PacketType)
c.connect()

c.send_packet(PacketType.COMMAND1, b"Hello!")
assert c.recv_packet() == (PacketType.COMMAND2, b"Hello back!")

c.close_connection()