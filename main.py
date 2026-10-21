from flask import Flask, render_template

player = Flask(__name__)

boardLength = 10


class square:
    def __init__(self):
        self.hasShip = False
        self.isHit = False
        self.shipType = None
        self.shipId = None


p1Matrix = [[square() for i in range(boardLength)] for i in range(boardLength)]

p2Matrix = [[square() for i in range(boardLength)] for i in range(boardLength)]

turn = "p1"

# temporary — manual test ships until placement logic exists
for row, col in [(0, 0), (0, 1), (0, 2)]:
    p1Matrix[row][col].hasShip = True
    p1Matrix[row][col].shipType = "Drakkar"

for row, col in [(3, 4), (4, 4), (5, 4), (6, 4)]:
    p2Matrix[row][col].hasShip = True
    p2Matrix[row][col].shipType = "Snekkja"


@player.route("/")
def lobby():
    return render_template("lobby.html")


@player.route("/player1")
def player1():
    return render_template("board.html", matrix=p1Matrix)


@player.route("/player2")
def player2():
    return render_template("board.html", matrix=p2Matrix)

if __name__ == "__main__":
    player.run(debug=True)
