import pafy
import vlc


def get_player(url):
    # fetch stream url
    video = pafy.new(url)
    best = video.getbest()
    playurl = best.url

    # create player
    Instance = vlc.Instance()
    player = Instance.media_player_new()
    Media = Instance.media_new(playurl, ":no-video")
    Media.get_mrl()
    player.set_media(Media)
    return player
