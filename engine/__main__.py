from server import Server
from content import parse, Audio, QuizConfig
from enum import Enum, auto
from gui import Gui
import vlc
import time


class State(Enum):
    UNLOADED = auto()
    PAUSED = auto()
    PLAYING = auto()
    BUZZED = auto()


class ProgramOld:
    def __init__(self, config: QuizConfig, gui: Gui, server: Server):
        self.config = config
        self.gui = gui
        self.server = server

        # PROGRAM STATE VARIABLES
        self.state = State.UNLOADED
        self.loaded_song: Audio = None
        self.player: vlc.MediaPlayer = None
        self.points = [0] * config.n_teams
        self.timers = [0.0] * config.n_teams
        self.last_time = None
        self.buzzers_enabled = True

    def reset_timers(self):
        self.timers = [0.0] * self.config.n_teams

    def update_timers(self):
        now = time.time()
        elapsed = now - self.last_time
        self.last_time = now
        for team in self.config.teams:
            remaining = self.timers[team.ident]
            if remaining != 0.0:
                self.timers[team.ident] = max(remaining - elapsed, 0.0)

    def update_teams(self):
        for team in self.config.teams:
            # timers
            if self.timers[team.ident] != 0.0:
                self.gui.window[f"-{team.name}_PENALTIES-"].update(
                    f"{self.timers[team.value]:.1f} s"
                )
            else:
                self.gui.window[f"-{team.name}_PENALTIES-"].update(f"-")

            # points
            self.gui.window[f"-{team.name}_POINTS-"].update(
                f"{self.points[team.value]}"
            )

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
        self.gui.log(f"{self.songs[index].title}:", new=True)

        # update ui and state
        self.loaded_song = self.songs[index]
        self.player = self.loaded_song.get_player()
        self.songs[index].used = True
        self.gui.update_player_info(self.loaded_song)
        self.gui.reload_song_list(self.songs)
        self.gui.update_progress_bar(self.player.get_position())  # always shows 0.0

        self.buzzers_enabled = True
        self.gui.window["-ENABLE-"].update(True)

    def mark_song(self):
        index = self.gui.song_index()
        self.songs[index].used = not self.songs[index].used
        self.gui.reload_song_list(self.songs)

    def open_server(self):
        if self.buzzers_enabled:
            for team in Team:
                if self.timers[team.value] == 0.0:
                    self.server.open(team)

    def check_buzz_enable(self):
        self.buzzers_enabled = self.gui.window["-ENABLE-"].get()

    def run_team_popup(self, team, msg):
        self.gui.open_popup(msg)
        while True:
            # read event
            self.gui.popup.TKroot.focus_force()
            _ = self.gui.get_event()
            event = self.gui.get_popup_event()
            if event == "Exit" or event == "-DONE-":
                break
            elif event == "-PENALTY-":
                self.timers[team.value] += 5.0
                self.gui.log(f"{team.name} got a 5 second time penalty", indent=True)
            elif event == "-CLEAR_PENALTY-" and self.timers[team.value] != 0.0:
                self.timers[team.value] = 0.0
                self.gui.log(f"{team.name}'s time penalty was cleared", indent=True)
            elif event == "-GIVE-":
                points = self.gui.popup["-POINTS-"].get()
                end = "" if points == 1 else "s"
                self.gui.log(
                    f"{team.name} was awarded {points} point" + end, indent=True
                )
                self.points[team.value] += points
            elif event == "-DEDUCT-":
                points = self.gui.popup["-POINTS-"].get()
                end = "" if points == 1 else "s"
                self.gui.log(
                    f"{team.name} was deducted {points} point" + end, indent=True
                )
                self.points[team.value] -= points

            if event is not None:
                self.update_teams()

        self.gui.close_popup()

    def run(self):
        # log server location
        self.gui.log(f"Music Quiz Server:  {self.server.get_url()}")
        self.gui.log(f"———")

        # Run the Event Loop
        while True:
            self.gui.window["-PLAYPAUSE-"].set_focus()
            # read event
            event = self.gui.get_event()

            # always handle these
            if event == "Exit":
                break
            elif event == "-MARK-":
                self.mark_song()
            elif event == "-ENABLE-":
                self.check_buzz_enable()

            # check for buzz
            if self.server.has_next():
                self.change_state_to(State.BUZZED)

            # state specific handling
            if self.state == State.UNLOADED or self.state == State.PAUSED:
                if event == "-LOAD-":
                    self.load_song()
                    self.reset_timers()
                    self.change_state_to(State.PAUSED)
                    self.update_teams()

            if self.state == State.PAUSED:
                if event == "-PLAYPAUSE-":
                    self.change_state_to(State.PLAYING)
                    self.check_buzz_enable()
                    self.open_server()

                elif event == "-EDIT_RED-":
                    self.run_team_popup(Team.RED, f"Updating Red Team")
                elif event == "-EDIT_BLUE-":
                    self.run_team_popup(Team.BLUE, f"Updating Blue Team")

            elif self.state == State.PLAYING:
                self.gui.update_progress_bar(self.player.get_position())
                self.update_timers()
                self.update_teams()

                if self.buzzers_enabled:
                    self.open_server()
                else:
                    self.server.close_all()

                if event == "-PLAYPAUSE-" or not self.player.is_playing():
                    self.change_state_to(State.PAUSED)
                    self.server.close_all()

            elif self.state == State.BUZZED:
                # get team and show popup
                team = self.server.get()
                self.gui.log(f"{team.name} buzzed in!", indent=True)
                self.run_team_popup(team, f"{team.name} Buzzed In!")

                # return to pause state
                if not self.server.has_next():
                    self.server.reset_buzzers()
                    self.server.close_all()
                    self.change_state_to(State.PAUSED)

        # shut down gracefully
        self.pause_player()
        self.gui.window.close()


if __name__ == "__main__":
    # load content
    cfg = parse("config.yml")

    # set up and run server
    server = Server(cfg)

    # setup gui
    gui = Gui(songs)

    # Set up and run program
    program = Program(gui, server, songs)
    program.run()
