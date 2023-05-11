import datetime
from ..app import db, ma

class ExchangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sell = db.Column(db.Boolean)
    usd = db.Column(db.Boolean)
    amount = db.Column(db.Float)
    location = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __init__(self, sell, usd, amount, user_id, location):
        super(ExchangeRequest, self).__init__(sell=sell,
                                              usd=usd,
                                              amount=amount,
                                              location=location,
                                              user_id=user_id)


class ExchangeRequestSchema(ma.Schema):
    class Meta:
        fields = ("id", "sell", "usd", "amount", "location", "user_id")
        model = ExchangeRequest


exchangeRequest_schema = ExchangeRequestSchema()
exchangeRequests_schema = ExchangeRequestSchema(many=True)

