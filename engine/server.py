from flask import Flask, request, render_template


def run_server(queue):
    app = Flask(__name__)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/red", methods=["GET", "POST"])
    def red():
        if request.method == "POST":
            queue.put("red")

        return render_template("red.html")

    @app.route("/blue", methods=["GET", "POST"])
    def blue():
        if request.method == "POST":
            queue.put("blue")

        return render_template("blue.html")

    app.run(debug=False, host="0.0.0.0", port=9999)
