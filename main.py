#!/usr/bin/env python3

import sys
from math import *
import numpy as np


class Model:
    def __init__(self, n_past, horizon):
        self.n_past=n_past
        self.horizon=horizon
        self.fitted=False

    def reg_lin(self, X, y):
        mat1=np.linalg.inv(np.dot(X.T, X))
        beta=np.dot(np.dot(mat1, X.T), y)
        return beta

    def fit(self, Data):
        close_arr=np.array(Data.close)
        open_arr=np.array(Data.open)
        max_arr=np.array(Data.high)
        min_arr=np.array(Data.low)
        Y = ((np.roll(close_arr, shift=-self.horizon) - close_arr)/close_arr)[self.n_past:-self.horizon].reshape(-1, 1)
        diff_close=(np.roll(close_arr, shift=-1) - close_arr)[:-1]
        diff_open=(np.roll(open_arr, shift=-1) - open_arr)[:-1]
        diff_max=(np.roll(max_arr, shift=-1) - max_arr)[:-1]
        diff_min=(np.roll(min_arr, shift=-1) - min_arr)[:-1]
        X = np.ones((Y.shape[0], self.n_past))
        for i in range(Y.shape[0]):
            X[i, :self.n_past] = diff_close[i:i+self.n_past]
            #X[i, self.n_past:2*self.n_past] = diff_open[i:i+self.n_past]
            #X[i, 2*self.n_past:3*self.n_past] = diff_max[i:i+self.n_past]
            #X[i, 3*self.n_past:4*self.n_past] = diff_min[i:i+self.n_past]
        self.beta = self.reg_lin(X, Y)
        self.fitted=True

    def predict(self, Data):
        if self.fitted:
            close_arr=np.array(Data.close[-self.n_past-1:])
            #open_arr=np.array(Data.open[-self.n_past-1:])
            #high_arr=np.array(Data.high[-self.n_past-1:])
            #low_arr=np.array(Data.low[-self.n_past-1:])

            shift_close=(np.roll(close_arr, shift=-1)-close_arr)[:-1]
            #shift_open=(np.roll(open_arr, shift=-1)-open_arr)[:-1]
            #shift_high=(np.roll(high_arr, shift=-1)-high_arr)[:-1]
            #shift_low=(np.roll(low_arr, shift=-1)-low_arr)[:-1]

            #X_pred = np.hstack((shift_close, shift_open, shift_high, shift_low)).reshape(1, -1)
            X_pred=np.hstack((shift_close)).reshape(1, -1)
            return np.dot(X_pred, self.beta)[0]
        else:
            return None

class Position:
    def __init__(self, horizon):
        self.horizon=horizon
        self.pos=0 # pas dans un trade
        self.last_trade=-1

    def rules(self, prediction, stack_usd, stack_btc, last_price):
        if prediction is None:
            print("no_moves", file=sys.stdout)

        elif self.pos==0 and prediction>0.003:
            print('=== BUY===', file=sys.stderr)
            print(stack_usd, file=sys.stderr)
            print(last_price, file=sys.stderr)
            amount = np.floor(stack_usd/last_price*1000)/1000
            self.last_trade=0
            self.pos=1
            print("buy USDT_BTC "+str(amount), file=sys.stdout)
            # buy
        elif self.pos==1 and self.last_trade>=self.horizon:
            amount=stack_btc
            print('=== SELL ===', file=sys.stderr)
            print(amount, file=sys.stderr)
            print("sell USDT_BTC "+str(amount), file=sys.stdout)
            # sell
            self.last_trade=-1
            self.pos=0
        elif self.pos==1:
            self.last_trade+=1
            print("no_moves", file=sys.stdout)
            # do nothing
        else:
            print("no_moves", file=sys.stdout)
            # do nothing




class Data:
    def __init__(self):
        self.date = []
        self.high = []
        self.low = []
        self.open = []
        self.close = []
        self.volume = []

    def debug_print_all(self):
        print("Date: ")
        print(self.date, end = "\n\n")
        print("High: ")
        print(self.high, end = "\n\n")
        print("Low: ")
        print(self.low, end = "\n\n")
        print("Open: ")
        print(self.open, end = "\n\n")
        print("Close: ")
        print(self.close, end = "\n\n")
        print("Volume: ")
        print(self.volume, end = "\n\n")

    def add_values(self, _format, values):
        idx = 0
        for val in _format:
            if val == "pair": pass
            if val == "date": self.date.append(int(values[idx]))
            if val == "high": self.high.append(float(values[idx]))
            if val == "low": self.low.append(float(values[idx]))
            if val == "open": self.open.append(float(values[idx]))
            if val == "close": self.close.append(float(values[idx]))
            if val == "volume": self.volume.append(float(values[idx]))
            idx += 1

class Trade:
    def __init__(self):
        self.BTC_ETH = Data()
        self.USDT_ETH = Data()
        self.USDT_BTC = Data()

        self.stack_BTC = None
        self.stack_ETH = None
        self.stack_USDT = None

        self.player_names = None
        self.your_bot = None
        self.timebank = None
        self.time_per_move = None
        self.candle_interval = None
        self.candle_format = None
        self.candles_total = None
        self.candles_given = None
        self.initial_stack = None
        self.transaction_fee_percent = None

        self.error = None
        self.pair_idx = None

        self.index=0

        self.horizon=10
        self.n_past=5
        self.model = Model(self.n_past, self.horizon)
        self.position = Position(self.horizon)
    
    def eprint(self, err):
        print(err, file=sys.stderr)

    def check_none(self):
        missing = None
        if self.player_names == None: missing = "player_names"
        if self.your_bot == None: missing = "your_bot"
        if self.timebank == None: missing = "timebank"
        if self.time_per_move == None: missing = "time_per_move"
        if self.candle_format == None: missing = "candle_format"
        if self.candles_total == None: missing = "candles_total"
        if self.candles_given == None: missing = "candles_given"
        if self.initial_stack == None: missing = "initial_stack"
        if self.transaction_fee_percent == None: missing = "transaction_fee_percent"
        if missing != None:
            raise ValueError("missing setting \"" + missing + "\"" )

    def get_settings(self):
        for i in range(0, 10):
            array = input().split(" ")
            if (len(array) < 3 or array[0] != "settings"):
                raise ValueError("bad settings format")
            if array[1] == "player_names": self.player_names = array[2]
            elif array[1] == "your_bot": self.your_bot = array[2]
            elif array[1] == "timebank": self.timebank = int(array[2])
            elif array[1] == "time_per_move": self.time_per_move = int(array[2])
            elif array[1] == "candle_interval": self.candle_interval = int(array[2])
            elif array[1] == "candle_format": self.candle_format = array[2].split(",")
            elif array[1] == "candles_total": self.candles_total = int(array[2])
            elif array[1] == "candles_given": self.candles_given = int(array[2])
            elif array[1] == "initial_stack": self.initial_stack = int(array[2])
            elif array[1] == "transaction_fee_percent": self.transaction_fee_percent = float(array[2])
            else:
                raise ValueError("unknown setting \"" + array[1] + "\"" )

    def add_data(self, array):
        pairs = array.split(";")
        pair = self.pair_idx
        for val in pairs:
            values = val.split(",")
            if len(values) != 7:
                raise ValueError("missing value in one of the pairs")
            if (values[pair] == "BTC_ETH"):
                self.BTC_ETH.add_values(self.candle_format, values)
            elif (values[pair] == "USDT_ETH"):
                self.USDT_ETH.add_values(self.candle_format, values)
            elif (values[pair] == "USDT_BTC"):
                self.USDT_BTC.add_values(self.candle_format, values)
        # [debug]
        #self.BTC_ETH.debug_print_all()
        #self.USDT_ETH.debug_print_all()
        #self.USDT_BTC.debug_print_all()

    def order(self, values):
        pred= self.model.predict(self.USDT_BTC)
        print(self.index, " ", pred, file=sys.stderr)
        #if (self.index > 100):
         #   print(self.model.beta);
        self.position.rules(pred, self.stack_USDT, self.stack_BTC, self.USDT_BTC.close[-1])

    def get_stack(self, values):
        array = values.split(",")
        if (len(array) != 3):
            raise ValueError("invalid stack format: \"" + values + "\"")
        for val in array:
            values = val.split(":")
            if (len(values) != 2):
                raise ValueError("invalid stack: \"" + val + "\"")
            elif (values[0] == "BTC"):
                self.stack_BTC = float(values[1])
            elif (values[0] == "ETH"):
                self.stack_ETH = float(values[1])
            elif (values[0] == "USDT"):
                self.stack_USDT = float(values[1])
            else:
                raise ValueError("unknow value \"" + val + "\"")
        # [debug]
        #print(self.stack_BTC)
        #print(self.stack_ETH)
        #print(self.stack_USDT)

    def where_is_pair(self):
        idx = 0
        for val in self.candle_format:
            if (val == "pair"):
                self.pair_idx = idx
                break
            idx += 1

    def loop(self):
        try:

            # [debug]
            #self.candle_format = "pair,date,high,low,open,close,volume"
            self.get_settings()
            self.check_none()
            self.where_is_pair()
            while True:
                self.index+=1
                print("ok1", file=sys.stderr)
                print(self.index, file=sys.stderr)
                print(self.model.fitted, file=sys.stderr)
                if self.index >0 and self.index%50==0:
                    self.model.fit(self.USDT_BTC)
                    print("ok2", file=sys.stderr)
                array = input().split(" ")
                if (array[0] == "update" and array[1] == "game" and array[2] == "next_candles"):
                    self.add_data(array[3])
                elif (array[0] == "update" and array[1] == "game" and array[2] == "stacks"):
                    self.get_stack(array[3])
                elif (array[0] == "action" and array[1] == "order"):
                    self.order(array[2])
                else:
                    self.eprint("Error: unknown command.")
        except Exception as error:
            print("Error: ", end = '')
            print(error, end = '\n')
            exit(84)

def main():
    obj = Trade()
    obj.loop()

main()