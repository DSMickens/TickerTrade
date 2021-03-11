import alpaca_trade_api as ata
import yfinance as yf
import os
import datetime
import time
sys.path.append('/Users/Danny/git/Ticker-Projects')
import TPasswords
sys.path.append('/Users/Danny/git/Ticker-Projects/TickerTrader')
import TickerTrader as TT


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
buying_power = int(float(account.daytrading_buying_power))
individual_buying_power = buying_power / 8.5
#uptrend = None
#lin_reg_bars = 5
#sl_percent = .0025
#tp_percent = .0025
#ticker_bounds = {}
staged_db_rows = {}
positions = []
orders = {}

##
# USING yf stock.history
# to get accurate data for minutes 10 through 12 you must start with minute 8
# and end with minute 12, it will give you minutes 9, 10, 11, and 12 but minute
# 9 will have no volume. Ignore the first returned bar
##

def is_green(bar):
    return bar[0] <= bar[3]

def update_positions_orders():
    global positions
    global orders

    old_positions = positions
    old_orders = [i for i in orders.keys()]

    #list of tickers in which a position is held
    positions = []
    for p in api.list_positions():
        positions.append(p.symbol)
    #dictionary of orders. ticker -> order side ("AAPL" -> "buy")
    orders = {}
    for o in api.list_orders():
        order = o.__dict__["_raw"]
        orders[order["symbol"]] = order["side"]

    #returns change in positions and change in orders
    return [i for i in old_positions + positions if i not in old_positions or i not in positions], [i for i in old_orders + list(orders.keys()) if i not in old_orders or i not in orders.keys()]

def get_linear_regression_slope(y):
    x = []
    for num in range(len(y)):
        x.append(num)
    x_bar = sum(x) / len(x)
    y_bar = sum(y) / len(y)
    n = len(x)

    numerator = sum([xi*yi for xi, yi in zip(x, y)]) - n * x_bar * y_bar
    denominator = sum([xi**2 for xi in x]) - n * x_bar**2
    if denominator != 0:
        return round( 1000 * numerator / (denominator * y[len(y) - 1]), 4)
    else:
        return 0

def get_bounds_data(bell, algo_start, tickers):
    global ticker_bounds

    for ticker in tickers:
        stock = yf.Ticker(ticker)
        history = stock.history(interval="5m", start=bell, end=algo_start).values.tolist() #open - high - low - close - volume
        extrema = []
        extrema.append(history[0][0])
        extrema.append(history[0][3])
        extrema.append(history[1][0])
        extrema.append(history[1][3])
        extrema.append(history[2][0])
        extrema.append(history[2][3])
        max_val = max(extrema)
        min_val = min(extrema)
        ticker_bounds[ticker] = (max_val, min_val)

def wait_for_algo_start_time(algo_start_time):
    while datetime.datetime.now() < algo_start_time:
        time.sleep(1)

def make_initial_bracket_orders_15():
    for ticker, bounds in ticker_bounds.items():
        current_price = api.get_last_trade(ticker).price
        stop_loss_length = round((bounds[0] - bounds[1]) * .2, 2)
        #if price is within the bounds, make orders like normal
        if current_price <= bounds[0] and current_price >= bounds[1]:
            #if price is closer to upper bound, make a long order
            if bounds[0] - current_price <= current_price - bounds[1]:
                stop_loss = round(bounds[0] - stop_loss_length, 2)
                take_profit = round(bounds[0] + 3 * stop_loss_length, 2)
                limit_price = bounds[0]
                qty = int(individual_buying_power / limit_price)
                TT.bracket_limit_buy(ticker, limit_price, qty, stop_loss, take_profit)
            #if price is closer to lower bound, make a short order
            else:
                stop_loss = round(bounds[1] + stop_loss_length, 2)
                take_profit = round(bounds[1] - 3 * stop_loss_length, 2)
                limit_price = bounds[1]
                qty = int(individual_buying_power / limit_price)
                TT.bracket_limit_sell(ticker, limit_price, qty, stop_loss, take_profit)
        #if price is outside the upper bounds, make long market bracket order
        elif current_price > bounds[0] and current_price < bounds[0] + stop_loss * 1.1:
            stop_loss = round(bounds[0] - stop_loss_length, 2)
            take_profit = round(bounds[0] + 3 * stop_loss_length, 2)
            qty = int(individual_buying_power / current_price)
            TT.bracket_market_buy(ticker, qty, stop_loss, take_profit)
        elif current_price < bounds[1] and current_price > bounds[1] - stop_loss * 1.1:
            stop_loss = round(bounds[1] + stop_loss_length, 2)
            take_profit = round(bounds[1] - 3 * stop_loss_length, 2)
            qty = int(individual_buying_power / current_price)
            TT.bracket_market_sell(ticker, qty, stop_loss, take_profit)

def make_bracket_orders_15():

    update_positions_orders()

    for ticker, bounds in ticker_bounds.items():
        has_position = True if ticker in positions else False
        #if a current position is held, there is nothing to do
        current_price = api.get_last_trade(ticker).price
        if has_position or current_price > bounds[0] or current_price < bounds[1]:
            pass
        else:
            stop_loss_length = round((bounds[0] - bounds[1]) * .2, 2)
            if bounds[0] - current_price <= current_price - bounds[1]:
                if ticker not in orders:
                    stop_loss = round(bounds[0] - stop_loss_length, 2)
                    take_profit = round(bounds[0] + 3 * stop_loss_length, 2)
                    limit_price = bounds[0]
                    qty = int(individual_buying_power / limit_price)
                    TT.bracket_limit_buy(ticker, limit_price, qty, stop_loss, take_profit)
            else:
                if ticker not in orders:
                    stop_loss = round(bounds[1] + stop_loss_length, 2)
                    take_profit = round(bounds[1] - 3 * stop_loss_length, 2)
                    limit_price = bounds[1]
                    qty = int(individual_buying_power / limit_price)
                    TT.bracket_limit_sell(ticker, limit_price, qty, stop_loss, take_profit)

def run_15_algo():
    """
    POTENTIAL PROBLEMS:
        currently orders are placed with a limit price at the bounds, if it's 9:46 or
        later because the algorithm was started or stopped and
        the price is higher than the bound and keeps going up, the order will not be
        filled, but may be filled when the price falls down again, buying during a downtrend
        Should be fixable with a limit price range that is independent of where the SL/TP
        is, or clean up function to delete orders that have been hanging.
    """

    """
    IMPROVEMENT IDEAS:
          currently the stop loss and take profit and bounds are all based off of the extrema
          for the first 3 5m bars. If there is very little range in the opening 15 minutes at
          the open and close of each 5m bar then you could end up with a very small boundary
          range, and therefore a very small stop loss. This could lead to a lot of buys and sells
          as a small change in the price could cover a lot of the boundary range and trigger
          stop losses and new bracket orders.
          There should be a fairly easy solution, where the list of tickers is longer in order
          to have backup stocks just in case some of the stocks don't work out because the range
          is too small. The first 8 stocks in the list that have an acceptable range are used
          for the rest of the day.
          A FURTHER SIGNIFICANT IMPROVEMENT IDEA IS TO ENABLE A WAY TO TRACK THE PERFORMANCE OF
          INDIVIDUAL STOCKS OVER TIME AND PUT THOSE STOCKS AT THE FRONT OF THE LIST OF TICKERS
          TO GIVE THEM THE FIRST CHANCE OF BEING CHOSEN THE NEXT DAY. SELECT INITIAL ORDER OF
          LIST BASED ON PERFORMANCE WHEN BACKTESTING FOR LAST 30 DAYS.
    """
    tickers = ["AAPL","T", "V", "WMT", "FB", "JNJ", "MSFT", "CSCO"]
    interval = "5 m"
    today = datetime.datetime.today()
    bell = datetime.datetime(today.year, today.month, today.day, 9, 30)
    algo_start_time = datetime.datetime(today.year, today.month, today.day, 9, 45)
    algo_end_time = datetime.datetime(today.year, today.month, today.day, 14, 30)
    one_minute = datetime.timedelta(minutes=1)
    #wait for 9:45 am before you can get 15 min data
    wait_for_algo_start_time(algo_start_time)

    #once it's 9:45, get bar data for tickers
    get_bounds_data(bell, algo_start_time, tickers)
    #make the initial bracket orders based on which side of the bounds the current price
    #is closest to, if the time is just after the algo start time
    if datetime.datetime.now() > algo_start_time and datetime.datetime.now() < algo_start_time + one_minute:
        make_initial_bracket_orders_15()

    while(datetime.datetime.now() < algo_end_time):
        current_minute = datetime.datetime.now().replace(second = 0, microsecond = 0)
        print(current_minute)
        next_minute = current_minute + one_minute
        while datetime.datetime.now() < next_minute:
            time.sleep(1)
        make_bracket_orders_15()

def check_engulfing_3(bars):
    open = 0
    high = 1
    low = 2
    close = 3
    volume = 4
    top = 5
    bottom = 6
    body = 7

    bar1 = bars[0][0:5]
    bar2 = bars[1][0:5]
    bar3 = bars[2][0:5]

    bar1_top = bar1[close] if is_green(bar1) else bar1[open]
    bar1_bottom = bar1[open] if is_green(bar1) else bar1[close]
    bar1_body = round(bar1_top - bar1_bottom, 2)
    bar1.append(bar1_top)
    bar1.append(bar1_bottom)
    if bar1_body == 0: bar1_body = 0.01
    bar1.append(bar1_body)


    bar2_top = bar2[close] if is_green(bar2) else bar2[open]
    bar2_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar2_body = round(bar2_top - bar2_bottom, 2)
    bar2.append(bar2_top)
    bar2.append(bar2_bottom)
    if bar2_body == 0: bar2_body = 0.01
    bar2.append(bar2_body)


    bar3_top = bar3[close] if is_green(bar3) else bar3[open]
    bar3_bottom = bar3[open] if is_green(bar3) else bar3[close]
    bar3_body = round(bar3_top - bar3_bottom, 2)
    bar3.append(bar3_top)
    bar3.append(bar3_bottom)
    if bar3_body == 0: bar3_body = 0.01
    bar3.append(bar3_body)



    if bar1[body] / bar1[close] < .0015:
        return False, None
    if is_green(bar1):
        if (bar2[top] - bar3[bottom]) / bar3[close] < .002:
            return False, None
    else:
        if (bar3[top] - bar2[bottom]) / bar3[close] < .002:
            return False , None

    if is_green(bar1) == is_green(bar2) or is_green(bar1) == is_green(bar3):
        return False, None
    if is_green(bar1) and not is_green(bar2):
        if (bar2[top] >= bar1[top] - .01 and (bar2[bottom] < bar1[bottom] or bar3[bottom] < bar1[bottom])
            and bar2[top] - bar3[bottom] >= 1.15 * bar1[body]):
            return True, round((bar2[top] - bar3[bottom]) / bar1[body], 4)
        else:
            return False, None
    if not is_green(bar1) and is_green(bar2):
        if (bar2[bottom] <= bar1[bottom] + .01 and (bar2[top] > bar1[top] or bar3[top] > bar1[top])
            and bar3[top] - bar2[bottom] >= 1.15 * bar1[body]):
            return True, round((bar3[top] - bar2[bottom]) / bar1[body], 4)
        else:
            return False, None

def check_engulfing_2(bars):
    open = 0
    high = 1
    low = 2
    close = 3
    volume = 4
    top = 5
    bottom = 6
    body = 7

    bar1 = bars[0][0:5]
    bar2 = bars[1][0:5]

    bar1_top = bar1[close] if is_green(bar1) else bar1[open]
    bar1_bottom = bar1[open] if is_green(bar1) else bar1[close]
    bar1_body = round(bar1_top - bar1_bottom, 2)
    bar1.append(bar1_top)
    bar1.append(bar1_bottom)
    if bar1_body == 0: bar1_body = 0.01
    bar1.append(bar1_body)


    bar2_top = bar2[close] if is_green(bar2) else bar2[open]
    bar2_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar2_body = round(bar2_top - bar2_bottom, 2)
    bar2.append(bar2_top)
    bar2.append(bar2_bottom)
    if bar2_body == 0: bar2_body = 0.01
    bar2.append(bar2_body)



    if bar1[body] / bar1[close] < 0.0015:
        return False, None
    if bar2[body] / bar2[close] < 0.002:
        return False, None

    if is_green(bar1) == is_green(bar2):
        return False, None
    if is_green(bar1) and not is_green(bar2):
        if (bar2[top] >= bar1[top] - .01 and bar2[bottom] < bar1[bottom]
            and bar2[body] >= 1.15 * bar1[body]):
            return True, round(bar2[body] / bar1[body], 4)
        else:
            return False, None
    if not is_green(bar1) and is_green(bar2):
        if (bar2[bottom] <= bar1[bottom] + .01 and bar2[top] > bar1[top]
            and bar2[body] >= 1.15 * bar1[body]):
            return True, round(bar2[body] / bar1[body], 4)
        else:
            return False, None

def create_row(ticker, long, bars, percent, sl, dia, spy, qqq):
    global staged_db_rows

    db_row = [None] * 16

    db_row[1] = long                                            #long
    db_row[2] = datetime.datetime.now().replace(microsecond=0)  #open_time
    db_row[6] = bars                                            #engulfing_bars
    db_row[7] = percent                                         #engulfing_percentage
    db_row[8] = 0.75                                            #take_profit
    db_row[9] = sl                                              #stop_loss
    db_row[12] = dia                                            #dia_at_open
    db_row[13] = spy                                            #spy_at_open
    db_row[14] = qqq                                            #qqq_at_open

    staged_db_rows[ticker] = db_row
    print("Created row for {0}: ".format(ticker))
    print("\t{0}".format(staged_db_rows[ticker]))

def run_engulfing_algo():
    global staged_db_rows

    tickers = ["AAPL","T", "V", "WMT", "FB", "JNJ", "MSFT", "CSCO"]
    interval = "5m"
    today = datetime.datetime.today()
    algo_start_time = datetime.datetime(today.year, today.month, today.day, 9, 50)
    algo_end_time = datetime.datetime(today.year, today.month, today.day, 15, 45)
    one_minute = datetime.timedelta(minutes=1)
    five_minutes = datetime.timedelta(minutes=5)
    #wait for 9:45 am before you can get 15 min data
    wait_for_algo_start_time(algo_start_time)
    TT.handlePanic(["!"])
    while(datetime.datetime.now() < algo_end_time):
        current_minute = datetime.datetime.now().replace(second = 0, microsecond = 0)
        # wait for next 5 minute marker
        while current_minute.minute % 5 != 0:
            time.sleep(1)
            current_minute = datetime.datetime.now().replace(second = 0, microsecond = 0)
        closed_positions = update_positions_orders()
        print("Reached 5 minute time: {0}".format(current_minute))

        for ticker in tickers:
            print("checking {0}".format(ticker))
            stock = yf.Ticker(ticker)
            start = current_minute - (five_minutes * 3)
            end = current_minute
            print("Start: {0}".format(start))
            print("End: {0}".format(end))
            history = stock.history(interval=interval, start=start, end=end).values.tolist()
            if len(history) == 4:
                history = history[:3]
            print("Bar 1:\n\tO:{0}\n\tH:{1}\n\tL:{2}\n\tC:{3}".format(history[0][0], history[0][1], history[0][2], history[0][3]))
            print("Bar 2:\n\tO:{0}\n\tH:{1}\n\tL:{2}\n\tC:{3}".format(history[1][0], history[1][1], history[1][2], history[1][3]))
            print("Bar 3:\n\tO:{0}\n\tH:{1}\n\tL:{2}\n\tC:{3}".format(history[2][0], history[2][1], history[2][2], history[2][3]))

            two_bar_engulfing, engulfing_percentage_2 = check_engulfing_2(history[1:])
            three_bar_engulfing, engulfing_percentage_3 = check_engulfing_3(history)

            if two_bar_engulfing:
                if is_green(history[1]):
                    print("Bearish 2 bar engulfing detected")
                else:
                    print("Bullish 2 bar engulfing detected")
                if ticker not in positions and ticker not in orders:
                    price = history[2][3]
                    qty = int(individual_buying_power / price - 1)
                    stop_loss = history[1][3]
                    stop_loss_percent = round(abs(price - stop_loss) / price, 4)
                    if is_green(history[1]):
                        take_profit = price * 0.9925
                        #print(datetime.datetime.now(), "sell", ticker, history[-1][3], qty, stop_loss, take_profit)
                        TT.bracket_limit_sell(ticker, price, qty, stop_loss, take_profit)
                    else:
                        take_profit = price * 1.0075
                        #print(datetime.datetime.now(), "buy", ticker, history[-1][3], qty, stop_loss, history[-1][3], take_profit)
                        TT.bracket_limit_buy(ticker, price, qty, stop_loss, take_profit)
                elif ((is_green(history[1]) and int(api.get_position(ticker).qty) > 0)
                       or (not is_green(history[1]) and int(api.get_position(ticker).qty) < 0)):
                    TT.handlePanic(["!", "{0}".format(ticker)])

            elif three_bar_engulfing:
                if is_green(history[0]):
                    print("Bearish 3 bar engulfing detected")
                else:
                    print("Bullish 3 bar engulfing detected")

                if ticker not in positions and ticker not in orders:
                    price = history[2][3]
                    qty = int((individual_buying_power / price) - 1)
                    stop_loss = history[0][3]
                    stop_loss_percent = round(abs(price - stop_loss) / price, 4)
                    if is_green(history[0]):
                        take_profit = price * 0.9925
                        #print(datetime.datetime.now(), "sell", ticker, history[-1][3], qty, stop_loss, take_profit)
                        TT.bracket_limit_sell(ticker, price, qty, stop_loss, take_profit)
                    else:
                        take_profit = price * 1.075
                        #print(datetime.datetime.now(), "buy", ticker, history[-1][3], qty, stop_loss, take_profit)
                        TT.bracket_limit_buy(ticker, history[2][3], qty, stop_loss, take_profit)
                elif ((is_green(history[-1]) and int(api.get_position(ticker).qty) < 0)
                       or (not is_green(history[2]) and int(api.get_position(ticker).qty) > 0)):
                    TT.handlePanic(["!", "{0}".format(ticker)])

        while current_minute.minute % 5 == 0:
            time.sleep(1)
            current_minute = datetime.datetime.now().replace(second = 0, microsecond = 0)
        print("Finished 5 minute time: {0}".format(current_minute))
        update_positions_orders()
        for ticker in orders:
            if ticker not in positions:
                TT.handlePanic(["!", "{0}".format(ticker)])

def main():
    #run_15_algo()
    try:
        run_engulfing_algo()
    except:
        print("Algorithm Failed Unexpectedly.")
    finally:
        TT.handlePanic(["!"])

if __name__ == "__main__":
    # execute only if run as a script
    exit(main())
