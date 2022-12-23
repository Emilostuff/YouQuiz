import yaml
import pafy
import vlc
from dataclasses import dataclass
import os
from enum import Enum
from threading import Thread


PATH = "temp"
STD_BUZZ = {"url": "https://www.youtube.com/watch?v=f1kA5ozNbzg&ab_channel=Memefinity"}


class QuizConfig:
    def __init__(self, path):
        # make downloads folder if it does not exist
        if not os.path.exists(PATH):
            os.makedirs(PATH)

        # parse YAML
        with open(path, "r") as f:
            data = yaml.load(f, Loader=yaml.Loader)

        # parse settings (or set to default)
        settings = data.get("settings", dict())
        self.title: str = settings.get("title", "A Music Quiz")
        self.number_of_teams: int = settings.get("teams", 2)
        if self.number_of_teams < 2 or self.number_of_teams > 4:
            raise ValueError("Invalid number of teams")
        self.penalty_time: float = settings.get("penalty_time", 5)
        if self.penalty_time < 1:
            raise ValueError("Penalty time should be at least 1 second")

        # construct teams
        buzzers = data.get("buzzers", dict())
        red = Team("RED", 0, Audio(buzzers.get("red", STD_BUZZ)).get_player())
        blue = Team("BLUE", 1, Audio(buzzers.get("blue", STD_BUZZ)).get_player())
        green = Team("GREEN", 0, Audio(buzzers.get("green", STD_BUZZ)).get_player())
        yellow = Team("YELLOW", 0, Audio(buzzers.get("yellow", STD_BUZZ)).get_player())
        self.teams = TeamList(
            red,
            blue,
            green if self.number_of_teams > 2 else None,
            yellow if self.number_of_teams == 4 else None,
        )

        # get songs
        entries = data["songs"]
        self.songs = [None] * len(entries)
        handles = []

        for (i, info) in enumerate(entries):

            thread = Thread(target=lambda (i, info): self.songs[i] = Audio(info), args=(i, info))
            thread.start()
            handles.append(thread)

        for thread in handles:
            thread.join()


@dataclass
class Team:
    name: str
    ID: int
    buzzer: vlc.MediaPlayer


@dataclass
class TeamList:
    red: Team
    blue: Team
    green: Team | None
    yellow: Team | None

    def __iter__(self):
        yield self.red
        yield self.blue
        if self.green is not None:
            yield self.green
        if self.yellow is not None:
            yield self.yellow

    def __len__(self):
        pass


class Audio:
    def __init__(self, info):
        video = pafy.new(info["url"])
        best = video.getbestaudio()

        self.file = best.download(filepath=PATH)
        self.title = info.get("title", video.title)
        self.start = info.get("start", 0)
        self.stop = info.get("stop", None)
        self.note = info.get("note", "")

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
