from flask import Flask, render_template, request, url_for, redirect
from werkzeug.exceptions import HTTPException

player = Flask(__name__)
player.jinja_env.globals["shipImage"] = lambda *args: shipImage(*args)


@player.errorhandler(Exception)
def handle_crash(e):
    if isinstance(e, HTTPException):
        raise e
    print(f"Unhandled error on {request.path}: {e}")
    if request.path.startswith("/player2"):
        return redirect(url_for("player2"))
    return redirect(url_for("player1"))

boardLength = 10

FLEET = {
    "3tile": 3,
    "5tile": 5,
}

PLAYER_COLOR = {"p1": "blå", "p2": "rød"}

# Maps (shipType, color, state, segment index) -> filename on disk.
# "ødelagt" entries that are None fall back to the "full" art for that
# segment (no broken-art asset exists yet for that spot).
SHIP_ART = {
    "3tile": {
        "blå": {
            "full": {0: "blå_oppe_full-frame0.png", 1: "blå_midt_full-frame0.png", 2: "blå_bunn_full-frame0.png"},
            "ødelagt": {0: "blå_topp_ødelagtaseprite-frame0.png", 1: "blå_midt_ødelagt-frame0.png", 2: "blå_bunn_ødelagt-frame0.png"},
        },
        "rød": {
            "full": {0: "rød_topp_full-frame0.png", 1: "rød_midt_full-frame0.png", 2: "rød_bunn_full-frame0.png"},
            "ødelagt": {0: "rød_topp_ødelagt-frame0.png", 1: "rød_midt_ødelagt-frame0.png", 2: None},
        },
    },
    "5tile": {
        "blå": {
            "full": {i: f"5tile_#{i + 1}_full_blå-frame0.png" for i in range(5)},
            "ødelagt": {i: f"tile#{i + 1}_ødelagt_blå-frame0.png" for i in range(5)},
        },
        "rød": {
            "full": {i: f"5tile_#{i + 1}_full_rød-frame0.png" for i in range(5)},
            "ødelagt": {i: f"tile#{i + 1}_ødelagt_rød-frame0.png" for i in range(5)},
        },
    },
}


def shipImage(shipType, color, state, segment):
    ship_art = SHIP_ART.get(shipType, {}).get(color, {})
    filename = ship_art.get(state, {}).get(segment)
    if filename is None:
        state = "full"
        filename = ship_art.get("full", {}).get(segment)
    if filename is None:
        return None
    return f"assets/ships/{shipType}/{state}/{filename}"
def getSqrPos():
    try:
        row = int(request.form.get("row", ""))
        col = int(request.form.get("col", ""))
    except ValueError:
        return None, None
    if not (0 <= row < boardLength and 0 <= col < boardLength):
        return None, None
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
    for segment, (r, c) in enumerate(shipCells(row, col, length, orientation)):
        matrix[r][c].hasShip = True
        matrix[r][c].shipType = shipType
        matrix[r][c].shipId = shipType
        matrix[r][c].segment = segment
        matrix[r][c].orientation = orientation
    return True

class square:
    def __init__(self):
        self.hasShip = False
        self.isHit = False
        self.shipType = None
        self.shipId = None
        self.segment = None
        self.orientation = None

    def css_class(self, hide_ships=False):
        if hide_ships and not self.isHit:
            return "empty"
        if self.hasShip:
            return "ship hit" if self.isHit else "ship"
        return "miss" if self.isHit else "empty"

    def image_path(self, color, hide_ships=False):
        if not self.hasShip:
            return None
        if hide_ships and not self.isHit:
            return None
        state = "ødelagt" if self.isHit else "full"
        return shipImage(self.shipType, color, state, self.segment)


p1Matrix = [[square() for i in range(boardLength)] for i in range(boardLength)]
p2Matrix = [[square() for i in range(boardLength)] for i in range(boardLength)]

shipsPlaced = {"p1": {}, "p2": {}}
ready = {"p1": False, "p2": False}
turn = "p1"
lastShot = {"p1": None, "p2": None}
placeError = {"p1": None, "p2": None}
VIEW_ENDPOINT = {"p1": "player1", "p2": "player2"}


def otherPlayer(me):
    return "p2" if me == "p1" else "p1"


def renderPlacement(matrix, player_key):
    remaining = [s for s in FLEET if s not in shipsPlaced[player_key]]
    error = placeError[player_key]
    placeError[player_key] = None
    return render_template(
        "place.html",
        matrix=matrix,
        title="Your Fleet",
        hide_ships=False,
        clickable=False,
        post_url=url_for(f"place_{player_key}"),
        remaining=remaining,
        fleet=FLEET,
        color=PLAYER_COLOR[player_key],
        error=error,
    )


def gameOrPlacement(matrix, enemy_matrix, player_key, title, enemy_title, fire_endpoint):
    other = otherPlayer(player_key)
    if not ready[player_key]:
        return renderPlacement(matrix, player_key)
    if not ready[other]:
        return render_template("waiting.html")
    return renderGame(matrix, title, enemy_matrix, enemy_title, player_key, fire_endpoint)


def handlePlacement(matrix, player_key):
    shipType = request.form.get("shipType", "")
    orientation = request.form.get("orientation", "")
    row, col = getSqrPos()

    if shipType not in FLEET or orientation not in ("horizontal", "vertical") or row is None:
        placeError[player_key] = "That placement didn't go through, try again."
    elif shipType in shipsPlaced[player_key]:
        placeError[player_key] = "Already placed that ship."
    elif not placeShip(matrix, row, col, shipType, orientation):
        placeError[player_key] = "Can't place there."
    else:
        shipsPlaced[player_key][shipType] = True
        if len(shipsPlaced[player_key]) == len(FLEET):
            ready[player_key] = True

    return redirect(url_for(VIEW_ENDPOINT[player_key]))


def renderGame(my_matrix, my_title, enemy_matrix, enemy_title, me, fire_endpoint):
    other = otherPlayer(me)
    last_shot = lastShot[me]
    lastShot[me] = None
    return render_template(
        "game.html",
        own_matrix=my_matrix,
        own_title=my_title,
        own_color=PLAYER_COLOR[me],
        enemy_matrix=enemy_matrix,
        enemy_title=enemy_title,
        enemy_color=PLAYER_COLOR[other],
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
    return handlePlacement(p1Matrix, "p1")


@player.route("/player2/place", methods=["POST"])
def place_p2():
    return handlePlacement(p2Matrix, "p2")


@player.route("/player1/fire", methods=["POST"])
def fire_p1():
    global turn
    row, col = getSqrPos()
    if row is not None:
        target = p2Matrix[row][col]
        if turn == "p1" and not target.isHit:
            target.isHit = True
            lastShot["p1"] = {"hit": target.hasShip, "shipType": target.shipType if target.hasShip else None}
            if not target.hasShip:
                turn = "p2"
    return redirect(url_for("player1"))


@player.route("/player2/fire", methods=["POST"])
def fire_p2():
    global turn
    row, col = getSqrPos()
    if row is not None:
        target = p1Matrix[row][col]
        if turn == "p2" and not target.isHit:
            target.isHit = True
            lastShot["p2"] = {"hit": target.hasShip, "shipType": target.shipType if target.hasShip else None}
            if not target.hasShip:
                turn = "p1"
    return redirect(url_for("player2"))


if __name__ == "__main__":
    player.run(host="0.0.0.0", debug=True, port=5002)
