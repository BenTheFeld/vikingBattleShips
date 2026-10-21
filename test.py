from flask import Flask, render_template

player = Flask(__name__)

@player.route("/")
def lobby():
    return render_template("lobby.html")

@player.route("/player1")
def player1():
    return render_template("p1.html")

@player.route("/player2")
def player2():
    return render_template("p2.html")

if __name__ == "__main__":
    player.run(debug=True)