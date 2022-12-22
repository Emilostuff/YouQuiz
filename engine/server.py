from flask import Flask, request, render_template
import queue
from threading import Thread
from content import Team
import socket
from content import Audio


PORT = 600


class Server:
    def __init__(self, buzzers: list[Audio]):
        self.queue = queue.Queue()
        self.buzzed = [False] * len(Team)
        self.accepting = [False] * len(Team)
        self.buzzers = [b.get_player() for b in buzzers]
        thread = Thread(target=self.__run_thread, args=())
        thread.start()

    def get_url(self):
        hostname = socket.gethostname()
        return "http://" + socket.gethostbyname(hostname) + f":{PORT}"

    def has_next(self):
        return not self.queue.empty()

    def get(self):
        return self.queue.get()

    def close_all(self):
        self.accepting = [False] * len(Team)

    def open(self, team):
        self.accepting[team.value] = True

    def reset_buzzers(self):
        self.buzzed = [False] * len(Team)

    def __run_thread(self):
        app = Flask(__name__)

        @app.route("/")
        def home():
            return render_template("index.html")

        @app.route("/red", methods=["GET", "POST"])
        def red():
            i = Team.RED.value
            if self.accepting[i] and not self.buzzed[i] and request.method == "POST":
                self.queue.put(Team.RED)
                self.buzzed[i] = True
                self.buzzers[i].stop()
                self.buzzers[i].play()

            return render_template("red.html")

        @app.route("/blue", methods=["GET", "POST"])
        def blue():
            i = Team.BLUE.value
            if self.accepting[i] and not self.buzzed[i] and request.method == "POST":
                self.queue.put(Team.BLUE)
                self.buzzed[i] = True
                self.buzzers[i].stop()
                self.buzzers[i].play()

            return render_template("blue.html")

        app.run(debug=False, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    s = Server()
    s.open(Team.RED)

    while True:
        if s.has_next():
            print(f"Buzz from {s.get()}")
