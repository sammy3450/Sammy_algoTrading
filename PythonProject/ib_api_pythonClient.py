from ibapi.client import *  #EClient sends messages to TWS
from ibapi.wrapper import * #EWrapper receives and processes messages from TWS
from ibapi.contract import *

from time import sleep
from threading import Thread
from datetime import datetime

#calling values from config
from config import host, port, client_id, ib_account

contract_request_dictionary = {
    1: {'symbol': 'NVDA', 'conId': 4815747, 'exchange': 'NASDAQ'},
#    2: {'symbol': 'AAPL', 'conId': 265598, 'exchange': 'NASDAQ'},
#    3: {'symbol': 'MSFT', 'conId': 272093, 'exchange': 'NASDAQ'},
}

class TradeApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self,self)

        #custom attributes - these have now been initialized in the self function
        self.account_balance = None
        self.account_equity = None
        self.portfolio = {} #setting it as an empty dictionary
        self.market_data = {} #creates empty dictionary

        self.next_order_id = None

        # to give empty dictionary keys with stock tickers from contract_request_dictionary
        # creates this Market Data: {'AAPL': {}, 'MSFT': {}, 'NVDA': {}}
        for key in contract_request_dictionary:
            self.market_data[contract_request_dictionary[key]['symbol']] = {
                'bid': None,
                'ask': None,
                'last': None
            }

    # Custom functions
    def getNextValidId(self):
        valid_order_id = self.next_order_id
        self.next_order_id +=1
        return self.next_order_id

    #EWrapper functions
    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        #this line gives all the values from the account
        #print this to figure out what all is needed and then filter with the next line using key
        #print("UpdateAccountValue. Key", key, "Value", val, "Currency", currency, "AccountName", accountName)

        #currentTime = datetime.now()
        if key == 'TotalCashBalance' and currency == 'BASE':
        #    print(currentTime, 'Cash balance is:', val)
            self.account_balance = val
        if key == 'NetLiquidationByCurrency' and currency == 'BASE':
        #    print(currentTime, 'Net Liquidation value is:', val)
            self.account_equity = val

    def updatePortfolio(self, contract: Contract, position: Decimal, marketPrice: float, marketValue: float, averageCost: float, unrealizedPNL: float,
                             realizedPNL: float, accountName: str):

        # This is a dictionary and Local symbol pulls the unique information for each position
        # then we use this unique info to pull other information
        self.portfolio[contract.localSymbol] = {
            'Position': decimalMaxString(position),
            'MarketPrice': floatMaxString(marketPrice),
            'MarketValue': floatMaxString(marketValue),
            'AverageCost': floatMaxString(averageCost),
            'unrealizedPNL': floatMaxString(unrealizedPNL),
            'realizedPNL': floatMaxString(realizedPNL)
        }

        """
        print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:",
              contract.exchange, "Position:", decimalMaxString(position), "MarketPrice:", floatMaxString(marketPrice),
              "MarketValue:", floatMaxString(marketValue), "AverageCost:", floatMaxString(averageCost),
              "UnrealizedPNL:", floatMaxString(unrealizedPNL), "RealizedPNL:", floatMaxString(realizedPNL),
              "AccountName:", accountName)
        """

    def tickPrice(self, reqID: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
#        print(reqID, tickType, price, attrib)
        symbol = contract_request_dictionary[reqID]['symbol']
        for key in contract_request_dictionary:
            if tickType == 1:
                self.market_data[symbol]['bid'] = price
            elif tickType == 2:
                self.market_data[symbol]['ask'] = price
            elif tickType == 4:
                self.market_data[symbol]['last'] = price

    def nextValidId(self, orderId: int):
        print("nextValidId:", orderId)
        self.next_order_id = orderId



if __name__ == "__main__":
    app = TradeApp()

    app.connect(host, port, client_id)
    sleep(1) #giving app 1 second to connect

    #app.run() prevents running more code while it runs. so we use threading which allows us to run multiple parts concurrently
    app_thread = Thread(target=app.run, daemon=True) #daemon - when we exit main thread block, it will kill existing threads
    app_thread.start()


    app.reqAccountUpdates(True, ib_account)

    #defining contracts and reqID
    app.reqMarketDataType(2)  # requests delayed market data 1 = Live, 2 = Frozen, 3 = Delayed, 4 = Delayed Frozen
    contract = Contract()
    for key in contract_request_dictionary:
        reqId = key
        contract.conId = contract_request_dictionary[reqId]['conId']
        contract.exchange = contract_request_dictionary[reqId]['exchange']
        app.reqMktData(reqId, contract, "", False, False,[])

    sleep(3)

    # Open a market order
    market_order = Order()
    market_order.action = 'BUY'
    market_order.orderType = 'MKT'
    market_order.tif = 'DAY'
    market_order.totalQuantity = 1

    next_valid_id = app.getNextValidId()
    app.placeOrder(next_valid_id, contract, market_order)

    while True:

        current_time = datetime.now()
       # print(current_time, 'Balance', app.account_balance, 'Equity', app.account_equity)
        data = [current_time, app.account_balance, app.account_equity]
        print("Current time:",data[0])
        print("Balance", data[1])
        print("Equity", data[2])

        for key in app.portfolio:
            print('Portfolio:', key, app.portfolio[key])
        print(datetime.now(), 'Market Data:', app.market_data)
        print("--\n")

        sleep(5)

