from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.animation import Animation
from time import time
from threading import Thread
from server import Maze_Server
import subprocess
from high_scores import HighScore
import cv2
import atexit
from profanity_check import predict
from kivy.core.audio import SoundLoader

Window.fullscreen = 'auto'
Window.show_cursor = False


def cleanup():
    s.send_packet(1)


atexit.register(cleanup)  # sends a packet that tells the client to turn off when the server program stops

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
RIGHT_SCREEN_NAME = 'right'
LEFT_SCREEN_NAME = 'left'
PLACEMENT_SCREEN_NAME = 'placement'


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
alphabet_list = "ABCDEFGHIJKLMNOPQRSTUVWXYZ  "
abc = 0
letter = 0
name_letters = ""
high_score = HighScore()
last_name = ''
auto_switch_screens = None

SOUND_FILES = {
    "navigate": 'sounds/navigate_sound.wav',
    "ready": 'sounds/ready_sound.wav',
    "go": 'sounds/go_sound.wav',
    "undo": 'sounds/undo_sound.wav',
    "select": 'sounds/select_sound.wav',
    "victory": 'sounds/victory_sound.wav'
}


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


def play_sound(action):
    sound = SoundLoader.load(SOUND_FILES[action])
    sound.stop()
    sound.play()


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
        self.start_time = 0
        self.start = True
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def reset_image(self):
        _, frame = self.capture.read()
        texture = self.convert_to_texture(frame)
        self.ids.img1.texture = texture
        self.ids.img2.texture = texture

    def level_transition(self, direction):
        anim3 = Animation(size_hint=(0.115, 0.115), duration=0.05)
        if direction == "left":
            arrow = self.ids.left_arrow_symbol
            setattr(self.ids.img1, 'x', -1920)
            setattr(self.ids.img2, 'x', 0)
            anim1 = Animation(x=0, duration=.2)
            anim2 = Animation(x=1920, duration=.2)
        if direction == "right":
            arrow = self.ids.right_arrow_symbol
            setattr(self.ids.img1, 'x', 1920)
            setattr(self.ids.img2, 'x', 0)
            anim1 = Animation(x=0, duration=.2)
            anim2 = Animation(x=-1920, duration=.2)
        anim1.start(self.ids.img1)
        anim2.start(self.ids.img2)
        anim3.start(arrow)
        anim3.bind(on_complete=lambda *args: Animation(size_hint=(0.125, 0.125), duration=0.05).start(arrow))
        anim1.bind(on_complete=lambda *args: setattr(self, 'play_video', True))

    def update(self, dt):
        global level
        if self.play_video:
            if s.check_button_presses(1) and not s.ball_insert:
                s.level -= 1
                play_sound("navigate")
            if s.check_button_presses(2) and not s.ball_insert:
                s.level += 1
                play_sound("navigate")
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
                if level == 0:
                    level = 5
                if self.start:  # begin ready go
                    self.start = False
                    play_sound("ready")
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
                    Clock.schedule_once(lambda *args: play_sound("go"), 1)
                    Clock.schedule_once(lambda *args: setattr(label, 'text', ''), 2)
                    Clock.schedule_once(lambda *args: setattr(self, 'timer', True), 2)
                    Clock.schedule_once(lambda *args: setattr(self, 'start_time', time()), 2)
                if self.timer:
                    minutes, seconds = divmod(time() - self.start_time, 60)
                    if minutes != 0:
                        self.ids.time_label.text = f"{int(minutes)}:{seconds:05.2f}"
                    else:
                        self.ids.time_label.text = f"{seconds:5.2f}"
                self.ids.level_label.text = ''
                self.ids.insert_label.text = ''
                self.ids.right_arrow_symbol.color = (1, 1, 1, 0)
                self.ids.left_arrow_symbol.color = (1, 1, 1, 0)
                if s.maze_end_flag:
                    play_sound("victory")
                    self.timer = False
                    self.start = True
                    self.play_video = False
                    s.ball_insert = False
                    if high_score.in_top_ten(level, s.maze_time):
                        SCREEN_MANAGER.transition = NoTransition()
                        SCREEN_MANAGER.current = LEFT_SCREEN_NAME
                    else:
                        SCREEN_MANAGER.transition = NoTransition()
                        SCREEN_MANAGER.current = RIGHT_SCREEN_NAME

    # def red_button(self):  # temp kivy button
    #     s.but1_presses = True
    #
    def blue_button(self):  # temp kivy button
        SCREEN_MANAGER.transition = NoTransition()
        SCREEN_MANAGER.current = RIGHT_SCREEN_NAME

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
        self.ids.right_arrow_symbol.color = (1, 1, 1, 1)
        self.ids.left_arrow_symbol.color = (1, 1, 1, 1)
        s.ball_insert = False
        s.maze_end_flag = False
        self.reset_image()
        self.play_video = True


class RightScreen(Screen):
    def switch_screen(self, dt):
        global auto_switch_screens
        if s.check_button_presses(1) or s.check_button_presses(2) or s.check_button_presses(3):
            play_sound("navigate")
            self.clear_widgets()
            Clock.unschedule(auto_switch_screens)
            Clock.unschedule(self.switch_screen)
            s.reset_button_states()
            SCREEN_MANAGER.transition = NoTransition()
            SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    def start_clock(self):
        global auto_switch_screens
        s.reset_button_states()
        Clock.schedule_once(lambda *args: Clock.schedule_interval(self.switch_screen, .2), 1)
        auto_switch_screens = Clock.schedule_once(lambda *args: setattr(s, 'but1_presses', True), 30)

    def high_score_animation(self, label, delay):
        anim = Animation(x=960 - label.width / 2, duration=0.5, t='out_expo')
        Clock.schedule_once(lambda dt: anim.start(label), delay / 6)

    def update_high_scores(self):
        global level
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
            if high_score.in_top_ten(level, s.maze_time):
                font = 60
                gap = 0.075
            else:
                high_score.add_score("", s.maze_time, level)
                font = 52.5
                gap = 0.0625
            if i <= 9:
                if score['time'] == s.maze_time:  # highlights last player who played
                    self.highlight_last_player(y)
                minutes, seconds = divmod(score["time"], 60)
                if minutes != 0:
                    text = f"{i + 1}. {score['name']} {int(minutes)}:{seconds:05.2f}"
                else:
                    text = f"{i + 1}. {score['name']} {seconds:5.2f}"
                label = self.create_label(text, y, font)
                self.add_widget(label)
                self.high_score_animation(label, i)
            y -= gap
            if i == 9:
                if not high_score.in_top_ten(level, s.maze_time):
                    y += 0.02
                    dot_label = self.create_label("...", y, font)
                    self.add_widget(dot_label)
                    self.high_score_animation(dot_label, i + 1)
                    y -= 0.0625
                    self.highlight_last_player(y)
                    minutes, seconds = divmod(score["time"], 60)
                    placement = high_score.get_placement(level, s.maze_time)
                    if minutes != 0:
                        text = f"{placement}. YOU {int(minutes)}:{seconds:05.2f}"
                    else:
                        text = f"{placement}. YOU {seconds:5.2f}"
                    label = self.create_label(text, y, font)
                    self.add_widget(label)
                    self.high_score_animation(label, i + 2)
                break
        self.add_widget(Label(
            text="press any button to continue",
            pos_hint={'center_x': 0.5, 'top': 0.1},
            size_hint=(None, None),
            color=(1, 0, 0, 1),
            outline_color=(1, 1, 1, 1),
            outline_width=2,
            bold=True,
            font_size=45
        ))

    def create_label(self, text, y, font):
        return Label(
            text=text,
            pos_hint={'top': y},
            pos=(960 * 3, 0),
            size_hint=(None, None),
            color=(1, 0, 0, 1),
            outline_color=(1, 1, 1, 1),
            outline_width=3,
            bold=True,
            font_size=font
        )

    def highlight_last_player(self, y):
        img = Image(
            source='glow_circle.png',
            size_hint=(None, None),
            size=(1000, 100),
            allow_stretch=True,
            keep_ratio=False,
            color=(1, 1, 1, 0),
            pos_hint={'center_x': 0.5, 'top': y}
        )
        anim = Animation(color=(1, 1, 1, 0.4), duration=0.5)
        Clock.schedule_once(lambda dt: anim.start(img), 1.5)
        self.add_widget(img)


class LeftScreen(Screen):
    def start_clock(self):
        s.reset_button_states()
        minutes, seconds = divmod(s.maze_time, 60)
        if minutes != 0:
            self.ids.time_label.text = f"{int(minutes)}:{seconds:05.2f}"
        else:
            self.ids.time_label.text = f"{seconds:5.2f}"
        Clock.schedule_interval(self.change_letter, 1.0 / 30.0)

    def arrow_animation(self, direction):
        anim = Animation(size_hint=(0.115, 0.115), duration=0.05)
        if direction == "left":
            arrow = self.ids.left_arrow_symbol
        if direction == "right":
            arrow = self.ids.right_arrow_symbol
        anim.start(arrow)
        anim.bind(on_complete=lambda *args: Animation(size_hint=(0.125, 0.125), duration=0.05).start(arrow))

    def change_letter(self, dt):
        global alphabet_list, abc, letter, name_letters, level
        if s.check_button_presses(1):  # left button pressed
            abc = abc - 1
            play_sound("navigate")
            self.arrow_animation("left")
        if s.check_button_presses(2):  # right button pressed
            abc = abc + 1
            play_sound("navigate")
            self.arrow_animation("right")
        if s.check_button_presses(3):  # middle button pressed
            if abc % 28 != 27 and abc % 28 != 26 and letter <= 30:  # if not enter symbol selected(and letter limit)
                play_sound("select")
                name_letters += alphabet_list[abc % 28]
                self.ids.name_label.text = name_letters
                letter += 1
            if abc % 28 == 26 and letter > 0:  # if backspace selected
                play_sound("undo")
                name_letters = name_letters[:-1]
                self.ids.name_label.text = name_letters
                letter -= 1
            if abc % 28 == 27 and letter != 0:  # if enter symbol selected
                if bool(predict([name_letters])):  # profanity filter
                    play_sound("undo")
                    letter = 0
                    name_letters = ""
                    self.ids.name_label.text = ''
                else:
                    play_sound("select")
                    high_score.add_score(name_letters, s.maze_time, level)
                    letter = 0
                    abc = 0
                    name_letters = ""
                    self.ids.name_label.text = ''
                    Clock.unschedule(self.change_letter)
                    SCREEN_MANAGER.transition = NoTransition()
                    SCREEN_MANAGER.current = RIGHT_SCREEN_NAME
        enter = self.ids.img2
        backspace = self.ids.img3
        if abc % 28 == 1:  # enter symbol is far left bs is offscreen
            self.update_img_pos(enter, .3, .5, .135)
            self.update_img_pos(backspace, 0, 0, 0)
        elif abc % 28 == 0:  # enter symbol is on the mid left bs is far left
            self.update_img_pos(enter, .4, .75, .15)
            self.update_img_pos(backspace, .29, .5, .135)
        elif abc % 28 == 27:  # enter symbol is in the middle
            self.update_img_pos(enter, .5, 1, .165)
            self.update_img_pos(backspace, .39, .75, .15)
        elif abc % 28 == 26:  # enter symbol is on the mid right
            self.update_img_pos(enter, .6, .75, .15)
            self.update_img_pos(backspace, .49, 1, .165)
        elif abc % 28 == 25:  # enter symbol is on the far right
            self.update_img_pos(enter, .7, .5, .135)
            self.update_img_pos(backspace, .59, .75, .15)
        elif abc % 28 == 24:  # backspace symbol is on the far right
            self.update_img_pos(enter, 0, 0, 0)
            self.update_img_pos(backspace, .69, .5, .135)
        else:
            self.update_img_pos(enter, 0, 0, 0)
            self.update_img_pos(backspace, 0, 0, 0)
        self.ids.letter_1.text = alphabet_list[(abc - 1) % 28]
        self.ids.letter_2.text = alphabet_list[abc % 28]
        self.ids.letter_3.text = alphabet_list[(abc + 1) % 28]
        self.ids.letter_4.text = alphabet_list[(abc - 2) % 28]
        self.ids.letter_5.text = alphabet_list[(abc + 2) % 28]

    def update_img_pos(self, img, x_pos, opacity, size_hint):
        img.pos_hint = {"center_x": x_pos}
        img.color = 1, 1, 1, opacity
        img.size_hint = (size_hint, size_hint)

        # self.ids.pos_marker.text = str(abc % 28)


class PlacementScreen(Screen):
    def switch_screen(self, dt):
        global auto_switch_screens
        if s.check_button_presses(1) or s.check_button_presses(2) or s.check_button_presses(3):
            play_sound("navigate")
            Clock.unschedule(auto_switch_screens)
            Clock.unschedule(self.switch_screen)
            s.reset_button_states()
            SCREEN_MANAGER.transition = NoTransition()
            SCREEN_MANAGER.current = RIGHT_SCREEN_NAME

    def start_clock(self):
        global auto_switch_screens, level
        minutes, seconds = divmod(s.maze_time, 60)
        if minutes != 0:
            self.ids.time_label.text = f"{int(minutes)}:{seconds:05.2f}"
        else:
            self.ids.time_label.text = f"{seconds:5.2f}"
        s.reset_button_states()
        high_score.add_score("", s.maze_time, level)
        placement = high_score.get_placement(level, s.maze_time)
        if placement % 10 == 1 and placement != 11:
            self.ids.placement_label.text = f"{placement}st"
        if placement % 10 == 2 and placement != 12:
            self.ids.placement_label.text = f"{placement}nd"
        if placement % 10 == 3 and placement != 13:
            self.ids.placement_label.text = f"{placement}rd"
        else:
            self.ids.placement_label.text = f"{placement}th"
        Clock.schedule_once(lambda *args: Clock.schedule_interval(self.switch_screen, .2), 1)
        auto_switch_screens = Clock.schedule_once(lambda *args: setattr(s, 'but1_presses', True), 7.5)
        self.placement_animation()

    def placement_animation(self):
        anim1 = Animation(font_size=220, duration=0.125)
        anim2 = Animation(outline_width=4, duration=0.125)
        anim3 = Animation(font_size=200, duration=0.05)
        anim_group = anim1 & anim2 + anim3
        anim_group.start(self.ids.placement_label)


"""
Widget additions
"""

Builder.load_file('VideoApp.kv')
SCREEN_MANAGER.add_widget(MainScreen(name=MAIN_SCREEN_NAME))
SCREEN_MANAGER.add_widget(RightScreen(name=RIGHT_SCREEN_NAME))
SCREEN_MANAGER.add_widget(LeftScreen(name=LEFT_SCREEN_NAME))
SCREEN_MANAGER.add_widget(PlacementScreen(name=PLACEMENT_SCREEN_NAME))

if __name__ == "__main__":
    ProjectNameGUI().run()
