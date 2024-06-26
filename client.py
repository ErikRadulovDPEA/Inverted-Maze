import enum
from dpea_p2p import Client
from dpeaDPi.DPiComputer import DPiComputer
from dpeaDPi.DPiPowerDrive import DPiPowerDrive
from dpeaDPi.DPiDigitalIn import DPiDigitalIn
from time import sleep, time
from threading import Thread
import board
import busio
import adafruit_max9744
i2c = busio.I2C(board.SCL, board.SDA)
amp = adafruit_max9744.MAX9744(i2c)
amp.volume = 31  # set amp volume

dpiComputer = DPiComputer()
dpiPowerDrive = DPiPowerDrive()
dpiDigitalIn = DPiDigitalIn()



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
    RESPONSE_ERROR = 8



class Maze_Client:
    def __init__(self):
        try:
            self.client = Client("172.17.21.1", 5001, PacketType)
            self.client.connect()
            dpiComputer.initialize()
            dpiPowerDrive.setBoardNumber(0)
            dpiPowerDrive.initialize()
            dpiDigitalIn.setBoardNumber(0)
            dpiDigitalIn.initialize()
            for i in range(16):
                dpiDigitalIn.setLatchActiveHigh(i)
            dpiDigitalIn.clearAllLatches()
            print("Client initialized")
            self.button1_pressed = False
            self.button2_pressed = False
            self.button3_pressed = False
        except Exception as err:
            print("Client failed to initialize")
            raise err

    def switch(self):
        while True:
            try:
                packet = self.client.recv_packet()
                packet_type = str(packet[0])
                if packet_type == "PacketType.COMMAND1":
                    dpiPowerDrive.switchDriverOnOrOff(0, False)
                elif packet_type == "PacketType.COMMAND2":
                    vol = int(packet[1].decode('utf-8'))
                    amp.volume = vol
                elif packet_type == "PacketType.COMMAND3":
                    brightness = int(packet[1].decode('utf-8'))
                    dpiPowerDrive.setDriverPWM(0, brightness)

            except Exception as e:
                self.client.send_packet(PacketType.RESPONSE_ERROR, bytearray(str(e), 'utf-8'))

    def button1(self):
        if not dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0) and not self.button1_pressed:
            self.client.send_packet(PacketType.COMMAND1, b"but1")
            self.button1_pressed = True
            sleep(0.05)
        elif dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0) and self.button1_pressed:
            self.button1_pressed = False

    def button2(self):
        if not dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_1) and not self.button2_pressed:
            self.client.send_packet(PacketType.COMMAND2, b"but2")
            self.button2_pressed = True
            sleep(0.05)
        elif dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_1) and self.button2_pressed:
            self.button2_pressed = False

    def button3(self):
        if not dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_3) and not self.button3_pressed:
            self.client.send_packet(PacketType.COMMAND3, b"but3")
            self.button3_pressed = True
            sleep(0.05)
        elif dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_3) and self.button3_pressed:
            self.button3_pressed = False

    def return_ending_time(self, time_dif):
        payload = str(time_dif).encode('utf-8')
        self.client.send_packet(PacketType.COMMAND4, payload)

    def ball_insert(self):
        self.client.send_packet(PacketType.COMMAND5, b'ball_insert')

    def ping_test(self):
        if not dpiDigitalIn.ping():
            DDI = "Communication with the DPiDigitalIn board failed."
        else:
            DDI = "Communication with the DPiDigitalIn board succeeded."
        if not dpiPowerDrive.ping():
            DPD = "Communication with the DPiPowerDrive board failed."
        else:
            DPD = "Communication with the DPiPowerDrive board succeeded."
        payload = (DDI + "\n" + DPD).encode('utf-8')
        self.client.send_packet(PacketType.COMMAND6, payload)

    def return_starting_time(self, time):
        payload = str(time).encode('utf-8')
        self.client.send_packet(PacketType.COMMAND7, payload)


if __name__ == "__main__":
    c = Maze_Client()
    c.ping_test()
    dpiPowerDrive.switchDriverOnOrOff(0, True)  # turn on leds
    dpiPowerDrive.setDriverPWM(0, 16)  # set the brightness to 16
    Thread(target=c.switch, daemon=True).start()
    while True:
        c.button1()
        c.button2()
        c.button3()
        _, latch_value_0 = dpiDigitalIn.readLatch(0)
        _, latch_value_1 = dpiDigitalIn.readLatch(1)
        if latch_value_0:
            start_time = time() + 2
            c.ball_insert()
            c.return_starting_time(start_time)
        if latch_value_1:
            end_time = time()
            c.return_ending_time(end_time - start_time)
        sleep(0.01)  # small delay to prevent high cpu usage
