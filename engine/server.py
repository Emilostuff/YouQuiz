from flask import (
    Flask,
    request,
    render_template,
    redirect,
    Response,
    stream_with_context,
    abort,
)
import queue
from threading import Thread, Lock
from content import QuizConfig
import socket
from content import parse
from werkzeug.serving import make_server
import json
import time
from datetime import datetime


PORT = 600
STREAM_INTERVAL = 0.1


class ServerThread(Thread):
    def __init__(self, app):
        Thread.__init__(self)
        self.server = make_server(host="0.0.0.0", port=PORT, app=app, threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()


class Server:
    def __init__(self, cfg: QuizConfig):
        self.cfg = cfg
        self.queue = queue.Queue()
        self.buzzed = {team: False for team in self.cfg.teams.values()}
        self.accepting = {team: False for team in self.cfg.teams.values()}
        self.lock = Lock()
        self.__run()

    def setup_read_access(self, program):
        self.program = program

    def get_url(self):
        hostname = socket.gethostname()
        return "http://" + socket.gethostbyname_ex(hostname)[-1][-1] + f":{PORT}"

    def has_next(self):
        return not self.queue.empty()

    def get(self):
        return self.queue.get()

    def close_all(self):
        self.lock.acquire()
        self.accepting = {team: False for team in self.cfg.teams.values()}
        self.lock.release()

    def open(self, team):
        self.lock.acquire()
        self.accepting[team] = True
        self.lock.release()

    def reset_buzzers(self):
        self.lock.acquire()
        self.buzzed = {team: False for team in self.cfg.teams.values()}
        self.lock.release()

    def __buzz(self, team):
        self.lock.acquire()
        if self.accepting[team] and not self.buzzed[team]:
            self.queue.put(team)
            self.buzzed[team] = True
            team.play_buzzer()
        self.lock.release()

    def __run(self):
        app = Flask(__name__)

        @app.route("/")
        def home():
            return render_template("index.html", count=self.cfg.n_teams)

        @app.route("/<color>", methods=["GET", "POST"])
        def buzzer(color):
            if color not in self.cfg.teams:
                abort(404)

            team = self.cfg.teams[color]
            if team is not None:
                if request.method == "POST":
                    self.__buzz(team)
                return render_template("buzzer.html", color=team.name.lower())
            else:
                return redirect("/")

        @app.route("/live")
        def live() -> str:
            return render_template(
                "live.html", count=self.cfg.n_teams, title=self.cfg.title
            )

        def stream_data():
            try:
                while True:
                    data = dict()
                    focus_team = self.program.team_in_focus
                    for team in self.cfg.teams.values():
                        x = dict()
                        x["points"] = self.program.points[team]
                        x["timer"] = round(self.program.timers[team], 1)
                        x["buzzed"] = self.buzzed[team]
                        x["focus"] = focus_team is not None and focus_team is team
                        data[team.name] = x

                    yield f"data:{json.dumps(data)}\n\n"
                    time.sleep(STREAM_INTERVAL)
            except GeneratorExit:
                pass

        @app.route("/live-data")
        def live_data() -> Response:
            response = Response(
                stream_with_context(stream_data()), mimetype="text/event-stream"
            )
            response.headers["Cache-Control"] = "no-cache"
            response.headers["X-Accel-Buffering"] = "no"
            return response

        self.thread = ServerThread(app)
        self.thread.start()

    def shutdown(self):
        self.thread.server.shutdown()


if __name__ == "__main__":
    cfg = parse("examples/test.yml")
    s = Server(cfg)
    print(s.get_url())
    input()
    s.shutdown()
