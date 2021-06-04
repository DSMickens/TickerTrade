import os
import sys
import alpaca_trade_api as ata
import math
from multiprocessing import Process
from time import sleep
import logging
import datetime
sys.path.append('/Users/Danny/git/Ticker-Projects')
import TPasswords

#PAPER
#"""
os.environ["APCA_API_KEY_ID"] = TPasswords.alpaca_key_id_paper
os.environ["APCA_API_SECRET_KEY"] = TPasswords.alpaca_secret_key_paper
os.environ["APCA_API_BASE_URL"] = TPasswords.alpaca_base_url_paper
#"""
#LIVE
"""
os.environ["APCA_API_KEY_ID"] = TPasswords.alpaca_key_id_live
os.environ["APCA_API_SECRET_KEY"] = TPasswords.alpaca_secret_key_live
os.environ["APCA_API_BASE_URL"] = TPasswords.alpaca_base_url_live
"""
api = ata.REST()
account = api.get_account()
updateProcess = None

logger = logging.getLogger('TickerTrader')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('logger.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

#****************************** LIMIT BUY ORDER *******************************#
def limit_buy(ticker, price, quantity):
    api.submit_order(
        symbol=ticker,
        side='buy',
        type='limit',
        limit_price=price,
        qty=quantity,
        time_in_force='day',
        extended_hours=True,
    )
    logger.info("ordered {0} shares of {1} at a maximum share price of ${2:.2f} per share\n".format(quantity, ticker, price))

#****************************** MARKET BUY ORDER ******************************#
def market_buy(ticker, quantity):
    api.submit_order(
        symbol=ticker,
        side='buy',
        type='market',
        qty=quantity,
        time_in_force='day',
        extended_hours=False,
    )
    logger.info("ordered {0} shares of {1} at market price\n".format(quantity, ticker))

#****************************** LIMIT SELL ORDER ******************************#
def limit_sell(ticker, price, quantity):
    api.submit_order(
        symbol=ticker,
        side='sell',
        type='limit',
        limit_price=price,
        qty=quantity,
        time_in_force='day',
        extended_hours=True
    )
    logger.info("ordered to sell {0} shares of {1} at a minimum share price of ${2:.2f} per share\n".format(quantity, ticker, price))

#****************************** MARKET SELL ORDER *****************************#
def market_sell(ticker, quantity):
    api.submit_order(
        symbol=ticker,
        side='sell',
        type='market',
        qty=quantity,
        time_in_force='day',
        extended_hours=False
    )
    logger.info("ordered to sell {0} shares of {1} at market price\n".format(quantity, ticker))

#****************************** BRACKET ORDER FOR LONG POSITION ***************#
def bracket_limit_buy(ticker, price, quantity, stop_loss = None, take_profit=None, profit_percent = None):
    if not stop_loss:
        stop_loss = math.floor(price * 99.9)/100.0 if price - 0.02 > math.floor(price * 99.9)/100.0 else price - 0.02
    if not take_profit:
        if not profit_percent:
            profit_percent = 0.25
        take_profit = round(price * (1 + float(profit_percent) / 100), 2)
    api.submit_order(
        symbol=ticker,
        side='buy',
        type='limit',
        limit_price=price,
        qty=quantity,
        time_in_force='day',
        order_class='bracket',
        take_profit={'limit_price': take_profit},
        stop_loss={'stop_price': stop_loss},
    )
    logger.info(
    """ordered {0} shares of {1} at ${2:.2f} per share to sell at ${3:.2f} per share for
    a gain, or ${4:.2f} per share for a loss\n""".format(quantity, ticker, float(price), float(take_profit), float(stop_loss)))

#*********************** MARKET BRACKET ORDER FOR LONG POSITION ***************#
def bracket_market_buy(ticker, quantity, stop_loss, take_profit):
    api.submit_order(
        symbol=ticker,
        side='buy',
        type='market',
        qty=quantity,
        time_in_force='day',
        order_class='bracket',
        take_profit={'limit_price': take_profit},
        stop_loss={'stop_price': stop_loss},
    )
    logger.info(
    """ordered {0} shares of {1} at market price to sell at ${2:.2f} per share for
    a gain, or ${3:.2f} per share for a loss\n""".format(quantity, ticker, float(take_profit), float(stop_loss)))

#****************************** BRACKET ORDER FOR SHORT POSITION **************#
def bracket_limit_sell(ticker, price, quantity, stop_loss = None, take_profit=None, profit_percent = None):
    if not stop_loss:
        stop_loss = math.ceil(price * 99.9)/100.0 if price + 0.02 < math.floor(price * 99.9)/100.0 else price + 0.02
    else:
        float(stop_loss)
    if not profit_percent:
        profit_percent = 0.25
    if not take_profit:
        take_profit = round(price * (1 - float(profit_percent) / 100), 2)
    api.submit_order(
        symbol=ticker,
        side='sell',
        type='limit',
        limit_price=price,
        qty=quantity,
        time_in_force='day',
        order_class='bracket',
        take_profit={'limit_price': take_profit},
        stop_loss={'stop_price': stop_loss},
    )
    logger.info(
    """short ordered {0} shares of {1} at ${2:.2f} per share to buy at ${3:.2f}
    per share for a gain, or ${4:.2f} per share for a loss\n""".format(quantity, ticker, price, take_profit, stop_loss))

#*********************** MARKET BRACKET ORDER FOR SHORT POSITION **************#
def bracket_market_sell(ticker, quantity, stop_loss, take_profit):
    api.submit_order(
        symbol=ticker,
        side='sell',
        type='market',
        qty=quantity,
        time_in_force='day',
        order_class='bracket',
        take_profit={'limit_price': take_profit},
        stop_loss={'stop_price': stop_loss},
    )
    logger.info(
    """short ordered {0} shares of {1} at market price to buy at ${2:.2f}
    per share for a gain, or ${3:.2f} per share for a loss\n""".format(quantity, ticker, take_profit, stop_loss))

#****************************** OCO BUY ORDER *********************************#
def oco_buy(ticker, quantity, stop_loss, take_profit):
    api.submit_order(
        symbol=ticker,
        side='buy',
        type='limit',
        qty=quantity,
        time_in_force='day',
        order_class='oco',
        take_profit={'limit_price': take_profit},
        stop_loss={'stop_price': stop_loss},
    )
    logger.info(
    """placed order to buy {0} shares of {1} at ${2:.2f} per share for a profit
    or ${3:.2f} per share for a loss\n""".format(quantity, ticker, take_profit, stop_loss))

#****************************** OCO SELL ORDER ********************************#
def oco_sell(ticker, quantity, stop_loss, take_profit):
    api.submit_order(
        symbol=ticker,
        side='sell',
        type='limit',
        qty=quantity,
        time_in_force='day',
        order_class='oco',
        take_profit={'limit_price': take_profit},
        stop_loss={'stop_price': stop_loss},
    )
    logger.info(
    """placed order to sell {0} shares of {1} at ${2:.2f} per share for a profit
    or ${3:.2f} per share for a loss\n""".format(quantity, ticker, take_profit, stop_loss))

#****************************** TRAILING STOP BUY *****************************#
def trailing_stop_buy(ticker, quantity, trail_price = None, trail_percent = None):
    if trail_price is not None:
        api.submit_order(
            symbol=ticker,
            side='buy',
            type='trailing_stop',
            qty=quantity,
            time_in_force='day',
            trail_price=trail_price,
        )
        logger.info("Trailing Stop ordered to buy {0} shares of {1} when price is ${2:.2f} below the high water mark".format(quantity, ticker, float(trail_price)))
    elif trail_percent is not None:
        api.submit_order(
            symbol=ticker,
            side='buy',
            type='trailing_stop',
            qty=quantity,
            time_in_force='day',
            trail_percent=trail_percent,
        )
        logger.info("Trailing Stop ordered to buy {0} shares of {1} when price is {2:.2f}% below the high water mark".format(quantity, ticker, float(trail_percent)))
    else:
        logger.error("trail price and trail percent cannot both be empty\n")

#****************************** TRAILING STOP SELL ****************************#
def trailing_stop_sell(ticker, quantity, trail_price = None, trail_percent = None):
    if trail_price is not None:
        api.submit_order(
            symbol=ticker,
            side='sell',
            type='trailing_stop',
            qty=quantity,
            time_in_force='day',
            trail_price=trail_price,
        )
        logger.info("Trailing Stop ordered to sell {0} shares of {1} when price is ${2:.2f} below the high water mark".format(quantity, ticker, float(trail_price)))
    elif trail_percent is not None:
        api.submit_order(
            symbol=ticker,
            side='sell',
            type='trailing_stop',
            qty=quantity,
            time_in_force='day',
            trail_percent=trail_percent,
        )
        logger.info("Trailing Stop ordered to sell {0} shares of {1} when price is {2}% below the high water mark".format(quantity, ticker, float(trail_percent)))
    else:
        logger.error("trail price and trail percent cannot both be empty\n")

#****************************** UPDATE ORDERS *********************************#
def updateOrders():
    orders = []
    while (1):
	    sleep(1)
	    for x in api.list_orders():
	        order = x.__dict__["_raw"]

#****************************** CANCEL ALL ORDERS *****************************#
def cancelAll():
	api.cancel_all_orders()
	logger.info("Canceled all orders\n")

#****************************** CANCEL TICKER ORDERS **************************#
def cancelTicker(ticker):
	order_found = False
	for x in api.list_orders():
		order = x.__dict__["_raw"]
		if order["symbol"] == ticker:
			api.cancel_order(order["id"])
			order_found = True
	if order_found:
		logger.info("Canceled all {0} orders\n".format(ticker))
	else:
		logger.info("No orders found for ticker {0}\n".format(ticker))

#****************************** CANCEL INDIVIDUAL ORDERS **********************#
def cancelOrder(id):
	api.cancel_order(id)
	logger.info("Canceled order {0}\n".format(id))

#****************************** CLOSED ORDERS *********************************#
def getClosedOrders():
    for x in api.list_orders(status='closed'):
        print(x)

#****************************** HELP ******************************************#
def help():
    print("""
        buy market [ticker] [quantity]
        buy limit [ticker] [price] [quantity]
        buy bracket [ticker] [price] [quantity] [stop price] [take profit %] [stop loss %]
        sell market [ticker] [quantity]
        sell limit [ticker] [price] [quantity]
        auto short/long wall [ticker] [price] [percent increase]
        auto short/long trend [ticker] [price] [percent increase] [stop price percent]
        cancel id/ticker/"all"
        panic ticker/"all"
        update on/off
        orders
        positions
        quit
    """)

#****************************** CHOOSE HELPER METHOD **************************#
def choose(name, choices):
    alternates = []
    for x in choices:
        dehyphenated = x.split()
        if len(dehyphenated) > 1:
            y = ""
            for word in dehyphenated:
                y += word[0]
            alternates.append(y)
        else:
            alternates.append(x[0])
    choice = input("{0} ({1}): ".format(name, ", ".join(choices)))
    choices.extend(alternates)
    choices = [x.upper() for x in choices]
    if choice.upper() in choices:
        return choice
    else:
        raise Exception("invalid choice - {0}".format(choice))

#****************************** UPDATE ACCOUNT ********************************#
def updateAccount():
    global account
    account = api.get_account()

#****************************** GET ACCOUNT DETAILS ***************************#
def handleAccount(inpt):
    updateAccount()
    if len(inpt) == 1:
        print("Portfolio Value: ", account.portfolio_value)
        print("Buying Power:    ", account.buying_power)
        print("Profit/Loss:      {0:.3f}%".format((float(account.equity) / float(account.last_equity) - 1) * 100))
    elif inpt[1] in ["FULL", "F"]:
        print(account)

#****************************** BUY COMMAND ***********************************#
def handleBuy(inpt):
    if len(inpt) > 1:
        order_type = inpt[1]
        if order_type in ["LIMIT", "L"]:
            ticker = inpt[2]
            price = float(inpt[3])
            quantity = int(inpt[4])
            limit_buy(ticker, price, quantity)
        elif order_type in ["MARKET", "M"]:
            ticker = inpt[2]
            quantity = int(inpt[3])
            market_buy(ticker, quantity)
        elif order_type in ["BRACKET", "B"]:
            ticker = inpt[2]
            price = float(inpt[3])
            quantity = int(inpt[4])
            stop_loss = float(inpt[5])
            if (float(inpt[6]) <= 0.5):
                profit_percent = float(inpt[6])
                bracket_limit_buy(ticker, price, quantity, stop_loss, profit_percent=profit_percent)
            else:
                take_profit = float(inpt[6])
                bracket_limit_buy(ticker, price, quantity, stop_loss, take_profit)
        elif order_type in ["ONE CANCELS ONE", "OCO"]:
            ticker = inpt[2]
            quantity = int(inpt[3])
            stop_loss = float(inpt[4])
            take_profit = float(inpt[5])
            oco_buy(ticker, quantity, stop_loss, take_profit)
        elif order_type in ["TRAILING STOP", "TS"]:
            ticker = inpt[2].upper()
            quantity = int(inpt[3])
            trail_type = inpt[4].upper()
            if trail_type == "PRICE":
                trail_price = inpt[5]
                trailing_stop_buy(ticker, quantity, trail_price)
            elif trail_type == "PERCENT":
                trail_percent = inpt[5]
                trailing_stop_buy(ticker, quantity, trail_percent=trail_percent)
        else:
            print("Invalid buy command - {0}\n".format(order_type))
    else:
        order_type = choose("Order Type", ["LIMIT", "MARKET", "BRACKET", "ONE CANCELS ONE", "TRAILING STOP"]).upper()
        if order_type in ["LIMIT", "L"]:
            ticker = input("ticker: ").upper()
            price = float(input("price: "))
            quantity = int(input("quantity: "))
            limit_buy(ticker, price, quantity)
        elif order_type in ["MARKET", "M"]:
            ticker = input("ticker: ").upper()
            quantity = int(input("quantity: "))
            market_buy(ticker, quantity)
        elif order_type in ["BRACKET", "B"]:
            ticker = input("ticker: ").upper()
            price = float(input("price: "))
            quantity = int(input("quantity: "))
            stop_loss = float(input("stop loss: "))
            take_profit = float(input("take profit: "))
            if take_profit == "":
                profit_percent = float(input("profit percent: "))
                bracket_limit_buy(ticker, price, quantity, stop_loss, profit_percent=profit_percent)
            else:
                bracket_limit_buy(ticker, price, quantity, stop_loss, take_profit)
        elif order_type in ["ONE-CANCELS-ONE", "OCO"]:
            ticker = input("ticker: ").upper()
            quantity = int(input("quantity: "))
            stop_loss = float(input("stop loss: "))
            take_profit = float(input("take profit: "))
            oco_buy(ticker, quantity, stop_loss, take_profit)
        elif order_type in ["TRAILING STOP", "TS"]:
            ticker = input("ticker: ").upper()
            quantity = int(input("quantity: "))
            trail_type = choose("trail type", ["PRICE", "PERCENT"]).upper()
            print(trail_type)
            if trail_type == "PRICE":
                trail_price = float(input("trail price: "))
                trailing_stop_buy(ticker, quantity, trail_price)
            elif trail_type == "PERCENT":
                trail_percent = float(input("trail percent: "))
                trailing_stop_buy(ticker, quantity, trail_percent=trail_percent)
        else:
            print("invalid buy command - {0}\n".format(order_type))

#****************************** SELL COMMAND **********************************#
def handleSell(inpt):
    if len(inpt) > 1:
        order_type = inpt[1]
        if order_type in ["LIMIT", "L"]:
            ticker = inpt[2]
            price = float(inpt[3])
            quantity = int(inpt[4])
            limit_sell(ticker, price, quantity)
        elif order_type in ["MARKET", "M"]:
            ticker = inpt[2]
            quantity = int(inpt[3])
            market_sell(ticker, quantity)
        elif order_type in ["BRACKET", "B"]:
            ticker = inpt[2]
            price = float(inpt[3])
            quantity = int(inpt[4])
            stop_loss = float(inpt[5])
            if (float(inpt[6]) <= 0.5):
                profit_percent = float(inpt[6])
                bracket_limit_sell(ticker, price, quantity, stop_loss, profit_percent=profit_percent)
            else:
                take_profit = float(inpt[6])
                bracket_limit_sell(ticker, price, quantity, stop_loss, take_profit)
        elif order_type in ["ONE CANCELS ONE", "OCO"]:
            ticker = inpt[2]
            quantity = int(inpt[3])
            stop_loss = float(inpt[4])
            take_profit = float(inpt[5])
            oco_sell(ticker, quantity, stop_loss, take_profit)
        elif order_type in ["TRAILING STOP", "TS"]:
            ticker = inpt[2]
            quantity = int(inpt[3])
            trail_type = inpt[4].upper()
            if trail_type == "PRICE":
                trail_price = float(inpt[5])
                trailing_stop_sell(ticker, quantity, trail_price)
            elif trail_type == "PERCENT":
                trail_percent = float(inpt[5])
                trailing_stop_sell(ticker, quantity, trail_percent=trail_percent)
        else:
            print("invalid sell command - {0}\n".format(order_type))
    else:
        order_type = choose("order type", ["LIMIT", "MARKET", "BRACKET", "ONE CANCELS ONE", "TRAILING STOP"]).upper()
        if order_type in ["LIMIT", "L"]:
            ticker = input("ticker: ").upper()
            price = float(input("price: "))
            quantity = int(input("quantity: "))
            limit_sell(ticker, price, quantity)
        elif order_type in ["MARKET", "M"]:
            ticker = input("ticker: ").upper()
            quantity = int(input("quantity: "))
            market_sell(ticker, quantity)
        elif order_type in ["BRACKET", "B"]:
            ticker = input("ticker: ").upper()
            price = float(input("price: "))
            quantity = int(input("quantity: "))
            stop_loss = float(input("stop loss: "))
            take_profit = float(input("take profit: "))
            if take_profit == "":
                profit_percent = float(input("profit percent: "))
                bracket_limit_sell(ticker, price, quantity, stop_loss, profit_percent=profit_percent)
            else:
                bracket_limit_sell(ticker, price, quantity, stop_loss, take_profit)
        elif order_type in ["ONE-CANCELS-ONE", "OCO"]:
            ticker = input("ticker: ").upper()
            quantity = int(input("quantity: "))
            stop_loss = float(input("stop loss: "))
            take_profit = float(input("take profit: "))
            oco_buy(ticker, quantity, stop_loss, take_profit)
        elif order_type in ["TRAILING STOP", "TS"]:
            ticker = input("ticker: ").upper()
            quantity = int(input("quantity: "))
            trail_type = choose("trail type", ["PRICE", "PERCENT"]).upper()
            if trail_type == "PRICE":
                trail_price = float(input("trail price: "))
                trailing_stop_sell(ticker, quantity, trail_price)
            elif trail_type == "PERCENT":
                trail_percent = float(input("trail percent: "))
                trailing_stop_sell(ticker, quantity, trail_percent=trail_percent)
        else:
            print("invalid sell command - {0}\n".format(order_type))

#****************************** AUTO COMMAND **********************************#
def handleAuto(inpt):
    updateAccount()
    buying_power = float(account.buying_power)
    buying_power //= 10
    if len(inpt) > 1:
        position_type = inpt[1]
        ticker = inpt[2]
        price = float(inpt[3])
        auto_type = inpt[4]
        quantity_remaining = buying_power // price
        if quantity_remaining < 4:
            print("not enough buying power for the auto function")
        percent_change = 0.25
        if auto_type in ["WALL", "W"]:
            if len(inpt) >= 5:
                percent_change = float(inpt[5])
        if auto_type in ["TREND", "T"]:
            if position_type in ["LONG", "L"]:
                if len(inpt) >= 6:
                    stop_loss = float(inpt[5])
                else:
                    stop_loss = math.floor(price * 99.7)/100.0
            elif position_type in ["SHORT", "S"]:
                if len(inpt) >= 6:
                    stop_loss = float(inpt[5])
                else:
                    stop_loss = math.ceil(price * 100.3)/100.0
            else:
                print("Incorrect choice for short/long position type - {0}\n".format(position_type))
                return
            if len(inpt) >= 7:
                percent_change = float(inpt[6])
        else:
            print("Incorrect choice for auto type - {0}\n".format(auto_type))
            return
    else:
        position_type = choose("Side", ["long", "short"]).upper()
        ticker = input("ticker: ").upper()
        price = float(input("price: "))
        auto_type = choose("Auto Type", ["trend", "wall"]).upper()
        quantity_remaining = buying_power // price
        if quantity_remaining < 4:
            print("not enough buying power for the auto function\n")
        percent_change = input("percent change (default is .25%):")
        if not percent_change:
            percent_change = 0.25
        else:
            float(percent_change)
        if auto_type in ["TREND", "T"]:
            if position_type in ["LONG", "L"]:
                stop_loss = input("stop price (default .3% is {0:.2f}):".format(math.floor(price * 99.7)/100.0))
                if not stop_loss:
                    stop_loss = math.floor(price * 99.7)/100.0
            elif position_type in ["SHORT", "S"]:
        	    stop_loss = input("stop price (default .3% is {0:.2f}):".format(math.ceil(price * 100.3)/100.0))
        	    if not stop_loss:
        	        stop_loss = math.ceil(price * 100.3)/100.0
            else:
                print("incorrect choice for position type - {0}\n".format(position_type))
                return
    if auto_type in ["WALL", "W"]:
        for x in range(4):
            quantity = quantity_remaining // (4 - x)
            quantity_remaining -= quantity
            if position_type in ["LONG", "L"]:
                bracket_limit_buy(ticker, price, quantity, profit_percent=(percent_increase * (x + 1)))
            elif position_type in ["SHORT", "S"]:
        	    bracket_limit_sell(ticker, price, quantity, profit_percent=(percent_increase * (x + 1)))
            else:
        	    print("incorrect choice for position type - {0}\n".format(position_type))
        	    return
    elif auto_type in ["TREND", "T"]:
        for x in range(4):
            quantity = quantity_remaining // (4 - x)
            quantity_remaining -= quantity
            if position_type in ["LONG", "L"]:
                bracket_limit_buy(ticker, price, quantity, stop_loss=stop_loss, profit_percent=(percent_change * (x + 1)))
            elif position_type in ["SHORT", "S"]:
                bracket_limit_sell(ticker, price, quantity, stop_loss=stop_loss, profit_percent=(percent_change * (x + 1)))

#****************************** QUICK COMMAND *********************************#
def handleQuick(inpt):
    if len(inpt) == 7 or len(inpt) == 8:
        side = inpt[1]
        if side not in ["BUY", "B", "SELL", "S"]:
            print("Wrong position choice - {0}\n".format(pos_type))
            return
        order_type = inpt[2]
        ticker = inpt[3]
        if order_type in ["LIMIT", "L"]:
            price = inpt[4]
            quantity = int(inpt[5])
            take_profit = inpt[6]
            stop_loss = inpt[7]
            if pos_type in ["BUY", "B"]:
                bracket_limit_buy(ticker, price, quantity, stop_loss, take_profit)
            else:
                bracket_limit_sell(ticker, price, quantity, stop_loss, take_profit)
        elif order_type in ["MARKET", "M"]:
            quantity = int(inpt[4])
            take_profit = int(inpt[5])
            stop_loss = int(inpt[6])
            print("TODO: market quick orders")
        else:
            print("Wrong market/limit type choice - {0}\n".format(order_type))
            return
    else:
        side = choose("Side", ["buy", "sell"]).upper()
        order_type = choose("Type", ["market", "limit"]).upper()
        ticker = input("Ticker: ").upper()
        if order_type in ["LIMIT", "L"]:
            price = float(input("Price: "))
            quantity = int(input("Quantity: "))
            take_profit = int(input("Profit Per Share (in cents, minimum {0}): ".format(math.ceil(float(price) * .1))))
            stop_loss = int(input("Max Loss Per Share (in cents, maximum {0}): ".format(math.ceil(float(price) * .1))))
            if side in ["BUY", "B"]:
                stop_loss = price - (stop_loss / 100.0)
                take_profit = price + (take_profit / 100.0)
                bracket_limit_buy(ticker, price, quantity, stop_loss, take_profit)
            if side in ["SELL", "S"]:
                stop_loss = price + (stop_loss / 100.0)
                take_profit = price - (take_profit / 100.0)
                bracket_limit_sell(ticker, price, quantity, stop_loss, take_profit)
        elif order_type in ["MARKET", "M"]:
            quantity = int(input("Quantity: "))
            take_profit = int(input("Profit Per Share (in cents, min .1% of market price): "))
            stop_loss = int(input("Max Loss Per Share (in cents): "))
            print("TODO: market quick orders")
        else:
            print("Wrong market/limit choice - {0}\n".format(order_type))

#***************************** PRESET COMMAND *********************************#
def handlePreset():
    side = None
    order_type = None
    ticker = None
    price = None
    quantity = None
    inpt = ""
    while len(inpt) < 1:
        inpt = input(">> PRESET MODE >> ").strip().upper().split()
    if len(inpt) >= 1:
        while inpt[0] not in ["QUIT", "Q"]:
            cmd = inpt[0]
            if cmd in ["LIST", "L"]:
                print("side: ", side)
                print("order_type: ", order_type)
                print("ticker: ", ticker)
                print("price: ", price)
                print("quantity: ", quantity)
            elif cmd in ["SET", "S"]:
                try:
                    param = inpt[1].upper()
                    val = inpt[2].upper()
                    if param in ["SIDE", "S"]:
                        side = val
                    elif param in ["ORDER_TYPE", "OT"]:
                        order_type = val
                    elif param in ["TICKER", "T"]:
                        ticker = val
                    elif param in ["PRICE", "P"]:
                        price = float(val)
                    elif param in ["QUANTITY", "Q"]:
                        quantity = int(val)
                    elif param in ["STOP_LOSS", "SL"]:
                        stop_loss = float(val)
                    elif param in ["TAKE_PROFIT", "TP"]:
                        take_profit = float(val)
                    elif param in ["PROFIT_PERCENT", "PP"]:
                        profit_percent = float(val)
                except IndexError as ie:
                    print("Usage: set [param] [value]")
                    logger.error(ie)
                except Error as e:
                    logger.error(e)
            elif cmd in ["REMOVE", "R"]:
                try:
                    param = inpt[1].upper()
                    if param in ["SIDE", "S"]:
                        side = None
                    elif param in ["ORDER_TYPE", "OT"]:
                        order_type = None
                    elif param in ["TICKER", "T"]:
                        ticker = None
                    elif param in ["PRICE", "P"]:
                        price = None
                    elif param in ["QUANTITY", "Q"]:
                        quantity = None
                    elif param in ["STOP_LOSS", "SL"]:
                        stop_loss = None
                    elif param in ["TAKE_PROFIT", "TP"]:
                        take_profit = None
                    elif param in ["PROFIT_PERCENT", "PP"]:
                        profit_percent = None
                except IndexError as ie:
                    print("Usage: set [param] [value]")
                    logger.error(ie)
                except Error as e:
                    logger.error(e)
            elif cmd in ["EXECUTE", "E"]:
                placeholder = 1
                if side is None:
                    side = inpt[placeholder]
                    placeholder = placeholder + 1
                if order_type is None:
                    order_type = inpt[placeholder]
                    placeholder = placeholder + 1
                if ticker is None:
                    ticker = inpt[placeholder]
                    placeholder = placeholder + 1
                if price is None and order_type in ["LIMIT", "L"]:
                    price = float(inpt[placeholder])
                    placeholder = placeholder + 1
                if quantity is None:
                    quantity = int(inpt[placeholder])
                    placeholder = placeholder + 1
                order_list = ([side, order_type, ticker, price, quantity])
                order_list = [" " if x is None else x for x in order_list]
                handleInput(order_list)
            elif cmd in ["PANIC", "P"]:
                handlePanic(inpt)
            elif cmd in ["CANCEL", "C"]:
                handleCancel(inpt)
            inpt = ""
            while len(inpt) < 1:
                inpt = input(">> PRESET MODE >> ").strip().upper().split()

    print("Exiting Preset Mode")

#****************************** CANCEL COMMAND ********************************#
def handleCancel(inpt):
    if len(inpt) > 1:
        if inpt[1] == "orders":
            cancelAll()
        elif len(inpt[1]) < 7:
            cancelTicker(inpt[1])
        else:
            cancelOrder(inpt[1])
    else:
        cancelAll()

#****************************** PANIC COMMAND *********************************#
def handlePanic(inpt):
    print("Panic at {0}".format(datetime.datetime.now()))
    if len(inpt) == 1:
        cancelAll()
        for pos in api.list_positions():
            if pos.side == "long":
                market_sell(pos.symbol, pos.qty)
            elif pos.side == "short":
                market_buy(pos.symbol, abs(int(pos.qty)))
    else:
        if inpt[1] in ["PROFIT", "P"]:
            cancelAll()
            if len(inpt) > 2:
                profit_cents = float(inpt[2]) / 100
            else:
                profit_cents = 0.01
            print(profit_cents)
            for pos in api.list_positions():
                if pos.side == "long":
                    limit_sell(pos.symbol, float(pos.avg_entry_price) + profit_cents, pos.qty)
                elif pos.side == "short":
                    limit_buy(pos.symbol, float(pos.avg_entry_price) - profit_cents, abs(int(pos.qty)))
        else:
            ticker = inpt[1]
            cancelTicker(ticker)
            for pos in api.list_positions():
                if pos.symbol == ticker:
                    if pos.side == "long":
                        market_sell(pos.symbol, pos.qty)
                    elif pos.side == "short":
                        market_buy(pos.symbol, abs(int(pos.qty)))

#****************************** UPDATE COMMAND ********************************#
def handleUpdate(inpt):
    global updateProcess
    if len(inpt) > 1:
        if inpt[1].upper() == "ON":
            if updateProcess is not None:
                print("Update process is already on\n")
            else:
                updateProcess = Process(target=updateOrders)
                updateProcess.daemon=True
                updateProcess.start()
        elif inpt[1].upper() == "OFF":
            if updateProcess is None:
                print("Update process is already off\n")
            else:
                updateProcess.terminate()
                updateProcess = None
    else:
        print("Invalid command. Usage: update (on/off)\n")

#****************************** ORDERS COMAND *********************************#
def handleOrders():
    for x in api.list_orders():
        o = x.__dict__["_raw"]
        print("{0:5} {1:8} {2:5} {3:5} @ {4:4.2f} {5}".format(o["symbol"],
              o["order_type"], o["side"], o["qty"], float(o["limit_price"]), o["id"]))

#****************************** POSITIONS COMMAND *****************************#
def handlePositions():
    positions = api.list_positions()
    if len(positions) == 0:
        print("No Positions to Show")
    else:
        cost_basis = 0.0
        p_l = 0.0
        print("{0:<5} {1:<5} {2:<10} {3:<10} {4:<10} {5:<8}".format("TICK", "QTY", "AVG-PRICE", "CUR-PRICE", "COST BASIS", "P/L"))
        for pos in positions:
            print("{0:<5} {1:<5} {2:<10.2f} {3:<10.2f} {4:<10.2f} {5:<8.2f}".format(pos.symbol, pos.qty,
                  float(pos.avg_entry_price), float(pos.current_price), float(pos.cost_basis), float(pos.unrealized_pl)))
            cost_basis = cost_basis + float(pos.cost_basis)
            p_l = p_l + float(pos.unrealized_pl)
        print("{0:<33} {1:<10.2f} {2:<8.2f}".format("CUMULATIVE", cost_basis, p_l))

#****************************** ASSET COMMAND *********************************#
def handleAsset(inpt):
    print(api.get_asset(inpt[1]))

#****************************** HANDLE INPUT **********************************#
def handleInput(inpt):
    try:
        cmd = inpt[0]

        if cmd in ["BUY", "B"]:
            handleBuy(inpt)

        elif cmd in ["SELL", "S"]:
            handleSell(inpt)

        elif cmd in ["AUTO", "A"]:
            handleAuto(inpt)

        elif cmd in ["QUICK", "K"]:
            handleQuick(inpt)

        elif cmd in ["PRESET", "PRESET-MODE", "PM"]:
            handlePreset()

        elif cmd in ["CANCEL", "C"]:
            handleCancel(inpt)

        elif cmd in ["PANIC", "!"]:
            handlePanic(inpt)

        elif cmd in ["UPDATE", "U"]:
            handleUpdate(inpt)

        elif cmd in ["ORDERS", "O"]:
        	handleOrders()

        elif cmd in ["POSITIONS", "P"]:
            handlePositions()

        elif cmd in ["HELP", "H"]:
            help()

        elif cmd in ["ACCOUNT", "ACC"]:
        	handleAccount(inpt)

        elif cmd in ["ASSET", "ASS"]:
            handleAsset(inpt)

        elif cmd not in ["QUIT", "Q"]:
            print("invalid command\n")

    except ValueError as ve:
        print("Value Error, make sure all number arguments can be parsed")
        logger.error("Exception Occured")
    except IndexError as ie:
        print("Index Error, make sure enough arguments are provided")
        logger.error("Exception Occured")
    except Exception as e:
        logger.error("Exception Occured: ", e)

#****************************** MAIN ******************************************#
def main():
    inpt = ""
    while len(inpt) < 1:
        inpt = input(">> ").strip().upper().split()
    if len(inpt) >= 1:
        while inpt[0] not in ["QUIT", "Q"]:
            handleInput(inpt)
            inpt = ""
            while len(inpt) < 1:
                inpt = input(">> ").strip().upper().split()

    print("\nThank you for using TickerTrade\n")
    return 0

#****************************** SCRIPT SUPPORT ********************************#
if __name__ == "__main__":
    # execute only if run as a script
    exit(main())
