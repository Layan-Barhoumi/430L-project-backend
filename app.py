import datetime
from flask import Flask, abort
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask import request
from flask import jsonify
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import jwt
from db_config import DB_CONFIG

app = Flask(__name__)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONFIG
CORS(app)
db = SQLAlchemy(app)
app.app_context().push()

SECRET_KEY = "b'|\xe7\xbfU3`\xc4\xec\xa7\xa9zf:}\xb5\xc7\xb9\x139^3@Dv'"


@app.route('/transaction', methods=['POST'])
def post_transaction():
    token = extract_auth_token(request)
    usd_amount = request.json["usd_amount"]
    lbp_amount = request.json["lbp_amount"]
    usd_to_lbp = request.json["usd_to_lbp"]
    if (token is None):
        trans = Transaction(usd_amount=usd_amount, lbp_amount=lbp_amount, usd_to_lbp=usd_to_lbp, user_id=None)
    else:
        try:
            user_id = decode_token(token)
        except:
            abort(403)
        trans = Transaction(usd_amount=usd_amount, lbp_amount=lbp_amount, usd_to_lbp=usd_to_lbp, user_id=user_id)
    db.session.add(trans)
    db.session.commit()
    return jsonify(transaction_schema.dump(trans))


@app.route('/transaction', methods=['GET'])
def get_transactions():
    token = extract_auth_token(request)
    if token is None:
        abort(403)
    else:
        try:
            user_id = decode_token(token)
        except:
            abort(403)
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        return (jsonify(transactions_schema.dump(transactions)))


@app.route('/exchangeRate', methods=['GET'])
def get_exchange_rate(end_date=datetime.datetime.now()):
    # get exchange rate on a certain day
    END_DATE = end_date
    START_DATE = END_DATE - datetime.timedelta(days=3)
    usd_to_lbp = Transaction.query.filter(Transaction.added_date.between(START_DATE, END_DATE), Transaction.usd_to_lbp == True).all()
    if len(usd_to_lbp) != 0:
        rates_usd_to_lbp = []
        sum_usd_to_lbp = 0
        for i in range(len(usd_to_lbp)):
            rates_usd_to_lbp.append(usd_to_lbp[i].lbp_amount / usd_to_lbp[i].usd_amount)
        for i in range(len(rates_usd_to_lbp)):
            sum_usd_to_lbp += rates_usd_to_lbp[i]
        AVERAGE_USD_TO_LBP = sum_usd_to_lbp / len(rates_usd_to_lbp)
        AVERAGE_USD_TO_LBP = round(AVERAGE_USD_TO_LBP, 2)
    else:
        AVERAGE_USD_TO_LBP = "Not available"
    lbp_to_usd = Transaction.query.filter(Transaction.added_date.between(START_DATE, END_DATE), Transaction.usd_to_lbp == False).all()
    if len(lbp_to_usd) != 0:
        rates_lbp_to_usd = []
        sum_lbp_to_usd = 0
        for i in range(len(lbp_to_usd)):
            rates_lbp_to_usd.append(lbp_to_usd[i].lbp_amount / lbp_to_usd[i].usd_amount)
        for i in range(len(rates_lbp_to_usd)):
            sum_lbp_to_usd += rates_lbp_to_usd[i]
        AVERAGE_LBP_TO_USD = sum_lbp_to_usd / len(rates_lbp_to_usd)
        AVERAGE_LBP_TO_USD = round(AVERAGE_LBP_TO_USD, 2)
    else:
        AVERAGE_LBP_TO_USD = "Not available"
    return {"usd_to_lbp": AVERAGE_USD_TO_LBP, "lbp_to_usd": AVERAGE_LBP_TO_USD}


@app.route('/getStats', methods=['GET'])
def get_stats():
    today = datetime.datetime.now()

    # daily stat
    yesterday = today - datetime.timedelta(days=1)
    new_rates_day = get_exchange_rate(today)
    old_rates_day = get_exchange_rate(yesterday)
    delta_usd_to_lbp_day = "Not available"
    delta_lbp_to_usd_day = "Not available"
    if (new_rates_day["usd_to_lbp"] != "Not available" and old_rates_day["usd_to_lbp"] != "Not available"):
        delta_usd_to_lbp_day = int(new_rates_day["usd_to_lbp"]) - int(old_rates_day["usd_to_lbp"])
    if (new_rates_day["lbp_to_usd"] != "Not available" and old_rates_day["lbp_to_usd"] != "Not available"):
        delta_lbp_to_usd_day = int(new_rates_day["lbp_to_usd"]) - int(old_rates_day["lbp_to_usd"])

    # monthly stat
    last_month = today - datetime.timedelta(days=30)
    new_rates_month = get_exchange_rate(last_month)
    old_rates_month = get_exchange_rate(last_month)
    delta_usd_to_lbp_month = "Not available"
    delta_lbp_to_usd_month = "Not available"
    if (new_rates_month["usd_to_lbp"] != "Not available" and old_rates_month["usd_to_lbp"] != "Not available"):
        delta_usd_to_lbp_month = int(new_rates_month["usd_to_lbp"]) - int(old_rates_month["usd_to_lbp"])
    if (new_rates_month["lbp_to_usd"] != "Not available" and old_rates_month["lbp_to_usd"] != "Not available"):
        delta_lbp_to_usd_month = int(new_rates_month["lbp_to_usd"]) - int(old_rates_month["lbp_to_usd"])

    # initialize min and max over the past month to be today's rates
    max_rate_usd_to_lbp = new_rates_day["usd_to_lbp"]
    min_rate_usd_to_lbp = new_rates_day["usd_to_lbp"]
    max_rate_lbp_to_usd = new_rates_day["lbp_to_usd"]
    min_rate_lbp_to_usd = new_rates_day["lbp_to_usd"]

    max_rate_usd_to_lbp_DATE = today.strftime('%a, %d %b %Y')
    min_rate_usd_to_lbp_DATE = today.strftime('%a, %d %b %Y')
    max_rate_lbp_to_usd_DATE = today.strftime('%a, %d %b %Y')
    min_rate_lbp_to_usd_DATE = today.strftime('%a, %d %b %Y')

    # highest and lowest rate
    for i in range(30, -1, -1):
        rate_date = today - datetime.timedelta(days=i)
        rate_value = get_exchange_rate(rate_date)
        rate_usd_to_lbp = rate_value["usd_to_lbp"]
        rate_lbp_to_usd = rate_value["lbp_to_usd"]
        if (rate_usd_to_lbp > max_rate_usd_to_lbp):
            max_rate_usd_to_lbp = rate_usd_to_lbp
            max_rate_usd_to_lbp_DATE = rate_date.strftime('%a, %d %b %Y')
        if (rate_usd_to_lbp < min_rate_usd_to_lbp):
            min_rate_usd_to_lbp = rate_usd_to_lbp
            min_rate_usd_to_lbp_DATE = rate_date.strftime('%a, %d %b %Y')
        if (rate_lbp_to_usd > max_rate_lbp_to_usd):
            max_rate_lbp_to_usd = rate_lbp_to_usd
            max_rate_lbp_to_usd_DATE = rate_date.strftime('%a, %d %b %Y')
        if (rate_lbp_to_usd < min_rate_lbp_to_usd):
            min_rate_lbp_to_usd = rate_lbp_to_usd
            min_rate_lbp_to_usd_DATE = rate_date.strftime('%a, %d %b %Y')

    return {"delta_sell_usd_day": delta_usd_to_lbp_day, "delta_buy_usd_day": delta_lbp_to_usd_day,
            "delta_sell_usd_month": delta_usd_to_lbp_month, "delta_buy_usd_month": delta_lbp_to_usd_month,
            "max_sell_usd_rate": max_rate_usd_to_lbp, "max_sell_usd_rate_DATE": max_rate_usd_to_lbp_DATE,
            "min_sell_usd_rate": min_rate_usd_to_lbp, "min_sell_usd_rate_DATE": min_rate_usd_to_lbp_DATE,
            "max_buy_usd_rate": max_rate_lbp_to_usd, "max_buy_usd_rate_DATE": max_rate_lbp_to_usd_DATE,
            "min_buy_usd_rate": min_rate_lbp_to_usd, "min_buy_usd_rate_DATE": min_rate_lbp_to_usd_DATE,
            }

# get values of rates over the past month, to be graphed
@app.route('/getGraph', methods=['GET'])
def get_graph():
    duration_days = 30
    today = datetime.datetime.now()
    sell_usd_rates = []
    buy_usd_rates = []
    days = []
    for i in range(duration_days, -1, -1):
        x = today - datetime.timedelta(days=i)
        days.append(x)
        x_exchange_rate = get_exchange_rate(x)
        x_sell_usd_rate = x_exchange_rate["usd_to_lbp"]
        sell_usd_rates.append(x_sell_usd_rate)
        x_buy_usd_rate = x_exchange_rate["lbp_to_usd"]
        buy_usd_rates.append(x_buy_usd_rate)

    return {"days": days, "sell_usd_rates": sell_usd_rates, "buy_usd_rates": buy_usd_rates}

# make a request to buy or sell a certain amount in lbp or usd
@app.route('/postExchangeRequest', methods=['POST'])
def post_exchange_request():
    token = extract_auth_token(request)
    sell = request.json["sell"]
    usd = request.json["usd"]
    amount = request.json["amount"]
    location = request.json["location"]
    if (token is not None):
        try:
            user_id = decode_token(token)
        except:
            abort(403)
    else: # user not authenticated
        abort(401)
    req = ExchangeRequest(sell=sell, usd=usd, amount=amount, user_id=user_id, location=location)
    db.session.add(req)
    db.session.commit()
    return jsonify(exchangeRequest_schema.dump(req))

# get all the exchange requests users have made
@app.route('/getExchangeRequest', methods=['GET'])
def get_exchange_requests():
    token = extract_auth_token(request)
    if token is None:
        abort(403)
    else:
        exchange_requests = ExchangeRequest.query.all()
        return (jsonify(exchangeRequests_schema.dump(exchange_requests)))


@app.route('/acceptExchangeRequest', methods=['POST'])
def accept_exchange_request():
    token = extract_auth_token(request)
    if token is None:
        abort(403)
    else:
        try:
            accepter_id = decode_token(token)
        except:
            abort(403)

        request_id = request.json["request_id"]
        exchange_request = ExchangeRequest.query.get(request_id)
        if exchange_request is None:
            abort(404)
        else:
            # get rates of today
            today = datetime.datetime.now()

            today_rates = get_exchange_rate(today)
            sell_usd_rate = today_rates["usd_to_lbp"]
            buy_usd_rate = today_rates["lbp_to_usd"]

            # delete exchange request
            db.session.delete(exchange_request)
            requester_id = exchange_request.user_id
            sell = exchange_request.sell
            usd = exchange_request.usd
            amount = exchange_request.amount

            # get wallets
            accepter_wallet = Wallet.query.filter_by(user_id=accepter_id).first()
            requester_wallet = Wallet.query.filter_by(user_id=requester_id).first()

            # update wallets
            if(sell):
                #sell usd
                if(usd):
                    accepter_wallet.usd_amount+= amount
                    requester_wallet.usd_amount-= amount
                    delta_amount_lbp = amount * sell_usd_rate
                    accepter_wallet.lbp_amount-=delta_amount_lbp
                    requester_wallet.lbp_amount+=delta_amount_lbp

                #sell lbp
                else:
                    accepter_wallet.lbp_amount+= amount
                    requester_wallet.lbp_amount-= amount
                    delta_amount_usd = amount/buy_usd_rate
                    accepter_wallet.usd_amount-= delta_amount_usd
                    requester_wallet.usd_amount+= delta_amount_usd
            else:
                # buy usd
                if(usd):
                    accepter_wallet.usd_amount-= amount
                    requester_wallet.usd_amount+= amount
                    delta_amount_lbp = amount * buy_usd_rate
                    accepter_wallet.lbp_amount+= delta_amount_lbp
                    requester_wallet.lbp_amount-= delta_amount_lbp

                # buy lbp
                else:
                    accepter_wallet.lbp_amount-= amount
                    requester_wallet.lbp_amount+= amount
                    delta_amount_usd = amount/sell_usd_rate
                    accepter_wallet.usd_amount+= delta_amount_usd
                    requester_wallet.usd_amount-= delta_amount_usd

            db.session.commit()

            return jsonify({"message": "Exchange request accepted."}), 200


# get user's usd and lbp balance
@app.route('/getWallet', methods=['GET'])
def get_wallet():
    token = extract_auth_token(request)
    if token is None:
        abort(403)
    else:
        try:
            user_id = decode_token(token)
        except:
            abort(403)
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        return jsonify({"usd_balance": wallet.usd_amount, "lbp_balance": wallet.lbp_amount})

@app.route('/user', methods=['POST'])
def post_user():
    user_name = request.json["user_name"]
    password = request.json["password"]
    user = User(user_name=user_name, password=password)
    db.session.add(user)
    db.session.commit()
    user_id = user.id
    # when a user registers, add a default wallet for demo purposes
    wallet = Wallet(user_id=user_id, usd_amount=5000, lbp_amount=700000000)
    db.session.add(wallet)
    db.session.commit()
    return jsonify(user_schema.dump(user))


@app.route('/authentication', methods=['POST'])
def authenticate_user():
    user_name = request.json["user_name"]
    password = request.json["password"]
    if (user_name is None or password is None):
        abort(400)
    else:
        name = User.query.filter_by(user_name=user_name).first()
        if (name is None):
            abort(403)
        else:
            checkPass = bcrypt.check_password_hash(name.hashed_password, password)
            if (not checkPass):
                abort(403)
            else:
                token = create_token(name.id)
                return ({"token": token})


def create_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=4),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm='HS256'
    )


def extract_auth_token(authenticated_request):
    auth_header = authenticated_request.headers.get('Authorization')
    if auth_header:
        return auth_header.split(" ")[1]
    else:
        return None


def decode_token(token):
    payload = jwt.decode(token, SECRET_KEY, 'HS256')
    return payload['sub']


if __name__ == '__main__':
    app.run(debug=True, host='192.168.2.204', port=5000)

from .model.user import User, user_schema
from .model.transaction import Transaction, transactions_schema, transaction_schema
from .model.wallet import Wallet, wallet_schema
from .model.exchangeRequest import ExchangeRequest, exchangeRequest_schema, exchangeRequests_schema