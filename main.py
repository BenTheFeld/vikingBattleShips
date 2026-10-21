from flask import Flask, render_template, request

player = Flask(__name__)

boardLength = 10

FLEET = {
    "2ship": 2,
    "3ship": 3,
    "4ship": 4
}
def getSqrPos():
    row = int(request.form["row"])
    col = int(request.form["col"])
    return row, col

def placeShip():
    pass

def canPlace():
    pass

class square:
    def __init__(self):
        self.hasShip = False
        self.isHit = False
        self.shipType = None
        self.shipId = None


p1Matrix = [[square() for i in range(boardLength)] for i in range(boardLength)]
p2Matrix = [[square() for i in range(boardLength)] for i in range(boardLength)]

shipsPlaced = {"p1": {}, "p2": {}}
ready = {"p1": False, "p2": False}
turn = "p1"

# temporary — manual test ships until placement logic exists
for row, col in [(0, 0), (0, 1), (0, 2)]:
    p1Matrix[row][col].hasShip = True
    p1Matrix[row][col].shipType = "3ship"

for row, col in [(3, 4), (4, 4), (5, 4), (6, 4)]:
    p2Matrix[row][col].hasShip = True
    p2Matrix[row][col].shipType = "4ship"


@player.route("/")
def lobby():
    return render_template("lobby.html")


@player.route("/player1", methods=["GET", "POST"])
def player1():
    if request.method == "POST":
        row, col = getSqrPos()
        print(f"Selected row {row}, column {col}")
        return render_template(
            "board.html",
            matrix=p1Matrix,
            selected_row=row,
            selected_col=col,
        )
    return render_template("board.html", matrix=p1Matrix)


@player.route("/player2", methods=["GET", "POST"])
def player2():
    if request.method == "POST":
        row, col = getSqrPos()
        return render_template(
            "board.html",
            matrix=p2Matrix,
            selected_row=row,
            selected_col=col,
        )
    return render_template("board.html", matrix=p2Matrix)

if __name__ == "__main__":
    player.run(debug=True, port=5002)
