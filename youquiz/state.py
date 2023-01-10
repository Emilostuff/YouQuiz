from content import Audio, QuizConfig
from enum import Enum, auto
import vlc
import time


class State(Enum):
    UNLOADED = auto()
    PAUSED = auto()
    PLAYING = auto()
    BUZZED = auto()


class Context:
    def __init__(self, config: QuizConfig):
        self.state = State.UNLOADED
        self.loaded_song: Audio = None
        self.player: vlc.MediaPlayer = None
        self.used_songs = dict.fromkeys(config.songs, False)
        self.points = dict.fromkeys(config.teams.values(), 0)
        self.timers = dict.fromkeys(config.teams.values(), 0.0)
        self.buzzed = set()
        self.last_time = None
        self.buzzing_enabled = True
        self.team_in_focus = None

    def reset_timers(self):
        self.timers = dict.fromkeys(self.timers, 0.0)

    def update_timers(self):
        assert self.state == State.PLAYING
        now = time.time()
        elapsed = now - self.last_time
        self.last_time = now
        for team, remaining in self.timers.items():
            if remaining != 0.0:
                self.timers[team] = max(remaining - elapsed, 0.0)

    def __pause_player(self):
        if self.player is not None and self.player.is_playing():
            self.player.pause()

    def __start_player(self):
        if self.player is not None and not self.player.is_playing():
            self.player.play()

    def set_to_paused(self):
        self.state = State.PAUSED
        self.__pause_player()
        self.team_in_focus = None

    def set_to_playing(self):
        self.reset_buzzed()
        self.state = State.PLAYING
        self.__start_player()
        self.last_time = time.time()

    def set_to_buzzed(self):
        self.state = State.BUZZED
        self.__pause_player()

    def load_song(self, song):
        assert self.state == State.PAUSED or self.state == State.UNLOADED
        self.state = State.PAUSED
        self.loaded_song = song
        self.player = song.get_player()
        self.used_songs[song] = True
        self.buzzing_enabled = True
        self.reset_timers()

    def toggle_mark_song(self, song):
        self.used_songs[song] = not self.used_songs[song]

    def try_add_buzz(self, team):
        if (
            (self.state == State.PLAYING or self.state == State.BUZZED)
            and team not in self.buzzed
            and self.buzzing_enabled
            and self.timers[team] == 0.0
        ):
            self.buzzed.add(team)
            return True
        else:
            return False

    def reset_buzzed(self):
        self.buzzed = set()

    def kill(self):
        if self.player is not None:
            self.player.stop()
