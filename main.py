from flask import Flask, render_template, request, url_for

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

def getSqrData(matrix, row, col):
    square = matrix[row][col]
    return {
        "hasShip": square.hasShip,
        "isHit": square.isHit,
        "shipType": square.shipType,
        "shipId": square.shipId
    }

def shipCells(row, col, length, orientation):
    cells = []
    for i in range(length):
        r = row + i if orientation == "vertical" else row
        c = col + i if orientation == "horizontal" else col
        if not (0 <= r < boardLength and 0 <= c < boardLength):
            return None
        cells.append((r, c))
    return cells

def canPlace(matrix, row, col, length, orientation):
    cells = shipCells(row, col, length, orientation)
    if cells is None:
        return False
    return all(not matrix[r][c].hasShip for r, c in cells)

def placeShip(matrix, row, col, shipType, orientation):
    length = FLEET[shipType]
    if not canPlace(matrix, row, col, length, orientation):
        return False
    for r, c in shipCells(row, col, length, orientation):
        matrix[r][c].hasShip = True
        matrix[r][c].shipType = shipType
        matrix[r][c].shipId = shipType
    return True

class square:
    def __init__(self):
        self.hasShip = False
        self.isHit = False
        self.shipType = None
        self.shipId = None

    def css_class(self, hide_ships=False):
        if hide_ships and not self.isHit:
            return "empty"
        if self.hasShip:
            return "ship hit" if self.isHit else "ship"
        return "miss" if self.isHit else "empty"


p1Matrix = [[square() for i in range(boardLength)] for i in range(boardLength)]
p2Matrix = [[square() for i in range(boardLength)] for i in range(boardLength)]

shipsPlaced = {"p1": {}, "p2": {}}
ready = {"p1": False, "p2": False}
turn = "p1"


def otherPlayer(me):
    return "p2" if me == "p1" else "p1"


def renderPlacement(matrix, player_key, error=None):
    remaining = [s for s in FLEET if s not in shipsPlaced[player_key]]
    return render_template(
        "place.html",
        matrix=matrix,
        title="Your Fleet",
        hide_ships=False,
        clickable=False,
        post_url=url_for(f"place_{player_key}"),
        remaining=remaining,
        fleet=FLEET,
        error=error,
    )


def gameOrPlacement(matrix, enemy_matrix, player_key, title, enemy_title, fire_endpoint):
    other = otherPlayer(player_key)
    if not ready[player_key]:
        return renderPlacement(matrix, player_key)
    if not ready[other]:
        return render_template("waiting.html")
    return renderGame(matrix, title, enemy_matrix, enemy_title, player_key, fire_endpoint)


def handlePlacement(matrix, enemy_matrix, player_key, title, enemy_title, fire_endpoint):
    shipType = request.form["shipType"]
    orientation = request.form["orientation"]
    row = int(request.form["row"])
    col = int(request.form["col"])

    if shipType in shipsPlaced[player_key]:
        return renderPlacement(matrix, player_key, error="Already placed that ship.")

    if not placeShip(matrix, row, col, shipType, orientation):
        return renderPlacement(matrix, player_key, error="Can't place there.")

    shipsPlaced[player_key][shipType] = True
    if len(shipsPlaced[player_key]) == len(FLEET):
        ready[player_key] = True

    return gameOrPlacement(matrix, enemy_matrix, player_key, title, enemy_title, fire_endpoint)


def renderGame(my_matrix, my_title, enemy_matrix, enemy_title, me, fire_endpoint, last_shot=None):
    return render_template(
        "game.html",
        own_matrix=my_matrix,
        own_title=my_title,
        enemy_matrix=enemy_matrix,
        enemy_title=enemy_title,
        your_turn=(turn == me),
        fire_url=url_for(fire_endpoint),
        last_shot=last_shot,
    )


@player.route("/")
def lobby():
    music_playing = request.args.get("music") == "on"
    return render_template("lobby.html", music_playing=music_playing)


@player.route("/player1")
def player1():
    return gameOrPlacement(p1Matrix, p2Matrix, "p1", "Your Fleet", "Enemy Waters", "fire_p1")


@player.route("/player2")
def player2():
    return gameOrPlacement(p2Matrix, p1Matrix, "p2", "Your Fleet", "Enemy Waters", "fire_p2")


@player.route("/player1/place", methods=["POST"])
def place_p1():
    return handlePlacement(p1Matrix, p2Matrix, "p1", "Your Fleet", "Enemy Waters", "fire_p1")


@player.route("/player2/place", methods=["POST"])
def place_p2():
    return handlePlacement(p2Matrix, p1Matrix, "p2", "Your Fleet", "Enemy Waters", "fire_p2")


@player.route("/player1/fire", methods=["POST"])
def fire_p1():
    global turn
    row, col = getSqrPos()
    target = p2Matrix[row][col]
    last_shot = None
    if turn == "p1" and not target.isHit:
        target.isHit = True
        last_shot = {"hit": target.hasShip, "shipType": target.shipType if target.hasShip else None}
        if not target.hasShip:
            turn = "p2"
    return renderGame(p1Matrix, "Your Fleet", p2Matrix, "Enemy Waters", "p1", "fire_p1", last_shot)


@player.route("/player2/fire", methods=["POST"])
def fire_p2():
    global turn
    row, col = getSqrPos()
    target = p1Matrix[row][col]
    last_shot = None
    if turn == "p2" and not target.isHit:
        target.isHit = True
        last_shot = {"hit": target.hasShip, "shipType": target.shipType if target.hasShip else None}
        if not target.hasShip:
            turn = "p1"
    return renderGame(p2Matrix, "Your Fleet", p1Matrix, "Enemy Waters", "p2", "fire_p2", last_shot)


if __name__ == "__main__":
    player.run(debug=True, port=5002)
