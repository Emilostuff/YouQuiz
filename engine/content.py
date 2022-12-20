import yaml
import pafy
import vlc
from dataclasses import dataclass
import os
from enum import Enum

PATH = "temp"


class Team(Enum):
    RED = 0
    BLUE = 1


@dataclass
class Song:
    file: str
    title: str
    start: int
    note: str
    used: bool = False

    def get_player(self):
        # load VLC instance and media
        instance = vlc.Instance()
        media = instance.media_new(self.file, ":no-video")
        media.get_mrl()

        # add custom start time
        if self.start != 0:
            media.add_option(f"start-time={self.start}")

        # return player
        player = instance.media_player_new()
        player.set_media(media)
        return player


class Config:
    def __init__(self, file):
        # make downloads folder if it does not exist
        if not os.path.exists(PATH):
            os.makedirs(PATH)

        # parse YAML
        with open(file, "r") as f:
            self.data = yaml.load(f, Loader=yaml.Loader)

    def get_songs(self):
        songs = []
        for song_info in self.data["songs"]:
            # get audio stream url
            video = pafy.new(song_info["url"])
            best = video.getbestaudio()
            path = best.download(filepath=PATH)

            # parse info
            title = song_info["title"] if "title" in song_info else video.title
            start = song_info["start"] if "start" in song_info else 0
            note = song_info["note"] if "note" in song_info else ""

            songs.append(Song(path, title, start, note))

        return songs
