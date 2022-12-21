# from player import get_player
from server import Server
from content import Config, Song
import PySimpleGUI as sg
from enum import Enum, auto
from gui import Gui
from content import Team
import vlc
import time


class State(Enum):
    UNLOADED = auto()
    PAUSED = auto()
    PLAYING = auto()
    BUZZED = auto()


class Program:
    def __init__(self, gui, server, songs):
        if len(songs) == 0:
            raise Exception("Can't make program from empty song list")
        self.gui = gui

        self.songs = songs
        self.server = server

        # PROGRAM STATE VARIABLES
        self.state = State.UNLOADED
        self.loaded_song: Song = None
        self.player: vlc.MediaPlayer = None
        self.points = [0] * len(Team)
        self.timers = [0.0] * len(Team)
        self.last_time = None

    def start_player(self):
        if self.player is not None and not self.player.is_playing():
            self.player.play()
        self.gui.window["-PLAYPAUSE-"].update("PAUSE")

    def pause_player(self):
        if self.player is not None and self.player.is_playing():
            self.player.pause()
        self.gui.window["-PLAYPAUSE-"].update("PLAY")

    def change_state_to(self, state):
        if state == State.UNLOADED:
            raise Exception("Can't go back to this state")
        elif state == State.PAUSED:
            self.pause_player()
        elif state == State.PLAYING:
            self.start_player()
            self.last_time = time.time()
        elif state == State.BUZZED:
            self.pause_player()
        # update state
        self.state = state

    def load_song(self):
        index = self.gui.song_index()
        # log
        if self.loaded_song != self.songs[index]:
            self.gui.log("———————————————————————————")
            self.gui.log(f"SONG: {self.songs[index].title}")
        # update ui and state
        self.loaded_song = self.songs[index]
        self.player = self.loaded_song.get_player()
        self.songs[index].used = True
        self.gui.update_player_info(self.loaded_song)
        self.gui.reload_song_list(self.songs)
        self.gui.update_progress_bar(self.player.get_position())  # always shows 0.0

    def mark_song(self):
        index = self.gui.song_index()
        self.songs[index].used = not self.songs[index].used
        self.gui.reload_song_list(self.songs)

    def run(self):
        # Run the Event Loop
        while True:
            # read event
            event = self.gui.get_event()

            # a
            if event == "Exit":
                break

            if event == "-MARK-":
                self.mark_song()

            # buzz
            if self.server.has_next():
                #self.gui.window.hide()
                self.change_state_to(State.BUZZED)

            # State specific behavior
            if self.state == State.UNLOADED or self.state == State.PAUSED:
                if event == "-LOAD-":
                    self.load_song()
                    self.timers = [0.0] * len(Team)
                    self.change_state_to(State.PAUSED)

            if self.state == State.PAUSED:
                if event == "-PLAYPAUSE-":
                    self.change_state_to(State.PLAYING)

                    for team in Team:
                        if self.timers[team.value] == 0.0:
                            self.server.open(team)

            elif self.state == State.PLAYING:
                self.gui.update_progress_bar(self.player.get_position())

                now = time.time()
                elapsed = now - self.last_time
                self.last_time = now
                for team in Team:
                    remaining = self.timers[team.value]
                    if remaining != 0.0:
                        self.timers[team.value] = max(remaining - elapsed, 0.0)
                        if self.timers[team.value] == 0.0:
                            self.server.open(team)

                    
                # pause
                if event == "-PLAYPAUSE-":
                    self.change_state_to(State.PAUSED)
                    
                    self.server.close_all()

            elif self.state == State.BUZZED:
                # get team
                team = self.server.get()

                # open popup
                self.gui.open_popup(team)
                while True:
                    # read event
                    _ = self.gui.get_event()
                    event = self.gui.get_popup_event()
                    if event == "Exit":
                        break
                    elif event == "-PENALTY-":
                        self.timers[team.value] = 5.0
                        self.gui.log(f" · Team {team.name} gets a time penalty")
                        break
                    elif event == "-GIVE-":
                        points = self.gui.popup["-POINTS-"].get()
                        self.gui.log(f" · Team {team.name} is awarded {points} points")
                        self.points[team.value] += points
                        break

                self.gui.close_popup()
                    

                # return to pause state
                if not self.server.has_next():
                    self.server.reset_buzzers()
                    self.server.close_all()
                    self.change_state_to(State.PAUSED)
                    # self.gui.window.un_hide()

        self.pause_player()
        self.gui.window.close()


if __name__ == "__main__":
    # load content
    cfg = Config("config.yml")
    songs = cfg.get_songs()

    # set up and run server
    server = Server()

    # setup gui
    gui = Gui(songs)

    # Set up and run program
    program = Program(gui, server, songs)
    program.run()
