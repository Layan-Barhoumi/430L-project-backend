from ..app import db, ma


class Wallet(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    usd_amount = db.Column(db.Float)
    lbp_amount = db.Column(db.Float)

    def __init__(self, user_id, usd_amount, lbp_amount):
        super(Wallet, self).__init__(user_id=user_id,
                                     usd_amount=usd_amount,
                                     lbp_amount=lbp_amount)


class WalletSchema(ma.Schema):
    class Meta:
        fields = ("user_id", "usd_amount", "lbp_amount")
        model = Wallet


wallet_schema = WalletSchema()
