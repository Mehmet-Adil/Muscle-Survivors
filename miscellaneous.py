import time
from os.path import join as path_join
from math import floor
import pygame.mixer


class Timer:
    def __init__(self, duration=None, has_sound=True):
        self.start_time = None
        self.curr_time = None
        self.duration = duration

        self.has_started = False
        self.has_ended = False

        self.has_sound = has_sound

        self.last_count = None
        self.counter_sfx = pygame.mixer.Sound(path_join("Music", "Counter SFX.wav"))
        self.counter_sfx.set_volume(0.7)

    def start(self):
        if self.has_started:
            return

        self.start_time = time.time()
        self.curr_time = None
        self.has_started = True

    def reset(self):
        self.start_time = None
        self.curr_time = None
        self.has_started = False
        self.has_ended = False
        self.last_count = None

    def is_over(self) -> bool:
        """
        This method is only used when the duration is set to a number.
        """

        if not self.has_started or not self.duration or self.has_ended:
            return False

        self.has_ended = time.time() - self.start_time >= self.duration

        return self.has_ended

    def get_time(self, reverse=False):
        if not self.has_started:
            return

        if reverse:
            self.curr_time = self.duration - floor(time.time() - self.start_time)
        else:
            self.curr_time = floor(time.time() - self.start_time)

        if self.has_sound and self.last_count != self.curr_time and not time.time() - self.start_time >= self.duration:
            self.counter_sfx.play()
            self.last_count = self.curr_time

        return self.curr_time
