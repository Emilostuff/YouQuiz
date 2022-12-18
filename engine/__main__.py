# from player import get_player
from server import run_server
from content import Config, Song
from threading import Thread
import queue
from enum import Enum, auto
import PySimpleGUI as sg
from gui import Gui
import textwrap


class State(Enum):
    UNLOADED = auto()
    PAUSED = auto()
    PLAYING = auto()
    INTERRUPTED = auto()
    

if __name__ == "__main__":
    # load content
    cfg = Config("config.yml")
    songs = cfg.get_songs()
    if len(songs) == 0:
        raise Exception("No songs found in config file")
    
    # set up server
    q = queue.Queue()
    thread = Thread(target=run_server, args=(q,))
    thread.start()
    
    # Setup control panel
    gui = Gui(songs)

    # PROGRAM STATE VARIABLES
    state = State.UNLOADED
    loaded_song = None
    player = None

    # Run the Event Loop
    while True:
        # read event
        event, values = gui.window.read(timeout=0)
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        # read from queue
        buzz = None if q.empty() else q.get()
        if buzz is not None:
            print(f"Got: {buzz}")

        # process event
        if event == "-MARK-":
            index = gui.song_index()
            songs[index].used = not songs[index].used
            gui.reload_song_list(songs)

        # State specific behavior
        if state == State.UNLOADED or state == State.PAUSED:
            # load song
            if event == "-LOAD-":
                state = state.PAUSED
                index = gui.song_index()
                if loaded_song != songs[index]:
                    title = textwrap.shorten(songs[index].title, width=50, placeholder=' ...')
                    gui.log(f"SONG: {title}")
                loaded_song = songs[index]
                player = loaded_song.get_player()
                gui.window["-SONG_DISPLAY-"].update(loaded_song.title)
                gui.window['-SONG_INFO-'].update(loaded_song.note)
                songs[index].used = True
                gui.reload_song_list(songs)
      
        if state == State.PAUSED:
            # play
            if event == "-PLAYPAUSE-":
                state = state.PLAYING
                player.play()
                gui.window["-PLAYPAUSE-"].update("PAUSE")

        elif state == State.PLAYING:
            # pause
            if event == "-PLAYPAUSE-":
                state = state.PAUSED
                player.pause()
                gui.window["-PLAYPAUSE-"].update("PLAY")


                  
    gui.window.close()

    thread.join()
