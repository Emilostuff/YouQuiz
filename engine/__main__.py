from server import Server
from content import parse
from gui import Gui, Popup
from state import State, Context
import sys


# load content
if len(sys.argv) < 2:
    print("Please provide a YML config file!")
    sys.exit()
cfg = parse(sys.argv[1])

# initialize modules
ctx = Context(cfg)
server = Server(cfg, ctx)
gui = Gui(cfg)
popup = None

# Display opening message
gui.log(f"Music Quiz Server:  {server.get_url()}")
gui.log(f"———")

# Run the Event Loop
while True:
    event = gui.get_event()
    if event == "Exit":
        break

    # update gui
    gui.refresh(cfg, ctx, focus=popup is None)

    # always handle these events
    if event == "-MARK-":
        ctx.toggle_mark_song(cfg.songs[gui.song_index()])
        gui.update_song_list(cfg, ctx)
    elif event == "-ENABLE-":
        ctx.buzzing_enabled = not ctx.buzzing_enabled
    elif event == "Copy::log":
        gui.copy_selection_from_log()
    elif event == "Copy::info":
        gui.copy_selection_from_info()

    # handle popup if present
    if popup is not None:
        popup_event = popup.get_event()
        if popup_event == "Exit":
            popup.close()
            popup = None
        elif popup_event == "-PENALTY-":
            ctx.timers[popup.team] += cfg.penalty_time
            gui.log(
                f"{popup.team.name} got a {cfg.penalty_time} second time penalty",
                indent=True,
            )
        elif popup_event == "-CLEAR_PENALTY-" and ctx.timers[popup.team] != 0.0:
            ctx.timers[popup.team] = 0.0
            gui.log(f"{popup.team.name}'s time penalty was cleared", indent=True)
        elif popup_event == "-GIVE-":
            points = popup.window["-POINTS-"].get()
            end = "" if points == 1 else "s"
            gui.log(f"{popup.team.name} was awarded {points} point" + end, indent=True)
            ctx.points[popup.team] += points
        elif popup_event == "-DEDUCT-":
            points = popup.window["-POINTS-"].get()
            end = "" if points == 1 else "s"
            gui.log(f"{popup.team.name} was deducted {points} point" + end, indent=True)
            ctx.points[popup.team] -= points
        # skip updating the main window further
        continue

    # check for buzz
    if server.has_next():
        ctx.set_to_buzzed()

    # state specific handling
    if ctx.state == State.UNLOADED or ctx.state == State.PAUSED:
        if event == "-LOAD-":
            index = gui.song_index()
            ctx.load_song(cfg.songs[index])
            gui.update_song_list(cfg, ctx)
            gui.log(f"{cfg.songs[index].title}:", new=True)

    if ctx.state == State.PAUSED:
        if event == "-PLAYPAUSE-":
            ctx.set_to_playing()
        elif event.endswith("_EDIT-"):
            team = cfg.teams[event.strip("-").split("_")[0].lower()]
            popup = Popup(f"Updating {team.name} Team", team, cfg)
    elif ctx.state == State.BUZZED:
        if server.has_next():
            team = server.get()
            gui.log(f"{team.name} buzzed in!", indent=True)
            popup = Popup(f"{team.name} Buzzed In!", team, cfg)
            ctx.team_in_focus = team
        else:
            ctx.set_to_paused()
    elif ctx.state == State.PLAYING:
        ctx.update_timers()
        if event == "-PLAYPAUSE-":
            ctx.set_to_paused()

# Shut down gracefully
print("Bye!")
gui.close()
server.close()
ctx.kill()
