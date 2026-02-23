from tradekit.fees.base import FeeModel
from tradekit.fees.factory import add_fee_model

class FeesBrokerA(FeeModel):
    def __init__(self, bps: int, flat: float):
        self.bps = bps
        self.flat = flat

    def fees(self, df):
        return df['capital'] * self.bps / 10000 + self.flat
    
add_fee_model('my_fees.broker_a', FeesBrokerA)

