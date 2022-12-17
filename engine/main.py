# from player import get_player
from server import run_server
from content import Config
from threading import Thread
import queue
from enum import Enum
import PySimpleGUI as sg


class State(Enum):
    IDLE = 0
    PLAY = 1
    ANSWER = 2


if __name__ == "__main__":
    # load content
    cfg = Config("config.yml")
    songs = cfg.get_songs()
    used_songs = [False] * len(songs)

    # set up server
    q = queue.Queue()
    thread = Thread(target=run_server, args=(q,))
    thread.start()

    # Setup control panel
    sg.theme("DarkPurple3")
    image_viewer_column = [
        [sg.Text("work in progress")],
    ]
    song_column = [
        [sg.Checkbox("Song used", default=False, key="-USED-", enable_events=True)],
        [
            sg.Listbox(
                values=[song.title for song in songs],
                enable_events=True,
                size=(60, 30),
                key="-SONGS-",
                no_scrollbar=True,
            )
        ],
    ]

    layout = [
        [
            sg.Column(song_column),
            sg.VSeperator(),
            sg.Column(image_viewer_column),
        ]
    ]

    window = sg.Window(
        "Music Quiz Control Board", layout, finalize=True, font=("Arial", 15)
    )
    window["-SONGS-"].update(set_to_index=[0])

    # Run the Event Loop
    while True:
        # read from queue
        buzz = None if q.empty() else q.get()

        if buzz is not None:
            print(f"Got: {buzz}")

        event, values = window.read(timeout=0)
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        elif event == "-SONGS-":
            index = window["-SONGS-"].get_indexes()[0]
            window["-USED-"].update(used_songs[index])
            print("clicked on a song")

        elif event == "-USED-":
            index = window["-SONGS-"].get_indexes()[0]
            used_songs[index] = window["-USED-"].get()

            names = []
            for (i, song) in enumerate(songs):
                names.append("√       " + song.title if used_songs[i] else song.title)
            window["-SONGS-"].update(
                values=names, set_to_index=index, scroll_to_index=index
            )

    window.close()

    thread.join()
