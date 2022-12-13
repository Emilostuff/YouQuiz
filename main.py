# from player import get_player
from server import run_server
from threading import Thread
import queue
from enum import Enum
import PySimpleGUI as sg


class State(Enum):
    IDLE = 0
    PLAY = 1
    ANSWER = 2


if __name__ == "__main__":
    # url = "https://www.youtube.com/watch?v=9qoXa5_w3Gw"

    # player = get_player(url)

    # playing = False
    # while True:
    #     if input() == "p":
    #         if playing:
    #             player.pause()
    #         else:
    #             player.play()
    #         playing = not playing

    q = queue.Queue()

    thread = Thread(target=run_server, args=(q,))
    thread.start()

    # For now will only show the name of the file that was chosen
    image_viewer_column = [
        [sg.Text("Choose an image from list on left:")],
    ]

    # ----- Full layout -----
    file_list_column = [
        [
            sg.Listbox(
                values=["hello", "world"],
                enable_events=True,
                size=(40, 20),
                key="-FILE LIST-",
            )
        ],
    ]

    layout = [
        [
            sg.Column(file_list_column),
            sg.VSeperator(),
            sg.Column(image_viewer_column),
        ]
    ]

    window = sg.Window("Image Viewer", layout)

    # Run the Event Loop
    while True:
        # read from queue
        buzz = None if q.empty() else q.get()

        if buzz is not None:
            print(f"Got: {buzz}")

        event, values = window.read(timeout=0)
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        elif event == "-FILE LIST-":  # A file was chosen from the listbox
            print("clicked on file")

    window.close()

    thread.join()
