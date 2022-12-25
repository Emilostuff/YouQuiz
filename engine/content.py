import yaml
import pafy
import vlc
from dataclasses import dataclass
import os
from enum import Enum
from threading import Thread

# defaults
PATH = "temp"
STD_BUZZ = {"url": "https://www.youtube.com/watch?v=f1kA5ozNbzg&ab_channel=Memefinity"}
STD_NO_OF_TEAMS = 2
STD_PENALTY_TIME = 5


@dataclass
class Team:
    name: str
    ident: int
    buzzer: vlc.MediaPlayer

    def play_buzzer(self):
        self.buzzer.stop()
        self.buzzer.play()


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
        2 + int(self.green is not None) + int(self.yellow is not None)


class Audio:
    def __init__(self, info):
        video = pafy.new(info["url"])
        best = video.getbestaudio()

        self.file: str = best.download(filepath=PATH, quiet=True)
        self.title: str = info.get("title", video.title)
        self.start: float = info.get("start", 0.0)
        self.stop: float = info.get("stop", None)
        self.note: str = info.get("note", "")

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


@dataclass
class QuizConfig:
    title: str
    n_teams: int
    penalty_time: float
    teams: TeamList
    songs: list[Audio]


def parse(path) -> QuizConfig:
    # make downloads folder if it does not exist
    if not os.path.exists(PATH):
        os.makedirs(PATH)

    # parse YAML
    with open(path, "r") as f:
        data = yaml.load(f, Loader=yaml.Loader)

    # parse settings (or set to default) and check validity
    settings = data.get("settings", dict())
    title: str = settings.get("title", "A Music Quiz")
    n_teams: int = settings.get("teams", STD_NO_OF_TEAMS)
    if n_teams < 2 or n_teams > 4:
        raise ValueError("Invalid number of teams")
    penalty_time: float = settings.get("penalty_time", STD_PENALTY_TIME)
    if penalty_time < 1:
        raise ValueError("Penalty time should be at least 1 second")
    if len(data["songs"]) == 0:
        raise Exception("Quiz must contain at least one song")

    # collect all resources to be fetched
    requests = []
    for key in ["red", "blue", "green", "yellow"]:
        requests.append(data.get("buzzers", dict()).get(key, STD_BUZZ))
    requests.extend(data["songs"])

    # fetch in parallel
    result = [None] * len(requests)
    handles = []

    def fetch(i, info):
        audio = Audio(info)
        print(f"Fetched: {audio.title}")
        result[i] = audio

    for (i, info) in enumerate(requests):
        thread = Thread(target=fetch, args=(i, info))
        thread.start()
        handles.append(thread)

    for thread in handles:
        thread.join()

    # construct teams
    teams = TeamList(
        Team("RED", 0, result[0].get_player()),
        Team("BLUE", 1, result[1].get_player()),
        Team("GREEN", 2, result[2].get_player()) if n_teams > 2 else None,
        Team("YELLOW", 3, result[3].get_player()) if n_teams == 4 else None,
    )

    return QuizConfig(title, n_teams, penalty_time, teams, result[4:])


if __name__ == "__main__":
    cfg = parse("examples/test.yml")
    print(cfg.title)
    print(cfg.n_teams)
    print(cfg.penalty_time)
    print(cfg.songs)
    print(cfg.teams)
