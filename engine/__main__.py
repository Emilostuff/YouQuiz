from server import Server
from content import parse
from gui import Gui, Popup
from state import State, ApplicationState
import sys


if __name__ == "__main__":
    # load content
    if len(sys.argv) < 2:
        print("Please provide a YML config file!")
        sys.exit()
    cfg = parse(sys.argv[1])

    # initialize things
    ctx = ApplicationState(cfg)
    server = Server(cfg)
    gui = Gui(cfg)
    popup = None

    # log server location
    gui.log(f"Music Quiz Server:  {server.get_url()}")
    gui.log(f"———")

    # Run the Event Loop
    while True:
        # update gui
        gui.refresh(cfg, ctx, popup is None)
        # read event
        event = gui.get_event()

        # always handle these
        if event == "Exit":
            break
        elif event == "-MARK-":
            ctx.toggle_mark_song(cfg.songs[gui.song_index()])
        elif event == "-ENABLE-":
            ctx.buzzers_enabled = not ctx.buzzers_enabled
        elif event == "Copy::log":
            gui.copy_selection_from_log()
        elif event == "Copy::info":
            gui.copy_selection_from_info()

        # handle popup
        if popup is not None:
            popup_event = popup.get_event()

            if popup_event == "-PENALTY-":
                ctx.timers[popup.team] += cfg.penalty_time
                gui.log(
                    f"{popup.team.name} got a {cfg.penalty_time} second time penalty",
                    indent=True,
                )
            elif popup_event == "-CLEAR_PENALTY-" and ctx.timers[popup.team] != 0.0:
                ctx.timers[popup.team] = 0.0
                gui.log(f"{popup.team.name}'s time penalty was cleared", indent=True)

            elif popup_event == "-GIVE-":
                points = gui.popup["-POINTS-"].get()
                end = "" if points == 1 else "s"
                gui.log(
                    f"{popup.team.name} was awarded {points} point" + end, indent=True
                )
                ctx.points[popup.team] += points

            elif popup_event == "-DEDUCT-":
                points = gui.popup["-POINTS-"].get()
                end = "" if points == 1 else "s"
                gui.log(
                    f"{popup.team.name} was deducted {points} point" + end, indent=True
                )
                ctx.points[popup.team] -= points

            if popup_event == "Exit" or popup_event == "-DONE-":
                popup.close()
                popup = None
            else:
                continue

        # check for buzz
        if server.has_next():
            ctx.set_to_buzzed()

        # state specific handling
        if ctx.state == State.UNLOADED or ctx.state == State.PAUSED:
            if event == "-LOAD-":
                index = gui.song_index()
                ctx.load_song(cfg.songs[index])
                gui.log(f"{cfg.songs[index].title}:", new=True)

        if ctx.state == State.PAUSED:
            if event == "-PLAYPAUSE-":
                ctx.set_to_paused()
                if ctx.buzzers_enabled:
                    for team in cfg.teams.values():
                        if ctx.timers[team] == 0.0:
                            server.open(team)

            elif event in [
                "-RED_EDIT-",
                "-BLUE_EDIT-",
                "-GREEN_EDIT-",
                "-YELLOW_EDIT-",
            ]:
                team = cfg.teams[event.strip("-").split("_")[0].lower()]
                popup = Popup(f"Updating {team.name} Team", team, cfg)

        elif ctx.state == State.BUZZED:
            if server.has_next():
                team = server.get()
                gui.log(f"{ctx.team.name} buzzed in!", indent=True)
                popup = Popup(f"{ctx.team.name} Buzzed In!", team, cfg)
                ctx.team_in_focus = team
            else:
                # return to pause state
                server.reset_buzzers()
                server.close_all()
                ctx.set_to_paused()

        elif ctx.state == State.PLAYING:
            ctx.update_timers()

            if ctx.buzzers_enabled:
                for team in cfg.teams.values():
                    if ctx.timers[team] == 0.0:
                        server.open(team)
            else:
                server.close_all()

            if event == "-PLAYPAUSE-":  # or not ctx.player.is_playing(), hmm?
                ctx.set_to_playing()
                server.close_all()

    # shut down gracefully
    print("Bye!")
    ctx.kill()
    gui.close()
    server.shutdown()
