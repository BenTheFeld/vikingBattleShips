from flask import Flask, render_template

player = Flask(__name__)


@player.route("/")
def lobby():
    return "hello"


@player.route("/player1")
def player1():
    return "What the hellyyyyy"


@player.route("/player2")
def player2():
    return "player2"

if __name__ == "__main__":
    player.run(debug=True)
