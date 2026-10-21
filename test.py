from flask import Flask, render_template, request

player = Flask(__name__)

@player.route("/")
def lobby():
    return render_template("lobby.html")

@player.route("/player1", methods=["GET", "POST"])
def player1():
    if request.method == "POST":
        name = request.form["username"]
        return f"hello, {name}"
    return render_template("p1.html")

@player.route("/player2")
def player2():
    return render_template("p2.html")

if __name__ == "__main__":
    player.run(debug=True, port=5001)