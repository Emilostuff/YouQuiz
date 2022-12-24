from flask import Flask, request, render_template, redirect
import queue
from threading import Thread
from content import QuizConfig
import socket
from content import parse
from werkzeug.serving import make_server


PORT = 600


class ServerThread(Thread):
    def __init__(self, app):
        Thread.__init__(self)
        self.server = make_server(host="0.0.0.0", port=PORT, app=app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()


class Server:
    def __init__(self, cfg: QuizConfig):
        self.cfg = cfg
        self.queue = queue.Queue()
        self.buzzed = [False] * self.cfg.n_teams
        self.accepting = [False] * self.cfg.n_teams
        self.__run()

    def get_url(self):
        hostname = socket.gethostname()
        return "http://" + socket.gethostbyname(hostname) + f":{PORT}"

    def has_next(self):
        return not self.queue.empty()

    def get(self):
        return self.queue.get()

    def close_all(self):
        self.accepting = [False] * self.cfg.n_teams

    def open(self, team):
        self.accepting[team.ident] = True

    def reset_buzzers(self):
        self.buzzed = [False] * self.cfg.n_teams

    def __buzz(self, team):
        i = team.ident
        if self.accepting[i] and not self.buzzed[i]:
            self.queue.put(team)
            self.buzzed[i] = True
            team.play_buzzer()

    def __run(self):
        app = Flask(__name__)

        @app.route("/")
        def home():
            return render_template("index.html", count=self.cfg.n_teams)

        @app.route("/red", methods=["GET", "POST"])
        def red():
            team = self.cfg.teams.red
            if request.method == "POST":
                self.__buzz(team)
            return render_template("red.html")

        @app.route("/blue", methods=["GET", "POST"])
        def blue():
            team = self.cfg.teams.blue
            if request.method == "POST":
                self.__buzz(team)
            return render_template("blue.html")

        @app.route("/green", methods=["GET", "POST"])
        def green():
            team = self.cfg.teams.green
            if team is not None:
                if request.method == "POST":
                    self.__buzz(team)
                return render_template("green.html")
            else:
                return redirect("/")

        @app.route("/yellow", methods=["GET", "POST"])
        def yellow():
            team = self.cfg.teams.yellow
            if team is not None:
                if request.method == "POST":
                    self.__buzz(team)
                return render_template("yellow.html")
            else:
                return redirect("/")

        self.thread = ServerThread(app)
        self.thread.start()

    def shutdown(self):
        self.thread.server.shutdown()


if __name__ == "__main__":
    cfg = parse("config.yml")
    s = Server(cfg)
    input()
    s.shutdown()
