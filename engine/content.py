import yaml
import pafy
import vlc
from dataclasses import dataclass
import os

PATH = "temp"


@dataclass
class Song:
    file: str
    title: str
    start: int

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

            songs.append(Song(file=path, title=title, start=start))

        return songs
