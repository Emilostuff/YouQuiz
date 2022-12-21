import PySimpleGUI as sg
import textwrap


STEPS = 500
COL_WIDTH = 60


class Gui:
    def __init__(self, songs):
        # settings
        sg.theme("DarkPurple3")

        # define layout
        col1 = [
            [
                sg.Text("CURRENT SONG", font=("Arial", 26)),
                sg.Push(),
                sg.Button("PLAY", key="-PLAYPAUSE-", enable_events=True),
            ],
            [
                sg.ProgressBar(
                    STEPS, orientation="h", size=(COL_WIDTH, 10), key="-PROGRESS-"
                )
            ],
            [sg.StatusBar("No song loaded", size=(COL_WIDTH, 1), key="-SONG_DISPLAY-")],
            [
                sg.Multiline(
                    size=(COL_WIDTH, 5),
                    key="-SONG_INFO-",
                    disabled=True,
                    no_scrollbar=True,
                )
            ],
            [sg.Text("", font=("Arial", 26))],
            [
                sg.Text("LIBRARY", font=("Arial", 26)),
                sg.Push(),
                sg.Button(" ✓ ", key="-MARK-", enable_events=True),
                sg.Button("Load into Player", key="-LOAD-", enable_events=True),
            ],
            [
                sg.Listbox(
                    values=[song.title for song in songs],
                    enable_events=True,
                    size=(COL_WIDTH, 20),
                    key="-SONGS-",
                    no_scrollbar=True,
                )
            ],
        ]

        col2 = [
            [sg.VPush()],
            [sg.Text("LOG", font=("Arial", 26))],
            [
                sg.Multiline(
                    size=(COL_WIDTH, 10),
                    key="-LOG-",
                    disabled=True,
                    no_scrollbar=True,
                )
            ],
        ]

        layout = [
            [
                sg.Column(col1),
                sg.VSeperator(),
                sg.Column(col2, expand_y=True),
            ]
        ]

        window = sg.Window(
            "Music Quiz Control Board", layout, finalize=True, font=("Arial", 15)
        )
        self.window = window
        self.set_song_index(0)
        sg.cprint_set_output_destination(self.window, "-LOG-")

    def get_event(self):
        event, values = self.window.read(timeout=10)
        if event == sg.WIN_CLOSED:
            event = "Exit"
        return event

    def song_index(self):
        return self.window["-SONGS-"].get_indexes()[0]

    def set_song_index(self, index):
        self.window["-SONGS-"].update(set_to_index=[index])

    def reload_song_list(self, songs):
        index = self.song_index()
        names = ["   ✓   " + s.title if s.used else s.title for s in songs]
        self.window["-SONGS-"].update(
            values=names, set_to_index=index, scroll_to_index=index
        )

    def update_player_info(self, song):
        self.window["-SONG_DISPLAY-"].update(song.title)
        self.window["-SONG_INFO-"].update(song.note)

    def log(self, msg):
        sg.cprint(textwrap.shorten(msg, width=60))

    def update_progress_bar(self, position):
        self.window["-PROGRESS-"].update(round(STEPS * position))

    # popup related
    def open_popup(self, team):
        # define layout
        layout = [
            [sg.Text(f"BUZZ FROM {team.name} TEAM", font=("Arial", 26), size=(30,3)), sg.Push()],
            [
                sg.Button("Give Time Penalty", key="-PENALTY-", enable_events=True),
                sg.Push(),
                sg.Spin(values=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0], initial_value=1.0, size=(6, 2), key="-POINTS-"),
                sg.Button("Award Points", key="-GIVE-", enable_events=True),
            ],
            
        ]

        popup = sg.Window("Buzz", layout, finalize=True, font=("Arial", 15))
        self.popup = popup

    def get_popup_event(self):
        if self.popup is None:
            return None
        event, values = self.popup.read(timeout=10)
        if event == sg.WIN_CLOSED:
            event = "Exit"
        return event

    def close_popup(self):
        self.popup.close()
        self.popup = None

    
