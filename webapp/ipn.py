from flask import abort, request, jsonify
from webapp import app
import database
from database.models import UserTransactions, CryptoAddress
from settings import logger, IPN_AUTH


@app.route("/ipn", methods=["GET", "POST"], endpoint="ipn.crypto_in")
def crypto_in():
    if request.method == "POST":
        auth = request.form.get("ipn_auth")
        if auth != IPN_AUTH:
            abort(401)
        address = request.form.get("address")
        confirmed = float(request.form.get("confirmed"))
        unconfirmed = float(request.form.get("unconfirmed"))
        logger.warning("IPN address {} -- confirmed {} -- unconfirmed {}".format(address, confirmed, unconfirmed))
        session = database.Session(autocommit=False)
        user = CryptoAddress.get_address_user(address=address, session=session)
        if user:
            logger.warning("IPN for user {} -- address {}".format(user, address))
            dep = UserTransactions.get_user_netdeposits(user, session=session)
            if confirmed > dep:
                UserTransactions.add_transaction(user, confirmed-dep, "deposit", reference="IPN", session=session)
                logger.warning("Deposit confirmed! user {} -- address {} -- amount {}".format(user, address, confirmed-dep))
            else:
                logger.warning("Confirmed is lower than net deposit yet. User {} -- address {} -- conf {} -- dep {} "
                               .format(user, address, confirmed, dep))
        else:
            logger.error("Address {} don't match any user.".format(address))
        data = {
            "address": address,
            "confirmed": confirmed,
            "unconfirmed": unconfirmed,
            "ipn_auth": auth
        }
        return jsonify(data)
    else:
        logger.error("Invalid request at IPN url!")
        abort(401)
