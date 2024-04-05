from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Color, BoxShadow
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy import *
from pidev.kivy import DPEAButton
from time import time
from dpea_p2p import server
from threading import Thread
from server import Maze_Server
import subprocess
from high_scores import HighScore
import cv2
import atexit
from profanity_check import predict

Window.fullscreen = 'auto'
Window.show_cursor = False


def cleanup():
    s.send_packet(1)


atexit.register(cleanup)  # sends a packet that tells the client to turn off when the server program stops

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
RIGHT_SCREEN_NAME = 'right'
LEFT_SCREEN_NAME = 'left'




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
alphabet_list = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
abc = 0
letter = 0
name_letters = ""
high_score = HighScore()
last_name = ''
auto_switch_screens = None


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
    return cv2.VideoCapture(0)


def reset_button_states():
    s.but1_state = False
    s.but2_state = False
    s.but3_state = False
    s.but1_presses = False
    s.but2_presses = False
    s.but3_presses = False


class MainScreen(Screen):
    """
    Class to handle the main screen and its associated touch events
    """

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.play_video = True
        self.lvl_5_state = 0
        self.capture = load_video_from_start()
        self.reset_image()  # sets image to start frame
        self.timer = False
        self.start = True
        Clock.schedule_interval(self.update, 1.0 / 30.0)

    def reset_image(self):
        _, frame = self.capture.read()
        texture = self.convert_to_texture(frame)
        self.ids.img1.texture = texture
        self.ids.img2.texture = texture

    def level_transition(self, direction):
        anim3 = Animation(font_size=110, duration=0.05)
        if direction == "left":
            arrow = self.ids.left_arrow
            setattr(self.ids.img1, 'x', -1920)
            setattr(self.ids.img2, 'x', 0)
            anim1 = Animation(x=0, duration=.2)
            anim2 = Animation(x=1920, duration=.2)
        if direction == "right":
            arrow = self.ids.right_arrow
            setattr(self.ids.img1, 'x', 1920)
            setattr(self.ids.img2, 'x', 0)
            anim1 = Animation(x=0, duration=.2)
            anim2 = Animation(x=-1920, duration=.2)
        anim1.start(self.ids.img1)
        anim2.start(self.ids.img2)
        anim3.start(arrow)
        anim3.bind(on_complete=lambda *args: Animation(font_size=100, duration=0.05).start(arrow))
        anim1.bind(on_complete=lambda *args: setattr(self, 'play_video', True))

    def update(self, dt):
        global level
        if self.play_video:
            if s.check_button_presses(1) and not s.ball_insert:
                s.level -= 1
            if s.check_button_presses(2) and not s.ball_insert:
                s.level += 1
            if level > s.level and not s.ball_insert:
                self.play_video = False
                self.level_transition("left")
                self.ids.img2.texture = self.ids.img1.texture
            if level < s.level and not s.ball_insert:
                self.play_video = False
                self.level_transition("right")
                self.ids.img2.texture = self.ids.img1.texture
            level = s.level
            self.lvl_5_state += 1
            _, frame = self.capture.read()
            if frame is None:
                self.capture = load_video_from_start()
                self.reset_image()
                return
            texture = self.convert_to_texture(frame)
            self.ids.img1.texture = texture

            if s.ball_insert:
                level = s.level % 5
                if s.level == 0:
                    level = 5
                if self.start:  # begin ready go
                    self.start = False
                    label = Label(text='Ready?',
                                  font_size=125,
                                  size_hint=(None, None),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                  color=(1, 0, 0, 1),
                                  outline_color=(1, 1, 1, 1),
                                  outline_width=3,
                                  bold=True
                                  )
                    self.add_widget(label)
                    Clock.schedule_once(lambda *args: setattr(label, 'text', 'Go!'), 1)
                    Clock.schedule_once(lambda *args: setattr(label, 'text', ''), 2)
                    Clock.schedule_once(lambda *args: setattr(self, 'timer', True), 2)
                if self.timer:
                    self.ids.time_label.text = format(time() - s.maze_time, '.2f')
                self.ids.level_label.text = ''
                self.ids.insert_label.text = ''
                if s.maze_end_flag:
                    self.timer = False
                    self.start = True
                    self.play_video = False
                    s.ball_insert = False
                    SCREEN_MANAGER.transition = NoTransition()
                    SCREEN_MANAGER.current = LEFT_SCREEN_NAME

    # def red_button(self):  # temp kivy button
    #     s.but1_presses = True
    #
    # def blue_button(self):  # temp kivy button
    #     s.but2_presses = True

    def convert_to_texture(self, frame):
        global level
        byte_buf = frame.tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.flip_horizontal()
        if s.level % 5 == 1:
            if not s.ball_insert:
                self.ids.level_label.text = 'Level 1'
        if s.level % 5 == 2:
            texture.flip_horizontal()
            if not s.ball_insert:
                self.ids.level_label.text = 'Level 2'
        if s.level % 5 == 3:
            texture.flip_vertical()
            if not s.ball_insert:
                self.ids.level_label.text = 'Level 3'
        if s.level % 5 == 4:
            texture.flip_horizontal()
            texture.flip_vertical()
            if not s.ball_insert:
                self.ids.level_label.text = 'Level 4'
        if s.level % 5 == 0:
            if 0 <= self.lvl_5_state % 240 <= 59:
                pass
            if 60 <= self.lvl_5_state % 240 <= 119:
                texture.flip_horizontal()
            if 120 <= self.lvl_5_state % 240 <= 179:
                texture.flip_vertical()
            if 180 <= self.lvl_5_state % 240 <= 239:
                texture.flip_horizontal()
                texture.flip_vertical()
            if not s.ball_insert:
                self.ids.level_label.text = 'Level 5'

        texture.blit_buffer(byte_buf, colorfmt='bgr', bufferfmt='ubyte')
        return texture

    def start_video(self):
        global level
        level = 1
        s.level = 1
        self.ids.insert_label.text = 'Insert ball to start'
        self.ids.time_label.text = ''
        s.ball_insert = False
        s.maze_end_flag = False
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
    def switch_screen(self, dt):
        global auto_switch_screens
        if s.check_button_presses(1) or s.check_button_presses(2) or s.check_button_presses(3):
            Clock.unschedule(auto_switch_screens)
            Clock.unschedule(self.switch_screen)
            reset_button_states()
            SCREEN_MANAGER.transition = NoTransition()
            SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    def start_clock(self):
        global auto_switch_screens
        reset_button_states()
        Clock.schedule_interval(self.switch_screen, .2)
        auto_switch_screens = Clock.schedule_once(lambda *args: setattr(s, 'but1_presses', True), 30)

    def update_high_scores(self):
        global level
        self.clear_widgets()
        self.add_widget(Label(
            text=f'Level {level} High Scores',
            font_size=75,
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'top': 0.95},
            color=(1, 0, 0, 1),
            outline_color=(1, 1, 1, 1),
            outline_width=3,
            bold=True
        ))
        y = 0.85
        for i, score in enumerate(high_score.scores[level]):
            if i <= 9:
                if score['time'] == s.maze_time:  # highlights last player who played
                    img = Image(
                        source='glow_circle.png',
                        size_hint=(None, None),
                        size=(1000, 100),
                        allow_stretch=True,
                        keep_ratio=False,
                        color=(1, 1, 1, 0.4),
                        pos_hint={'center_x': 0.5, 'top': y}
                    )
                    self.add_widget(img)
                self.add_widget(Label(
                    text=f"{i + 1}. {score['name']} {format(score['time'], '.2f')}",  # formatted to keep trailing zero
                    pos_hint={'center_x': 0.5, 'top': y},
                    size_hint=(None, None),
                    color=(1, 0, 0, 1),
                    outline_color=(1, 1, 1, 1),
                    outline_width=3,
                    bold=True,
                    font_size=60
                ))
            y -= 0.075
            if i == 9:
                break
        self.add_widget(Label(
            text="press any button to continue",
            pos_hint={'center_x': 0.5, 'top': y},
            size_hint=(None, None),
            color=(1, 0, 0, 1),
            outline_color=(1, 1, 1, 1),
            outline_width=3,
            bold=True,
            font_size=45
        ))


class LeftScreen(Screen):
    def start_clock(self):
        reset_button_states()
        self.ids.time_label.text = format(s.maze_time, '.2f')
        Clock.schedule_interval(self.change_letter, 1.0 / 30.0)

    def change_letter(self, dt):
        global alphabet_list, abc, letter, name_letters, level
        if s.check_button_presses(1):  # left button pressed
            abc = abc - 1
        if s.check_button_presses(2):  # right button pressed
            abc = abc + 1
        if s.check_button_presses(3):  # middle button pressed
            if abc % 27 != 26:  # if not enter symbol selected
                name_letters += alphabet_list[abc % 27]
                self.ids.name_label.text = name_letters
                letter += 1
            if abc % 27 == 26 and letter != 0:  # if enter symbol selected
                if bool(predict([name_letters])) or letter >= 30:  # profanity filter and letter limit
                    letter = 0
                    abc = 0
                    name_letters = ""
                    self.ids.name_label.text = ''
                else:
                    high_score.add_score(name_letters, s.maze_time, level)
                    letter = 0
                    abc = 0
                    name_letters = ""
                    self.ids.name_label.text = ''
                    Clock.unschedule(self.change_letter)
                    SCREEN_MANAGER.transition = NoTransition()
                    SCREEN_MANAGER.current = RIGHT_SCREEN_NAME
        if abc % 27 == 26:  # enter symbol is in the middle
            self.ids.img2.pos_hint = {"center_x": 0.5}
            self.ids.img2.color = 1, 1, 1, 1
        elif abc % 27 == 0:  # enter symbol is in on the left
            self.ids.img2.pos_hint = {"center_x": 0.4}
            self.ids.img2.color = 1, 1, 1, .75
        elif abc % 27 == 25:  # enter symbol is in on the right
            self.ids.img2.pos_hint = {"center_x": 0.6}
            self.ids.img2.color = 1, 1, 1, .75
        else:
            self.ids.img2.pos_hint = {"center_x": 2}  # enter symbol is not on screen
        self.ids.letter_1.text = alphabet_list[(abc - 1) % 27]
        self.ids.letter_2.text = alphabet_list[abc % 27]
        self.ids.letter_3.text = alphabet_list[(abc + 1) % 27]


"""
Widget additions
"""

Builder.load_file('VideoApp.kv')
SCREEN_MANAGER.add_widget(MainScreen(name=MAIN_SCREEN_NAME))
SCREEN_MANAGER.add_widget(RightScreen(name=RIGHT_SCREEN_NAME))
SCREEN_MANAGER.add_widget(LeftScreen(name=LEFT_SCREEN_NAME))

if __name__ == "__main__":
    ProjectNameGUI().run()
