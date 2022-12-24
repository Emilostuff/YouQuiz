from server import Server
from content import parse, Audio, QuizConfig
import PySimpleGUI as sg
from enum import Enum, auto
from gui import Gui
import vlc
import time
from dataclasses import dataclass


class State(Enum):
    UNLOADED = auto()
    PAUSED = auto()
    PLAYING = auto()
    BUZZED = auto()


@dataclass
class Program:
    config: QuizConfig
    gui: Gui
    server: Server
    state: State
    points: list[int]
    timers: list[float]
    last_time: float
    loaded_song: Audio = None
    buzzers_enabled: bool = True