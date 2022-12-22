import yaml
import pafy
import vlc
from dataclasses import dataclass
import os
from enum import Enum
from threading import Thread

PATH = "temp"


class Team(Enum):
    RED = 0
    BLUE = 1


@dataclass
class Audio:
    file: str
    title: str
    note: str
    start: int
    stop: int = None
    used: bool = False

    def get_player(self):
        # load VLC instance and media
        instance = vlc.Instance()
        media = instance.media_new(self.file, ":no-video")
        media.get_mrl()

        # add custom start time
        if self.start != 0:
            media.add_option(f"start-time={self.start}")
        if self.stop is not None:
            media.add_option(f"stop-time={self.stop}")

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

    def get_songs(self, ):
        entries = self.data["songs"]
        songs = [None] * len(entries)
        handles = []
        
        for (i, song_info) in enumerate(entries):
            def fetch(i, song_info):
                # get audio stream url
                video = pafy.new(song_info["url"])
                best = video.getbestaudio()
                path = best.download(filepath=PATH)

                # parse info
                title = song_info["title"] if "title" in song_info else video.title
                start = song_info["start"] if "start" in song_info else 0
                stop = song_info["stop"] if "stop" in song_info else None
                note = song_info["note"] if "note" in song_info else ""

                songs[i] = Audio(path, title, note, start, stop)

            thread = Thread(target=fetch, args=(i, song_info))
            thread.start()
            handles.append(thread)

        for thread in handles:
            thread.join()

        return songs

    def get_buzzers(self):
        buzzers = []
        
        for (i, team_info) in enumerate(self.data["buzzers"]):
            # get audio stream url
            video = pafy.new(team_info["url"])
            best = video.getbestaudio()
            path = best.download(filepath=PATH)

            # parse info
            start = team_info["start"] if "start" in team_info else 0
            stop = team_info["stop"] if "stop" in team_info else None

            if stop - start > 5.0:
                raise Exception("Buzzer audio must not last more than 5 seconds")
                
            buzzers.append(Audio(path, f"{Team(i).name} Buzzer", "", start, stop))

        return buzzers
