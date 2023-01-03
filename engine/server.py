from flask import Flask, request, render_template, Response, stream_with_context, abort
import queue
from threading import Thread, Lock
from content import QuizConfig
import socket
from werkzeug.serving import make_server
import json
import time


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
    def __init__(self, cfg: QuizConfig, ctx):
        self.cfg = cfg
        self.ctx = ctx
        self.queue = queue.Queue()
        self.lock = Lock()
        self.__run()

    def get_url(self):
        hostname = None
        while hostname is None:
            try:
                # connect
                hostname = socket.gethostname()
            except:
                print("Could not obtain host ip")
        return "http://" + socket.gethostbyname_ex(hostname)[-1][-1] + f":{PORT}"

    def has_next(self):
        return not self.queue.empty()

    def get(self):
        return self.queue.get()

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
            if request.method == "POST":
                self.lock.acquire()
                if self.ctx.try_add_buzz(team):
                    self.queue.put(team)
                    team.play_buzzer()
                self.lock.release()
            return render_template("buzzer.html", color=team.name.lower())

        @app.route("/live")
        def live() -> str:
            return render_template(
                "live.html",
                count=self.cfg.n_teams,
                title=self.cfg.title,
                teams=[t.name.lower() for t in self.cfg.teams.values()],
            )

        def stream_data():
            try:
                print("Live data connection established")
                while True:
                    data = dict()
                    focus_team = self.ctx.team_in_focus
                    for team in self.cfg.teams.values():
                        x = dict()
                        x["points"] = self.ctx.points[team]
                        x["timer"] = round(self.ctx.timers[team], 1)
                        x["buzzed"] = team in self.ctx.buzzed
                        x["focus"] = focus_team is not None and focus_team is team
                        data[team.name.lower()] = x

                    yield f"data:{json.dumps(data)}\n\n"
                    time.sleep(STREAM_INTERVAL)
            except GeneratorExit:
                print("Live data connection closed")
                pass

        @app.route("/live-data")
        def live_data() -> Response:
            response = Response(
                stream_with_context(stream_data()), mimetype="text/event-stream"
            )
            response.headers["Cache-Control"] = "no-cache"
            response.headers["X-Accel-Buffering"] = "no"
            return response

        # start server
        self.thread = ServerThread(app)
        self.thread.start()

    def close(self):
        self.thread.server.shutdown()
