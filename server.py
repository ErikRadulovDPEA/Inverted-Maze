import enum
from dpea_p2p.server import Server

class PacketType(enum.Enum):
    NULL = 0
    COMMAND0 = 0
    COMMAND1 = 1
    COMMAND2 = 2
    COMMAND3 = 3
    COMMAND4 = 4
    COMMAND5 = 5
    COMMAND6 = 6
    COMMAND7 = 7


class Maze_Server:
    def __init__(self, *args, **kwargs):
        print("starting server")
        try:
            self.server = Server("172.17.21.1", 5001, PacketType)
            self.server.open_server()
            print('server initialized')
        except Exception as err:
            print("Server failed to initialize")
            raise err
        self.wait_until_server_starts()
        print('waited for connection')
        self.but1_state = False
        self.but2_state = False
        self.but3_state = False
        self.but1_presses = False
        self.but2_presses = False
        self.but3_presses = False
        self.maze_time = 0
        self.maze_end_flag = False
        self.ball_insert = False
        self.level = 1
        self.abc = 0

    def __del__(self):
        if self.server.connection:
            self.server.close_connection()
        self.server.close_server()

    def wait_until_server_starts(self):
        self.server.wait_for_connection()

    def send_packet(self, num):
        if self.server is None:
            raise Exception("In Server.send_packet(): Server object does not exist")
        if num == 1:
            self.server.send_packet(PacketType.COMMAND1, b"cleanup")
            print("sent packet to client")

    def switch(self):
        try:
            packet = self.server.recv_packet()
            packet_type = str(packet[0])
            if packet_type == "PacketType.COMMAND1":
                if self.but1_state:
                    print("button1 turned off")
                else:
                    print("button1 turned on")
                self.but1_state = not self.but1_state
                self.but1_presses = True
                self.level -= 1
            elif packet_type == "PacketType.COMMAND2":
                if self.but2_state:
                    print("button2 turned off")
                else:
                    print("button2 turned on")
                self.but2_state = not self.but2_state
                self.but2_presses = True
                self.level += 1
            elif packet_type == "PacketType.COMMAND3":
                if self.but3_state:
                    print("button3 turned off")
                else:
                    print("button3 turned on")
                self.but3_state = not self.but3_state
                self.but3_presses = True
            elif packet_type == "PacketType.COMMAND4":
                self.maze_time = round(float(packet[1].decode('utf-8')), 2)
                self.maze_end_flag = True
                print("maze ended")
            elif packet_type == "PacketType.COMMAND5":
                self.ball_insert = True
            elif packet_type == "PacketType.COMMAND6":
                print(packet[1].decode('utf-8'))
            elif packet_type == "PacketType.COMMAND7":
                self.maze_time = round(float(packet[1].decode('utf-8')), 2)

        except Exception as err:
            raise err

    def check_button_state(self, but_num):
        if but_num == 1:
            return self.but1_state
        elif but_num == 2:
            return self.but2_state
        elif but_num == 3:
            return self.but3_state
        else:
            return 0

    def check_button_presses(self, but_num):
        if but_num == 1:
            if self.but1_presses:
                self.but1_presses = False
                return True
        elif but_num == 2:
            if self.but2_presses:
                self.but2_presses = False
                return True
        elif but_num == 3:
            if self.but3_presses:
                self.but3_presses = False
                return True
        else:
            return 0




if __name__ == "__main__":
    pass