from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy import *
from pidev.kivy import DPEAButton
from time import sleep
from dpea_p2p import server
from threading import Thread
from server import Maze_Server
import subprocess
import string
from high_scores import HighScore

import cv2

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
RIGHT_SCREEN_NAME = 'right'
LEFT_SCREEN_NAME = 'left'

VIDEO_PATH = '/home/softdev/Downloads/ball_bounce_across_stage.mp4'


def run_switch():
    while True:
        s.switch()


# Runs a shell script on the RPi to copy over and run client file
client_thread = Thread(target=lambda: subprocess.run('./upload.sh'), daemon=True, name='Client Thread').start()
# Initializes server object which begins connection to client
s = Maze_Server()
# Allows the server to continuously receive packages from the client while still having access to Maze_Server functions
server_thread = Thread(target=run_switch, daemon=True, name='Server Thread').start()

"""variables and class declarations"""
level = 1
alphabet_list = list(string.ascii_uppercase)
abc = 0
letter = 1
name_letters = ""
high_score = HighScore()


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


# def convert_to_texture(frame):
#     global level
#     if s.check_button_presses(1):
#         level += 1
#     if s.check_button_presses(2):
#         level -= 1
#     byte_buf = frame.tobytes()
#     texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
#     texture.flip_vertical()
#     if s.level % 4 == 1:
#         texture.flip_horizontal()
#         # self.ids.level_label.text
#     if s.level % 4 == 2:
#         texture.flip_vertical()
#     if s.level % 4 == 3:
#         texture.flip_horizontal()
#         texture.flip_vertical()
#     texture.blit_buffer(byte_buf, colorfmt='bgr', bufferfmt='ubyte')
#     return texture


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
        texture = self.convert_to_texture(frame)
        self.ids.img1.texture = texture

    def update(self, dt):
        if self.play_video:
            _, frame = self.capture.read()
            if frame is None:
                self.capture = load_video_from_start()
                self.reset_image()
                return
            texture = self.convert_to_texture(frame)
            self.ids.img1.texture = texture
            if s.maze_end_flag:
                self.play_video = False
                s.maze_end_flag = False
                self.switch_to_left()

    def convert_to_texture(self, frame):
        byte_buf = frame.tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.flip_vertical()
        if s.level % 4 == 0:
            self.ids.level_label.text = 'Level 1'
        if s.level % 4 == 1:
            texture.flip_horizontal()
            self.ids.level_label.text = 'Level 2'
        if s.level % 4 == 2:
            texture.flip_vertical()
            self.ids.level_label.text = 'Level 3'
        if s.level % 4 == 3:
            texture.flip_horizontal()
            texture.flip_vertical()
            self.ids.level_label.text = 'Level 4'
        texture.blit_buffer(byte_buf, colorfmt='bgr', bufferfmt='ubyte')
        return texture

    def start_video(self):
        self.play_video = True



    @staticmethod
    def switch_to_left():
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = LEFT_SCREEN_NAME

    @staticmethod
    def switch_to_right():
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = RIGHT_SCREEN_NAME


class RightScreen(Screen):
    # @staticmethod
    def switch_screen(self, dt):
        if s.check_button_presses(1):
            SCREEN_MANAGER.transition.direction = "right"
            SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    def update_high_scores(self):
        self.clear_widgets()
        self.add_widget(Label(
            text='High Scores',
            font_size='32sp',
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'top': 0.95},
            color=(0, 0, 0, 1)
        ))
        y = 0.9
        for i in range(len(high_score.scores)):
            self.add_widget(Label(
                text=f"{i + 1}. {high_score.scores[i]['name']} {high_score.scores[i]['time']}",
                pos_hint={'left': 0.3, 'top': y},
                size_hint=(None, None),
                color=(0, 0, 0, 1),
                font_size=32))
            y -= 0.05

    def start_clock(self):
        Clock.schedule_interval(self.switch_screen, 1.0 / 33.0)



class LeftScreen(Screen):
    @staticmethod
    def switch_screen():
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    def start_clock(self):
        Clock.schedule_interval(self.change_letter, 1.0 / 33.0)

    def change_letter(self, dt):
        global alphabet_list, abc, letter, name_letters
        if s.check_button_presses(1):
            abc = abc - 1
        if s.check_button_presses(2):
            abc = abc + 1
        if s.check_button_presses(3):
            name_letters += alphabet_list[abc % 26]
            letter += 1
            abc = 0
        if letter == 1:
            self.ids.letter_1.text = alphabet_list[abc % 26]
        if letter == 2:
            self.ids.letter_2.text = alphabet_list[abc % 26]
            self.ids.letter_2.color = 1, 0, 0, 1
            self.ids.letter_2.outline_color = 1, 1, 1, 1
            self.ids.letter_1.font_size = 50
            self.ids.letter_2.font_size = 60
            self.ids.pos_marker.pos_hint = {"center_x": 0.5}
        if letter == 3:
            self.ids.letter_3.text = alphabet_list[abc % 26]
            self.ids.letter_3.color = 1, 0, 0, 1
            self.ids.letter_3.outline_color = 1, 1, 1, 1
            self.ids.letter_2.font_size = 50
            self.ids.letter_3.font_size = 60
            self.ids.pos_marker.pos_hint = {"center_x": 0.6}
        if letter == 4:
            high_score.add_score(name_letters, s.maze_time)
            name_letters = ""
            self.ids.letter_3.font_size = 50
            abc = 0
            self.ids.letter_1.text = alphabet_list[abc]
            self.ids.letter_2.text = alphabet_list[abc]
            self.ids.letter_3.text = alphabet_list[abc]
            self.ids.letter_1.font_size = 60
            self.ids.letter_2.color = 1, 0, 0, 0.75
            self.ids.letter_2.outline_color = 1, 1, 1, 0.75
            self.ids.letter_3.color = 1, 0, 0, 0.75
            self.ids.letter_3.outline_color = 1, 1, 1, 0.75
            self.ids.pos_marker.pos_hint = {"center_x": 0.4}
            letter = 1
            SCREEN_MANAGER.transition = NoTransition()
            SCREEN_MANAGER.current = RIGHT_SCREEN_NAME

    def letter_button(self):  # temp kivy button because I dont have 3rd button
        s.but3_presses = True


"""
Widget additions
"""

Builder.load_file('VideoApp.kv')
SCREEN_MANAGER.add_widget(MainScreen(name=MAIN_SCREEN_NAME))
SCREEN_MANAGER.add_widget(RightScreen(name=RIGHT_SCREEN_NAME))
SCREEN_MANAGER.add_widget(LeftScreen(name=LEFT_SCREEN_NAME))

if __name__ == "__main__":
    ProjectNameGUI().run()
