import PySimpleGUI as sg


class Gui:
    def __init__(self, songs):
        # set color theme
        sg.theme("DarkPurple3")

        # define layout
        col1 = [
            [
                sg.Text("CURRENT SONG", font=("Arial", 26)),
                sg.Push(),
                sg.Button("PLAY", key="-PLAYPAUSE-", enable_events=True),
            ],
            [sg.StatusBar("No song loaded", size=(60, 1), key="-SONG_DISPLAY-")],
            [
                sg.Multiline(
                    size=(60, 5),
                    key="-SONG_INFO-",
                    disabled=True,
                    no_scrollbar=True,
                )
            ],
            [sg.Text("", font=("Arial", 26))],
            [
                sg.Text("LIBRARY", font=("Arial", 26)),
                sg.Push(),
                sg.Button("Mark", key="-MARK-", enable_events=True),
                sg.Button("Load into Player", key="-LOAD-", enable_events=True),
            ],
            [
                sg.Listbox(
                    values=[song.title for song in songs],
                    enable_events=True,
                    size=(60, 20),
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
                    size=(60, 10),
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

    def log(self, msg):
        sg.cprint_set_output_destination(self.window, "-LOG-")
        sg.cprint(msg)
