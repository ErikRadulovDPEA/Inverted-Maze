from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from pidev.kivy import DPEAButton
from time import sleep
from dpea_p2p import Server
from threading import Thread
import subprocess
import enum

import cv2


SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
RIGHT_SCREEN_NAME = 'right'
LEFT_SCREEN_NAME = 'left'

VIDEO_PATH = '/home/softdev/Downloads/ball_bounce_across_stage.mp4'

horizontally_flipped = False
vertically_flipped = False

class PacketType(enum.Enum):
    NULL = 0
    COMMAND1 = 1
    COMMAND2 = 2

#         |Bind IP       |Port |Packet enum
s = Server("172.17.21.2", 5001, PacketType)
s.open_server()

client = Thread(target=lambda: subprocess.run('./upload.sh'), daemon=True, name='Client Thread').start()
s.server.wait_for_connection()

s.wait_for_connection()

s.recv_packet() == (PacketType.COMMAND1, b"Hello!")
s.send_packet(PacketType.COMMAND2, b"Hello back!")

s.close_connection()
s.close_server()

def toggle_h_flip():
    global horizontally_flipped
    horizontally_flipped = not horizontally_flipped


def toggle_v_flip():
    global vertically_flipped
    vertically_flipped = not vertically_flipped


def toggle_hv_flip():
    global horizontally_flipped
    global vertically_flipped
    vertically_flipped = not vertically_flipped
    horizontally_flipped = not horizontally_flipped


class ProjectNameGUI(App):
    """
    Class to handle running the GUI Application
    """

    def build(self):
        """
        Build the application
        :return: Kivy Screen Manager instance
        """
        return SCREEN_MANAGER


Window.clearcolor = (1, 1, 1, 1)  # White


def load_video_from_start():
    return cv2.VideoCapture(VIDEO_PATH)


def convert_to_texture(frame):
    byte_buf = frame.tobytes()
    texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
    texture.flip_vertical()
    if horizontally_flipped and not vertically_flipped:
        texture.flip_horizontal()
    if vertically_flipped and not horizontally_flipped:
        texture.flip_vertical()
    if horizontally_flipped and vertically_flipped:
        texture.flip_horizontal()
        texture.flip_vertical()
    texture.blit_buffer(byte_buf, colorfmt='bgr', bufferfmt='ubyte')
    return texture


class MainScreen(Screen):
    """
    Class to handle the main screen and its associated touch events
    """

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.play_video = True
        self.capture = load_video_from_start()
        self.reset_image()  # sets image to start frame
        Clock.schedule_interval(self.update, 1.0 / 33.0)

    def reset_image(self):
        _, frame = self.capture.read()
        texture = convert_to_texture(frame)
        self.ids.img1.texture = texture

    def update(self, dt):
        if self.play_video:
            _, frame = self.capture.read()
            if frame is None:
                self.capture = load_video_from_start()
                self.reset_image()
                return
            texture = convert_to_texture(frame)
            self.ids.img1.texture = texture

    @staticmethod
    def switch_to_left():
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = LEFT_SCREEN_NAME

    @staticmethod
    def switch_to_right():
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = RIGHT_SCREEN_NAME


class RightScreen(Screen):
    @staticmethod
    def switch_screen():
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME


class LeftScreen(Screen):
    @staticmethod
    def switch_screen():
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME


"""
Widget additions
"""

Builder.load_file('VideoApp.kv')
SCREEN_MANAGER.add_widget(MainScreen(name=MAIN_SCREEN_NAME))
SCREEN_MANAGER.add_widget(RightScreen(name=RIGHT_SCREEN_NAME))
SCREEN_MANAGER.add_widget(LeftScreen(name=LEFT_SCREEN_NAME))

if __name__ == "__main__":
    ProjectNameGUI().run()
