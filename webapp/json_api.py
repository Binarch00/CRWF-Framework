from flask import g, jsonify, abort
from webapp import app
from settings import logger
from database.models import User


@app.route("/api/btc_address", methods=["GET"], endpoint="api.btc_address")
def btc_address():
    if g.user:
        address = g.user.btc_address()
        if not address:
            User.link_crypto_address(g.user.id)
            address = g.user.btc_address()
        data = {
            "btc": address
        }
        return jsonify(data)
    else:
        abort(403, "Login Required!")
