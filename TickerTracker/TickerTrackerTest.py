import alpaca_trade_api as ata
import yfinance as yf
import pandas as pd
import os
import datetime
import time
from matplotlib import pyplot as plt
plt.ion()
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
individual_bp = buying_power / 8.5
uptrend = None
lin_reg_bars = 5
total_buy = 0
total_sell = 0
buy_count = 0
sell_count = 0
positions = {}     #key: ticker - value: (quantity, price)
p_l = {}           #key: ticker - value: daily p/l
orders = {}        #key: ticker - value: (stop_loss, take_profit)
sl_percent = .0025
tp_percent = .0025
testing_p_l = {}   #key: ticker - value: total p/l
fees = 0

##
# USING yf stock.history
# to get accurate data for minutes 10 through 12 you must start with minute 8
# and end with minute 12, it will give you minutes 9, 10, 11, and 12 but minute
# 9 will have no volume. Ignore the first returned bar
##

def is_green(bar):
    return bar[0] <= bar[3]

def reset_globals():
    global total_buy
    global total_sell
    global buy_count
    global sell_count
    global positions
    global p_l
    global orders

    total_buy = 0
    total_sell = 0
    buy_count = 0
    sell_count = 0
    positions = {}
    p_l = {}
    orders = {}

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

def make_plot(start, end, interval, ticker, bars):
    stk = yf.Ticker(ticker)
    his = stk.history(interval=interval, start=start, end=end).values.tolist() #open - high - low - close - volume
    x = []
    y = []
    y_prime = []
    count = 0
    for bar in his:
        x.append(count)
        count = count + 1
        y.append(bar[3])
    plt.figure(2)
    plt.clf()
    fig2,axs2 = plt.subplots(2)
    axs2[0].plot(x[:len(x)-(bars + 1)],y[(bars + 1):])
    for n in range(count-(bars + 1)):
        y_prime.append(get_linear_regression_slope(y[(bars - 3) + n: (2 * bars - 3) + n]))
    axs2[1].plot(x[:len(x)-(bars + 1)],y_prime)
    plt.show()

def cover_position_test(ticker, current_price, time = None):
    global positions
    global p_l
    global total_buy
    global buy_count
    global total_sell
    global sell_count

    if ticker in positions:
        shares = positions[ticker][0]
        if shares > 0:
            total_sell = total_sell + (current_price * shares)
            sell_count = sell_count + shares
            print("{0} S {1} {2:.4f}".format(ticker, shares, current_price))
            #print("{0} SELL {1} of {2} at {3}".format(time, shares, ticker, current_price))
        elif shares < 0:
            total_buy = total_buy + (current_price * -1 * shares)
            buy_count = buy_count + (-1 * shares)
            print("{0} B {1} {2:.4f}".format(ticker, -1 * shares, current_price))
            #print("{0} BUY {1} of {2} at {3}".format(time, -1 * shares, ticker, current_price))
        pl = shares * (current_price - positions[ticker][1])

        if ticker not in p_l:
            p_l[ticker] = 0
        print("Profit/Loss: {0:.2f}".format(pl))
        p_l[ticker] = p_l[ticker] + pl
        print("Running P/L: {0:.2f}".format(p_l[ticker]))
        del positions[ticker]

def bracket_buy_position_test(ticker, current_price, qty, stop_loss = None, take_profit = None, time = None):
    global positions
    global total_buy
    global buy_count
    global orders

    total_buy = total_buy + (current_price * qty)
    buy_count = buy_count + qty
    positions[ticker] = (qty, current_price)
    #print("{0} BUY {1} of {2} at {3}".format(time, qty, ticker, current_price))
    print("{0} B {1} {2:.4f}".format(ticker, qty, current_price))
    #bracket order at .25% below AND above
    if stop_loss is None:
        stop_loss = round(current_price * (1 - sl_percent), 2)
    if take_profit is None:
        take_profit = round(current_price * (1 + tp_percent), 2)
    print("\tStop Loss: ", stop_loss)
    print("\tTake Profit: ", take_profit)
    orders[ticker] = (stop_loss, take_profit)

def bracket_sell_position_test(ticker, current_price, qty, stop_loss = None, take_profit = None, time = None):
    global positions
    global total_sell
    global sell_count
    global orders

    total_sell = total_sell + (current_price * qty)
    sell_count = sell_count + qty
    positions[ticker] = (-1 * qty, current_price)
    #print("{0} SELL {1} of {2} at {3}".format(time, qty, ticker, current_price))
    print("{0} S {1} {2:.4f}".format(ticker, qty, current_price))
    #bracket order at .25% below AND above
    if stop_loss is None:
        stop_loss = round(current_price * (1 + sl_percent), 2)
    if take_profit is None:
        take_profit = round(current_price * (1 - tp_percent), 2)
    print("\tStop Loss: ",stop_loss)
    print("\tTake Profit: ",take_profit)
    orders[ticker] = (stop_loss, take_profit)

def check_orders(ticker, bar, check_time = None):
    if ticker not in orders:
        return
    high = bar[1]
    low = bar[2]
    stop_loss = orders[ticker][0]
    take_profit = orders[ticker][1]
    #long position
    if ticker in positions and positions[ticker][0] > 0:
        if ticker in orders:
            if low <= stop_loss:
                #print("Long Position stop loss triggered")
                cover_position_test(ticker, stop_loss, check_time)
                del orders[ticker]
            elif high >= take_profit:
                #print("Long Position take profit triggered")
                cover_position_test(ticker, take_profit, check_time)
                del orders[ticker]
    #short position
    elif ticker in positions and positions[ticker][0] < 0:
        if ticker in orders:
            if high >= stop_loss:
                #print("Short Position stop loss triggered")
                cover_position_test(ticker, stop_loss, check_time)
                del orders[ticker]
            elif low <= take_profit:
                #print("Short Position take profit triggered")
                cover_position_test(ticker, take_profit, check_time)
                del orders[ticker]

def check_flags_2_bars(bars, slope):
    open = 0
    high = 1
    low = 2
    close = 3
    volume = 4
    top = 5
    bottom = 6
    body = 7
    upper_shadow = 8
    lower_shadow = 9
    green = None
    volume_flag = False
    engulfing_flag = False
    shadow_flag = False

    bar1 = bars[-2][0:5]
    bar2 = bars[-1][0:5]

    bar1_top = bar1[close] if is_green(bar1) else bar1[open]
    bar1_bottom = bar1[open] if is_green(bar1) else bar1[close]
    bar1_body = round(bar1_top - bar1_bottom, 2)
    bar1_upper_shadow = round(bar1[high] - bar1_top, 2)
    bar1_lower_shadow = round(bar1_bottom - bar1[low], 2)
    bar1.append(bar1_top)
    bar1.append(bar1_bottom)
    bar1.append(bar1_body)
    bar1.append(bar1_upper_shadow)
    bar1.append(bar1_lower_shadow)

    bar2_top = bar2[close] if is_green(bar2) else bar2[open]
    bar2_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar2_body = round(bar2_top - bar2_bottom, 2)
    bar2_upper_shadow = round(bar2[high] - bar2_top, 2)
    bar2_lower_shadow = round(bar2_bottom - bar2[low], 2)
    bar2.append(bar2_top)
    bar2.append(bar2_bottom)
    bar2.append(bar2_body)
    bar2.append(bar2_upper_shadow)
    bar2.append(bar2_lower_shadow)

    #check for volume and shadow flags and figure out how to return them
    #once they're returned, what do I do with them?

    # volume flag
    if bar2[volume] > 1.5 * bar1[volume]:
        volume_flag = True

    # uptrend - shadow flag and engulfing flag
    if uptrend is not None and uptrend is True:
        if (bar2[high] / bar2[top]) >= 1.005:
            shadow_flag = True
    # downtrend - shadow flag and engulfing flag
    elif uptrend is not None and uptrend is False:
        if (bar2[low] / bar2[bottom]) <= 0.995:
            shadow_flag = True

    return volume_flag, shadow_flag

def check_reversal_3_bars(bars, slope):
    open = 0
    high = 1
    low = 2
    close = 3
    volume = 4
    top = 5
    bottom = 6
    body = 7
    upper_shadow = 8
    lower_shadow = 9
    green = None
    volume_flag = False
    engulfing_flag = False
    shadow_flag = False

    bar1 = bars[0][0:5]
    bar2 = bars[1][0:5]
    bar3 = bars[2][0:5]

    bar1_top = bar1[close] if is_green(bar1) else bar1[open]
    bar1_bottom = bar1[open] if is_green(bar1) else bar1[close]
    bar1_body = round(bar1_top - bar1_bottom, 2)
    bar1_upper_shadow = round(bar1[high] - bar1_top, 2)
    bar1_lower_shadow = round(bar1_bottom - bar1[low], 2)
    bar1.append(bar1_top)
    bar1.append(bar1_bottom)
    bar1.append(bar1_body)
    bar1.append(bar1_upper_shadow)
    bar1.append(bar1_lower_shadow)

    bar2_top = bar2[close] if is_green(bar2) else bar2[open]
    bar2_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar2_body = round(bar2_top - bar2_bottom, 2)
    bar2_upper_shadow = round(bar2[high] - bar2_top, 2)
    bar2_lower_shadow = round(bar2_bottom - bar2[low], 2)
    bar2.append(bar2_top)
    bar2.append(bar2_bottom)
    bar2.append(bar2_body)
    bar2.append(bar2_upper_shadow)
    bar2.append(bar2_lower_shadow)

    bar3_top = bar2[close] if is_green(bar2) else bar2[open]
    bar3_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar3_body = round(bar2_top - bar2_bottom, 2)
    bar3_upper_shadow = round(bar2[high] - bar2_top, 2)
    bar3_lower_shadow = round(bar2_bottom - bar2[low], 2)
    bar3.append(bar2_top)
    bar3.append(bar2_bottom)
    bar3.append(bar2_body)
    bar3.append(bar2_upper_shadow)
    bar3.append(bar2_lower_shadow)

def check_reversal_trends_test(ticker, check_time, time_interval, history = None):
    global uptrend
    global total_buy
    global buy_count
    global total_sell
    global sell_count
    global positions

    ## Time/Interval Calculations - used in Bars

    split_interval = time_interval.split()
    num = int(split_interval[0])
    interval = split_interval[1]
    day_interval = num if interval == "d" else 0
    hour_interval = num if interval == "h" else 0
    min_interval = num if interval == "m" else 0
    if day_interval == 0 and hour_interval == 0 and min_interval == 0:
        print("Invalid Time Interval: ", time_interval)
        return
    decrement = datetime.timedelta(days=day_interval, hours=hour_interval, minutes=min_interval)
    ## Bars
    if history is None:
        stock = yf.Ticker(ticker)
        history = stock.history(interval=time_interval.replace(" ", ""), start=check_time - lin_reg_bars * decrement, end=check_time).values.tolist() #open - high - low - close - volume

    if ticker in orders:
        check_orders(ticker, history[lin_reg_bars - 1], check_time)


    closing_prices = []
    for x in range(lin_reg_bars):
        closing_prices.append(history[x][3])
    #for bar in history:
    #   closing_prices.append(bar[3])
    slope = get_linear_regression_slope(closing_prices)

    ## Check Flags
    volume_flag, shadow_flag = check_flags_2_bars(history[len(history) - 2:len(history)], slope)
    if volume_flag and shadow_flag:
        print(check_time)

    cl_price = closing_prices[lin_reg_bars - 1]
    if uptrend is not None:
        shares = int(buying_power / (8.0 * cl_price)) - 1
        if slope > 0:
            if not uptrend:
                #print("BUY AT {0}: {1}".format(check_time - decrement, closing_prices[lin_reg_bars - 1]))
                if ticker in positions:
                    pass#cover_position_test(ticker, cl_price, check_time)
                else:
                    pass#positions[ticker] = (shares, cl_price)
                pass#buy_position_test(ticker, cl_price, shares, check_time)
            uptrend = True
        elif slope < 0:
            if uptrend:
                #print("SELL AT {0}: {1}".format(check_time - decrement, closing_prices[lin_reg_bars - 1]))
                if ticker in positions:
                    pass#cover_position_test(ticker, cl_price, check_time)
                else:
                    pass#positions[ticker] = (shares, cl_price)
                pass#sell_position_test(ticker, cl_price, shares, check_time)
            uptrend = False
    else:
        uptrend = True if slope > 0 else False
    return 0

def check_reversal_trends(ticker, check_time, time_interval, history = None):
    global uptrend
    global total_buy
    global buy_count
    global total_sell
    global sell_count

    ## Time/Interval Calculations - used in Bars

    split_interval = time_interval.split()
    num = int(split_interval[0])
    interval = split_interval[1]
    day_interval = num if interval == "d" else 0
    hour_interval = num if interval == "h" else 0
    min_interval = num if interval == "m" else 0
    if day_interval == 0 and hour_interval == 0 and min_interval == 0:
        print("Invalid Time Interval: ", time_interval)
        return
    decrement = datetime.timedelta(days=day_interval, hours=hour_interval, minutes=min_interval)
    ## Bars
    if history is None:
        stock = yf.Ticker(ticker)
        history = stock.history(interval=time_interval.replace(" ", ""), start=check_time - lin_reg_bars * decrement, end=check_time).values.tolist() #open - high - low - close - volume

    closing_prices = []
    for x in range(lin_reg_bars):
        closing_prices.append(history[x][3])
    #for bar in history:
    #   closing_prices.append(bar[3])
    slope = get_linear_regression_slope(closing_prices)
    if uptrend is not None:
        if slope > 0:
            if not uptrend:
                #print("BUY AT {0}: {1}".format(check_time - decrement, closing_prices[lin_reg_bars - 1]))
                total_buy = total_buy + closing_prices[lin_reg_bars - 1]
                buy_count = buy_count + 1
            uptrend = True
        elif slope < 0:
            if uptrend:
                #print("SELL AT {0}: {1}".format(check_time - decrement, closing_prices[lin_reg_bars - 1]))
                total_sell = total_sell + closing_prices[lin_reg_bars - 1]
                sell_count = sell_count + 1
            uptrend = False
    else:
        uptrend = True if slope > 0 else False

def check_reversal(ticker, end, time_interval):
    global uptrend

    ## Locals

    open = 0
    high = 1
    low = 2
    close = 3
    volume = 4
    top = 5
    bottom = 6
    body = 7
    upper_shadow = 8
    lower_shadow = 9
    green = None
    volume_flag = False
    engulfing_flag = False
    shadow_flag = False

    ## Time/Interval Calculations - used in Bars

    split_interval = time_interval.split()
    num = int(split_interval[0])
    interval = split_interval[1]
    day_interval = num if interval == "d" else 0
    hour_interval = num if interval == "h" else 0
    min_interval = num if interval == "m" else 0
    if day_interval == 0 and hour_interval == 0 and min_interval == 0:
        print("Invalid Time Interval: ", time_interval)
        return
    decrement = datetime.timedelta(days=day_interval, hours=hour_interval, minutes=min_interval)

    ## Bars

    stock = yf.Ticker(ticker)
    history = stock.history(interval=time_interval.replace(" ", ""), start=end - (lin_reg_bars + 1) * decrement, end=end).values.tolist() #open - high - low - close - volume

    closing_prices = []
    for bar in history:
        closing_prices.append(bar[3])
    slope = get_linear_regression_slope(closing_prices)
    if uptrend is not None:
        if slope > 0:
            if not uptrend:
                print("BUY AT {0}: {1}".format(end, ))
            uptrend = True
        elif slope < 0:
            if uptrend:
                print("SELL AT ", end)
            uptrend = False
    else:
        uptrend = True if slope > 0 else False
    """
    bar1 = history[5][0:5]
    bar2 = history[6][0:5]
    bar3 = history[7][0:5]


    ## Bar Data

    bar1_top = bar1[close] if is_green(bar1) else bar1[open]
    bar1_bottom = bar1[open] if is_green(bar1) else bar1[close]
    bar1_body = round(bar1_top - bar1_bottom, 2)
    bar1_upper_shadow = round(bar1[high] - bar1_top, 2)
    bar1_lower_shadow = round(bar1_bottom - bar1[low], 2)
    bar1.append(bar1_top)
    bar1.append(bar1_bottom)
    bar1.append(bar1_body)
    bar1.append(bar1_upper_shadow)
    bar1.append(bar1_lower_shadow)

    bar2_top = bar2[close] if is_green(bar2) else bar2[open]
    bar2_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar2_body = round(bar2_top - bar2_bottom, 2)
    bar2_upper_shadow = round(bar2[high] - bar2_top, 2)
    bar2_lower_shadow = round(bar2_bottom - bar2[low], 2)
    bar2.append(bar2_top)
    bar2.append(bar2_bottom)
    bar2.append(bar2_body)
    bar2.append(bar2_upper_shadow)
    bar2.append(bar2_lower_shadow)

    bar3_top = bar3[close] if is_green(bar3) else bar3[open]
    bar3_bottom = bar3[open] if is_green(bar3) else bar3[close]
    bar3_body = round(bar3_top - bar3_bottom, 2)
    bar3_upper_shadow = round(bar3[high] - bar3_top, 2)
    bar3_lower_shadow = round(bar3_bottom - bar3[low], 2)
    bar3.append(bar3_top)
    bar3.append(bar3_bottom)
    bar3.append(bar3_body)
    bar3.append(bar3_upper_shadow)
    bar3.append(bar3_lower_shadow)


    ## Volume Confidence

    # outer bar volume is the volume of the largest bar on the side of bar 2
    if bar1[volume] > bar3[volume]:
        outer_bar_volume = bar1[volume]
    else:
        outer_bar_volume = bar3[volume]

    # .75-       of side bars = 0
    # .75 to 1   of side bars = 0.1
    # 1   to 1.1 of side bars = 0.15
    # 1.1 to 1.2 of side bars = 0.2
    # 1.2 to 1.3 of side bars = 0.25
    # 1.3 to 1.4 of side bars = 0.3
    # 1.4+       of side bars = 0.4
    # numbers subject to change
    if bar2[volume] / outer_bar_volume < 0.75:
        volume_confidence = 0
    elif bar2[volume] / outer_bar_volume < 1:
        volume_confidence = 0.1
    elif bar2[volume] / outer_bar_volume < 1.1:
        volume_confidence = 0.15
    elif bar2[volume] / outer_bar_volume < 1.2:
        volume_confidence = 0.2
    elif bar2[volume] / outer_bar_volume < 1.3:
        volume_confidence = 0.25
    elif bar2[volume] / outer_bar_volume < 1.4:
        volume_confidence = 0.3
    else:
        volume_confidence = 0.4

    ## Volume Flag

    if bar2[volume] > bar1[volume] + bar3[volume]:
        volume_flagged = True

    #UPTREND
    if uptrend:
        if green:

            #Color Confidence
            #color_confidence = 0.0

            upper_shadow = bar2[high] - bar2[close]
            candle_length = bar2[close] - bar2[open]
            if candle_length / bar2[open] >= .0020: #.20% and bigger candle doesn't need as much of a shadow
                candle_length = candle_length * 3 / 4 #handle this by reducing the candle length for confidence calculation
            if candle_length == 0:
                candle_length = 0.01


            #Shadow Length Confidence
            #shadow_length_confidence = min(0.40, (upper_shadow / candle_length) * 0.20)
            #shadow_length_confidence = 0.0 if shadow_length_confidence < .10 else shadow_length_confidence


            bar1_top = bar1[close] if is_green(bar1) else bar1[open]
            bar3_top = bar3[close] if is_green(bar3) else bar3[open]
            # FIX
            if bar1_top > bar2[high] or bar3_top > bar2[high]:
                return
            if bar2[close] + .01 < bar1_top or bar2[close] + .01 < bar3_top:
                extension_confidence = 0.10
            elif bar2[close] < bar1_top or bar2[close] < bar3_top:
                extension_confidence = 0.05
            else:
                extension_confidence = 0.15
            # END FIX
        else:

            #Color Confidence
            #color_confidence = 0.10

            upper_shadow = bar2[high] - bar2[open]
            candle_length = bar2[open] - bar2[close]
            if candle_length / bar2[open] >= .0020: #.20% and bigger candle doesn't need as much of a shadow
                candle_length = candle_length * 3 / 4
            if candle_length == 0:
                candle_length = 0.01


            #Shadow Length Confidence
            #shadow_length_confidence = min(0.40, (upper_shadow / candle_length) * 0.20)
            #shadow_length_confidence = 0.0 if shadow_length_confidence < .10 else shadow_length_confidence


            bar1_top = bar1[close] if is_green(bar1) else bar1[open]
            bar3_top = bar3[close] if is_green(bar3) else bar3[open]
            # FIX
            if bar1_top > bar2[high] or bar3_top > bar2[high]:
                return
            if bar1[high] <= bar2[high] and bar3[high] <= bar2[high] and bar1_top < bar2[open] and bar3_top < bar2[open]:
                extension_confidence = 0.15
            #elif bar2[low] >=
            # END FIX
    #DOWNTREND
    else:
        if green:

            #Color Confidence
            #color_confidence = .10

            lower_shadow = bar2[open] - bar2[low]
            candle_length = bar2[close] - bar2[open]
            if candle_length / bar2[open] >= .0020: #.20% and bigger candle doesn't need as much of a shadow
                candle_length = candle_length * 3 / 4
            if candle_length == 0:
                candle_length = 0.01


            #Shadow Length Confidence
            #shadow_length_confidence = min(0.40, (lower_shadow / candle_length) * 0.20)
            #shadow_length_confidence = 0.0 if shadow_length_confidence < .10 else shadow_length_confidence


            bar1_bottom = bar1[open] if is_green(bar1) else bar1[close]
            bar3_bottom = bar3[open] if is_green(bar3) else bar3[close]
            # FIX
            if bar1_bottom < bar2[low] or bar3_bottom < bar2[low]:
                return
            if bar2[open] - 0.01 > bar1_bottom and bar2[open] - 0.01 > bar3_bottom:
                extension_confidence = 0.10
            elif bar2[open] > bar1_bottom or bar2[open] > bar3_bottom:
                extension_confidence = 0.05
            else:
                extension_confidence = 0.15
            # END FIX
        else:

            #Color Confidence
            #color_confidence = 0.0

            lower_shadow = bar2[close] - bar2[low]
            candle_length = bar2[open] - bar2[close]
            if candle_length / bar2[open] >= .0020: #.20% and bigger candle doesn't need as much of a shadow
                candle_length = candle_length * 3 / 4
            if candle_length == 0:
                candle_length = 0.01


            #Shadow Length Confidence
            #shadow_length_confidence = min(0.40, (lower_shadow / candle_length) * 0.20)
            #shadow_length_confidence = 0.0 if shadow_length_confidence < .10 else shadow_length_confidence


            bar1_bottom = bar1[open] if is_green(bar1) else bar1[close]
            bar3_bottom = bar3[open] if is_green(bar3) else bar3[close]
            # FIX
            if bar1_bottom < bar2[low] or bar3_bottom < bar2[low]:
                return
            if bar2[close] - .01 > bar1_bottom or bar2[open] - .01 > bar3_bottom:
                extension_confidence = 0.10
            elif bar2[close] > bar1_bottom or bar2[close] > bar3_bottom:
                extension_confidence = 0.05
            else:
                extension_confidence = 0.15
            # END FIX
    total_confidence = color_confidence + shadow_length_confidence + volume_confidence + extension_confidence

    start_time = (start + datetime.timedelta(minutes=10)).time().strftime('%H:%M:%S')
    end_time = (start + datetime.timedelta(minutes=15)).time().strftime('%H:%M:%S')

    if (total_confidence >= 0.65):
        print(bar1)
        print(bar2)
        print(bar3)
        print({0} - {1}: {2} reversal
   # color confidence: {3:.2f}
   # shadow length confidence: {4:.2f}
   # volume confidence: {5:.2f}
   # extension confidence: {6:.2f}
   # total confidence: {7:.2f}.format(start_time, end_time, "downwards" if uptrend else "upwards", color_confidence,
   # shadow_length_confidence, volume_confidence, extension_confidence, total_confidence))
   """

def run_reversal_trends_test(tickers, start, end, time_interval, filename = None):
    global total_buy
    global buy_count
    global total_sell
    global sell_count
    global uptrend

    if filename is not None:
        fp = open(filename, "w+")
        description = "Test {0} bars, {1}% SL, {2}% TP, {3} start".format(lin_reg_bars, sl_percent * 100, tp_percent * 100, start.strftime("%X"))
        fp.write(datetime.datetime.now().strftime("%Y-%m-%d %X") + " Test")
        fp.write("\n" + description)

    split_interval = time_interval.split()
    num = int(split_interval[0])
    interval = split_interval[1]
    day_interval = num if interval == "d" else 0
    hour_interval = num if interval == "h" else 0
    min_interval = num if interval == "m" else 0
    increment = datetime.timedelta(days=day_interval, hours=hour_interval, minutes=min_interval)

    total_pl = 0
    for ticker in tickers:
        print("Starting ", ticker)
        total_buy = 0
        total_sell = 0
        buy_count = 0
        sell_count = 0

        if filename is not None:
            fp.write("\n" + ticker+ "\n")

        stock = yf.Ticker(ticker)
        history = stock.history(interval=time_interval.replace(" ", ""), start=start - lin_reg_bars * increment, end=end).values.tolist() #open - high - low - close - volume

        for x in range(lin_reg_bars, len(history)):
            if ticker in orders:
                check_orders(ticker, history[x])

            closing_prices = []
            for y in range(lin_reg_bars):
                closing_prices.append(history[x + y - lin_reg_bars][3])
            slope = get_linear_regression_slope(closing_prices)

            cl_price = closing_prices[-1]
            if uptrend is not None:
                shares = int(buying_power / (8.0 * cl_price)) - 1
                if slope > 0:
                    if not uptrend:
                        #print("BUY AT {0}: {1}".format(check_time - decrement, closing_prices[lin_reg_bars - 1]))
                        if ticker in positions:
                            cover_position_test(ticker, cl_price)
                        else:
                            positions[ticker] = (shares, cl_price)
                        bracket_buy_position_test(ticker, cl_price, shares)
                    uptrend = True
                elif slope < 0:
                    if uptrend:
                        #print("SELL AT {0}: {1}".format(check_time - decrement, closing_prices[lin_reg_bars - 1]))
                        if ticker in positions:
                            cover_position_test(ticker, cl_price)
                        else:
                            positions[ticker] = (shares, cl_price)
                        bracket_sell_position_test(ticker, cl_price, shares)
                    uptrend = False
            else:
                uptrend = True if slope > 0 else False

        """
        loop_count = 0
        last_price = 0
        while (start + (loop_count * increment) < end):
            #am I sending the right bars here??????
            last_price = check_reversal_trends_test(ticker, start + loop_count * increment, time_interval, history[loop_count:loop_count + lin_reg_bars])
            #time.sleep(1)
            loop_count = loop_count + 1
        """
        cover_position_test(ticker, history[-1][3])
        if filename is not None:
            avg_buy = total_buy / buy_count if buy_count > 0 else 0
            avg_sell = total_sell / sell_count if sell_count > 0 else 0
            fp.write("Avg Buy for {0} shares: {1:.3f}\n".format(buy_count, avg_buy ))
            fp.write("Avg Sell for {0} shares: {1:.3f}\n".format(sell_count, avg_sell))
            fp.write("Total Profit/Loss: {0:.2f}".format(p_l[ticker]))
            total_pl = total_pl + p_l[ticker]

    if filename is not None:
        fp.write("\n\nDaily Profit/Loss: {0:.2f}".format(total_pl))
        fp.close()

def run_15m_tests(tickers, year, month, day, filename = None):
    #Globals
    global total_buy
    global buy_count
    global total_sell
    global sell_count
    global fees

    #Locals
    _open = 0
    high = 1
    low = 2
    _close = 3
    volume = 4


    if filename is not None:
        fp = open(filename, "w+")
        description = "Testing 15m strategy with stop loss at .25% within range and take profit at .5% range above"
        fp.write(datetime.datetime.now().strftime("%Y-%m-%d %X") + " Test")
        fp.write("\n" + description)


    total_pl = 0
    for ticker in tickers:
        #print("Starting ", ticker)
        total_buy = 0
        total_sell = 0
        buy_count = 0
        sell_count = 0
        in_range = True

        if filename is not None:
            fp.write("\n" + ticker+ "\n")

        stock = yf.Ticker(ticker)
        start = datetime.datetime(year, month, day, 9, 30)
        end = datetime.datetime(year, month, day, 14, 30)
        history = stock.history(interval="1m", start=start, end=end).values.tolist() #open - high - low - close - volume
        extrema = []
        extrema.append(history[0][0])
        extrema.append(history[4][3])
        extrema.append(history[5][0])
        extrema.append(history[9][3])
        extrema.append(history[10][0])
        extrema.append(history[14][3])
        max_val = max(extrema)
        min_val = min(extrema)
        stop_loss = round((max_val - min_val) * .20, 2)
        long_stop_loss = round(max_val - stop_loss, 2)
        short_stop_loss = round(min_val + stop_loss, 2)
        print("max: ", max_val)
        print("min: ", min_val)
        print("stop loss: ", stop_loss)

        for bar in history[15:]:
            price = bar[_close]
            if price > max_val:
                if ticker not in positions and in_range is True:
                    shares = int(buying_power / (8.0 * price)) - 1
                    bracket_buy_position_test(ticker, price, shares, long_stop_loss, round(bar[_close] + 3 * stop_loss, 2))
                    in_range = False
                elif ticker in positions:
                     check_orders(ticker, bar)
                     if ticker not in orders:
                         in_range = False
            elif price < min_val:
                if ticker not in positions and in_range is True:
                    shares = int(buying_power / (8.0 * price)) - 1
                    bracket_sell_position_test(ticker, price, shares, short_stop_loss, round(bar[_close] - 3 * stop_loss, 2))
                    in_range = False
                elif ticker in positions:
                    check_orders(ticker, bar)
                    if ticker not in orders:
                        in_range = False
            elif price <= max_val and price >= min_val:
                if ticker not in positions:
                    in_range = True
                elif ticker in positions:
                    check_orders(ticker, bar)
                    if ticker not in orders:
                        in_range = True
        cover_position_test(ticker, history[-1][3])

        if filename is not None:
            avg_buy = total_buy / buy_count if buy_count > 0 else 0
            avg_sell = total_sell / sell_count if sell_count > 0 else 0
            fp.write("Avg Buy for {0} shares: {1:.3f}\n".format(buy_count, avg_buy ))
            fp.write("Avg Sell for {0} shares: {1:.3f}\n".format(sell_count, avg_sell))
            fp.write("Total Profit/Loss: {0:.2f}".format(p_l[ticker]))
            total_pl = total_pl + p_l[ticker]

        fees = fees + round(min(sell_count * 0.000119, 5.95),2)
        fees = fees + round(22.1 * (total_sell / 1000000.0), 2)

    if filename is not None:
        fp.write("\n\nDaily Profit/Loss: {0:.2f}".format(total_pl))
        fp.close()

def check_engulfing_4(bars):
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
    bar4 = bars[3][0:5]

    bar1_top = bar1[close] if is_green(bar1) else bar1[open]
    bar1_bottom = bar1[open] if is_green(bar1) else bar1[close]
    bar1_body = round(bar1_top - bar1_bottom, 2)
    bar1.append(bar1_top)
    bar1.append(bar1_bottom)
    bar1.append(bar1_body)

    bar2_top = bar2[close] if is_green(bar2) else bar2[open]
    bar2_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar2_body = round(bar2_top - bar2_bottom, 2)
    bar2.append(bar2_top)
    bar2.append(bar2_bottom)
    bar2.append(bar2_body)

    bar3_top = bar3[close] if is_green(bar3) else bar3[open]
    bar3_bottom = bar3[open] if is_green(bar3) else bar3[close]
    bar3_body = round(bar3_top - bar3_bottom, 2)
    bar3.append(bar3_top)
    bar3.append(bar3_bottom)
    bar3.append(bar3_body)

    bar4_top = bar4[close] if is_green(bar4) else bar4[open]
    bar4_bottom = bar4[open] if is_green(bar4) else bar4[close]
    bar4_body = round(bar4_top - bar4_bottom, 2)
    bar4.append(bar4_top)
    bar4.append(bar4_bottom)
    bar4.append(bar4_body)

    if is_green(bar1) == is_green(bar2) or is_green(bar1) == is_green(bar4):
        return False
    if is_green(bar1) and not is_green(bar2):
        if (bar2[top] >= bar1[top] * .9998 and bar4[bottom] < bar1[bottom]
            and bar4[top] - bar3[bottom] > 1.15 * bar1[body]):
            return True
        else:
            return False
    if not is_green(bar1) and is_green(bar2):
        if (bar2[bottom] <= bar1[bottom] *1.0002 and bar4[top] > bar1[top]
            and bar4[top] - bar2[bottom] >= 1.15 * bar1[body]):
            return True
        else:
            return False

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
    bar1.append(bar1_body)

    bar2_top = bar2[close] if is_green(bar2) else bar2[open]
    bar2_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar2_body = round(bar2_top - bar2_bottom, 2)
    bar2.append(bar2_top)
    bar2.append(bar2_bottom)
    bar2.append(bar2_body)

    bar3_top = bar3[close] if is_green(bar3) else bar3[open]
    bar3_bottom = bar3[open] if is_green(bar3) else bar3[close]
    bar3_body = round(bar3_top - bar3_bottom, 2)
    bar3.append(bar3_top)
    bar3.append(bar3_bottom)
    bar3.append(bar3_body)

    if bar1[body] / bar1[close] < .0015:
        return False
    if is_green(bar1):
        if (bar2[top] - bar3[bottom]) / bar3[close] < .002:
            return False
    else:
        if (bar3[top] - bar2[bottom]) / bar3[close] < .002:
            return False

    if is_green(bar1) == is_green(bar2) or is_green(bar1) == is_green(bar3):
        return False
    if is_green(bar1) and not is_green(bar2):
        if (bar2[top] >= bar1[top] * .9998 and bar3[bottom] < bar1[bottom]#(bar2[bottom] < bar1[bottom] or bar3[bottom] < bar1[bottom])
            and bar2[top] - bar3[bottom] > 1.15 * bar1[body]):
            return True
        else:
            return False
    if not is_green(bar1) and is_green(bar2):
        if (bar2[bottom] <= bar1[bottom] *1.0002 and bar3[top] > bar1[top]#(bar2[top] > bar1[top] or bar3[top] > bar1[top])
            and bar3[top] - bar2[bottom] >= 1.15 * bar1[body]):
            return True
        else:
            return False

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
    bar1.append(bar1_body)

    bar2_top = bar2[close] if is_green(bar2) else bar2[open]
    bar2_bottom = bar2[open] if is_green(bar2) else bar2[close]
    bar2_body = round(bar2_top - bar2_bottom, 2)
    bar2.append(bar2_top)
    bar2.append(bar2_bottom)
    bar2.append(bar2_body)

    if bar1[body] / bar1[close] < 0.0015:
        return False
    if bar2[body] / bar2[close] < 0.002:
        return False

    if is_green(bar1) == is_green(bar2):
        return False
    if is_green(bar1) and not is_green(bar2):
        if (bar2[top] >= bar1[top] - .01 and bar2[bottom] < bar1[bottom]
            and bar2[body] >= 1.15 * bar1[body]):
            return True
        else:
            return False
    if not is_green(bar1) and is_green(bar2):
        if (bar2[bottom] <= bar1[bottom] + .01 and bar2[top] > bar1[top]
            and bar2[body] >= 1.15 * bar1[body]):
            return True
        else:
            return False

def run_engulfing_test(tickers, start, end, time_interval):
    #Globals
    global fees

    #Locals
    _open = 0
    _close = 3

    split_interval = time_interval.split()
    num = int(split_interval[0])
    interval = split_interval[1]
    day_interval = num if interval == "d" else 0
    hour_interval = num if interval == "h" else 0
    min_interval = num if interval == "m" else 0
    increment = datetime.timedelta(days=day_interval, hours=hour_interval, minutes=min_interval)

    for ticker in tickers:
        print("Starting ", ticker)

        stock = yf.Ticker(ticker)
        history = stock.history(interval=time_interval.replace(" ", ""), start=start, end=end).values.tolist() #open - high - low - close - volume

        long = False
        short = False
        for x in range(3, len(history)):
            print("{0}:".format(start + (x + 1) * increment))
            check_orders(ticker, history[x])
            #print("Opening Price: {0:.2f}".format(history[x][_open]))
            #print("Closing Price: {0:.2f}".format(history[x][_close]))
            if check_engulfing_2(history[x-1:x+1]):
                price = history[x][_close]
                print("\tEngulfing Detected")
                if is_green(history[x-1]) and not short:
                    if long:
                        cover_position_test(ticker, price)
                    short = True
                    long = False
                    print("\tBearish Engulfing")
                    print("\tClosing Price: {0:.2f}".format(price))
                    bracket_sell_position_test(ticker, price, int(individual_bp / price), history[x-1][_close], round(price * 0.9925, 2))
                elif not is_green(history[x-1]) and not long:
                    if short:
                        cover_position_test(ticker, price)
                    long = True
                    short = False
                    print("\tBullish Engulfing")
                    print("\tClosing Price: {0:.2f}".format(price))
                    bracket_buy_position_test(ticker, price, int(individual_bp / price), history[x-1][_close], round(price * 1.0075, 2))
                else:
                    print("\tNo action taken")
            elif check_engulfing_3(history[x-2:x+1]):
                price = history[x][_close]
                print("\tEngulfing detected over two bars")
                if is_green(history[x-2]) and not short:
                    if long:
                        cover_position_test(ticker, price)
                    short = True
                    long = False
                    print("\tBearish Engulfing")
                    print("\tClosing Price: {0:.2f}".format(price))
                    bracket_sell_position_test(ticker, price, int(individual_bp / price), history[x-2][_close], round(price * .9925, 2))
                elif not is_green(history[x-2]) and not long:
                    if short:
                        cover_position_test(ticker, price)
                    long = True
                    short = False
                    print("\tBullish Engulfing")
                    print("\tClosing Price: {0:.2f}".format(price))
                    bracket_buy_position_test(ticker, price, int(individual_bp / price), history[x-2][_close], round(price * 1.0075, 2))
                else:
                    print("\tNo action taken")
            """
            elif check_engulfing_4(history[x-3:x+1]):
                price = history[x][_close]
                print("\tEngulfing detected over three bars")
                if is_green(history[x-3]) and not short:
                    if long:
                        cover_position_test(ticker, price)
                    short = True
                    long = False
                    print("\tBearish Engulfing")
                    print("\tClosing Price: {0:.2f}".format(price))
                    bracket_sell_position_test(ticker, price, int(individual_bp / price), history[x-3][_close], round(price * .99, 2))
                elif not is_green(history[x-3]) and not long:
                    if short:
                        cover_position_test(ticker, price)
                    long = True
                    short = False
                    print("\tBullish Engulfing")
                    print("\tClosing Price: {0:.2f}".format(price))
                    bracket_buy_position_test(ticker, price, int(individual_bp / price), history[x-3][_close], round(price * 1.01, 2))
                else:
                    print("\tNo action taken")
            """
        cover_position_test(ticker, history[-1][_close])


    fees = fees + round(min(sell_count * 0.000119, 5.95),2)
    fees = fees + round(22.1 * (total_sell / 1000000.0), 2)

def start_15m(tickers, test_results):

    fifteen_m_long_test_dates = [(11, 30), (12, 1), (12, 2), (12, 3), (12, 4),
                        (12, 7), (12, 8), (12, 9), (12, 10), (12, 11), (12, 14), (12, 15), (12, 16),
                        (12, 17), (12, 18), (12, 21), (12, 22), (12, 23)]
    fifteen_length = len(fifteen_m_long_test_dates)

    interval = "5 m"

    ## 15 m Test
    for x in range(fifteen_length):
        year = 2020
        month = fifteen_m_long_test_dates[x][0]
        day = fifteen_m_long_test_dates[x][1]
        filename = "{0}b.txt".format(x)
        print("\n*** ", year, " ", month, " ", day, "***\n")
        run_15m_tests(tickers, year, month, day)#, filename)
        for ticker in p_l:
            if ticker in testing_p_l:
                testing_p_l[ticker] = testing_p_l[ticker] + p_l[ticker]
            else:
                testing_p_l[ticker] = p_l[ticker]
        reset_globals()
        test_results.write("{0}\n".format(datetime.datetime(2020, fifteen_m_long_test_dates[x][0], fifteen_m_long_test_dates[x][1]).strftime("%B %d %Y")))
        if x == fifteen_length - 1:
            test_total = 0
            test_results.write("INDIVIDUAL: \n")
            for ticker in testing_p_l:
                test_results.write("{0}:\n\tOverall P/L of {1:.2f}\n".format(ticker, testing_p_l[ticker]))
                test_results.write("\tDaily Avg P/L of {0:.2f}\n".format(testing_p_l[ticker] / fifteen_length))
                test_total = test_total + testing_p_l[ticker]
            test_results.write("OVERALL: \n")
            test_results.write("\tOverall P/L of {0:.2f}\n".format(test_total))
            test_results.write("\tDaily Avg P/L of {0:.2f}\n".format(test_total / fifteen_length))
            test_results.write("\n\nThis test was performed with a stop loss of 20% opening range, and a take profit at 60% opening range\n")

def start_trends(tickers, test_results):
    reversal_trend_long_test_dates = [(10, 27), (10, 28), (10, 29), (10, 30), (11, 2), (11, 3),
                       (11, 4), (11, 5), (11, 6), (11, 9), (11, 10), (11, 11), (11, 12),
                       (11, 13), (11, 16), (11, 17), (11, 18), (11, 19), (11, 20), (11, 23),
                       (11, 24), (11, 25), (11, 30), (12, 1), (12, 2), (12, 3), (12, 4),
                       (12, 7), (12, 8), (12, 9), (12, 10), (12, 11), (12, 14), (12, 15), (12, 16),
                       (12, 17), (12, 18), (12, 21), (12, 22), (12, 23)]

    reversal_length = len(reversal_trend_long_test_dates)

    interval = "5 m"

    ## Reversal Trends Test
    for x in range(reversal_length):
        start = datetime.datetime(2020, reversal_trend_long_test_dates[x][0], reversal_trend_long_test_dates[x][1], 10, 0)
        end = datetime.datetime(2020, reversal_trend_long_test_dates[x][0], reversal_trend_long_test_dates[x][1], 16, 0)
        filename = "{0}_{1}_BASELINE.txt".format(reversal_trend_long_test_dates[x][0], reversal_trend_long_test_dates[x][1])
        run_engulfing_test(tickers, start, end, interval)
        for ticker in p_l:
            if ticker in testing_p_l:
                testing_p_l[ticker] = testing_p_l[ticker] + p_l[ticker]
            else:
                testing_p_l[ticker] = p_l[ticker]
        reset_globals()
        test_results.write("{0}\n".format(datetime.datetime(2020, reversal_trend_long_test_dates[x][0], reversal_trend_long_test_dates[x][1]).strftime("%B %d %Y")))
        if x == reversal_length - 1:
            test_results.write("The number of linear regression bars used is: {0}\n".format(lin_reg_bars))
            test_results.write("The time interval for bars is: {0}\n".format(interval))
            test_results.write("The stop loss percentage in place is: {0}%\n".format(sl_percent * 100))
            test_results.write("The take profit percentage in place is: {0}%\n".format(tp_percent * 100))
            test_total = 0
            test_results.write("INDIVIDUAL: \n")
            for ticker in testing_p_l:
                test_results.write("{0}:\n\tOverall P/L of {1:.2f}\n".format(ticker, testing_p_l[ticker]))
                test_results.write("\tDaily Avg P/L of {0:.2f}\n".format(testing_p_l[ticker] / reversal_length))
                test_total = test_total + testing_p_l[ticker]
            test_results.write("OVERALL: \n")
            test_results.write("\tOverall P/L of {0:.2f}\n".format(test_total))
            test_results.write("\tDaily Avg P/L of {0:.2f}\n".format(test_total / reversal_length))

def start_engulfing(tickers, test_results):
    engulfing_trend_long_test_dates = [(10, 30), (11, 2), (11, 3), (11, 4), (11, 5),
                       (11, 6), (11, 9), (11, 10), (11, 11), (11, 12), (11, 13), (11, 16),
                       (11, 17), (11, 18), (11, 19), (11, 20), (11, 23), (11, 24), (11, 25),
                       (11, 30), (12, 1), (12, 2), (12, 3), (12, 4), (12, 7), (12, 8),
                       (12, 9), (12, 10), (12, 11), (12, 14), (12, 15), (12, 16),
                       (12, 17), (12, 18), (12, 21), (12, 22), (12, 23)]

    engulfing_length = len(engulfing_trend_long_test_dates)

    interval = "5 m"

    for x in range(engulfing_length):
        start = datetime.datetime(2020, engulfing_trend_long_test_dates[x][0], engulfing_trend_long_test_dates[x][1], 9, 30)
        end = datetime.datetime(2020, engulfing_trend_long_test_dates[x][0], engulfing_trend_long_test_dates[x][1], 15, 45)
        run_engulfing_test(tickers, start, end, interval)
        for ticker in p_l:
            if ticker in testing_p_l:
                testing_p_l[ticker] = testing_p_l[ticker] + p_l[ticker]
            else:
                testing_p_l[ticker] = p_l[ticker]
        reset_globals()
        test_results.write("{0}\n".format(datetime.datetime(2020, engulfing_trend_long_test_dates[x][0], engulfing_trend_long_test_dates[x][1]).strftime("%B %d %Y")))
        if x == engulfing_length - 1:
            test_total = 0
            test_results.write("INDIVIDUAL: \n")
            for ticker in testing_p_l:
                test_results.write("{0}:\n\tOverall P/L of {1:.2f}\n".format(ticker, testing_p_l[ticker]))
                test_results.write("\tDaily Avg P/L of {0:.2f}\n".format(testing_p_l[ticker] / engulfing_length))
                test_total = test_total + testing_p_l[ticker]
            test_results.write("OVERALL: \n")
            test_results.write("\tOverall P/L of {0:.2f}\n".format(test_total))
            test_results.write("\tDaily Avg P/L of {0:.2f}\n".format(test_total / engulfing_length))
            print("Overall P/L:   {0:.2f}".format(test_total))
            print("Daily Avg P/L: {0:.2f}".format(test_total / engulfing_length))

def main():
    global lin_reg_bars
    global sl_percent
    global tp_percent

    #make_plot(datetime.datetime(2020, 12, 3, 9, 30), datetime.datetime(2020, 12, 3, 16), "5m", "AAPL", 5)
    """start = datetime.datetime(2020, 12, 30, 9, 30)
    end = datetime.datetime(2020, 12, 30, 9, 35)
    stock = yf.Ticker("AAPL")
    history = stock.history(interval="5m", start=start, end=end).values.tolist() #open - high - low - close - volume
    print(history)
    """
    tickers = ["AAPL","T", "V", "WMT", "FB", "JNJ", "MSFT", "CSCO"]

    test_results = open("{0}_TESTS.txt".format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")), "w+")
    test_results.write(datetime.datetime.now().strftime("%Y-%m-%d %X") + " Test\n")
    test_results.write("\nThe tickers used are: \n")
    for ticker in tickers:
        test_results.write("{0}\n".format(ticker))
    test_results.write("This test is performed over the following Dates: \n")

    #start_15m(tickers, test_results)

    #start_trends(tickers, test_results)

    start_engulfing(tickers, test_results)

    test_results.write("\nTotal Fees: {0:.2f}".format(fees))
    test_results.close()
    print("Total Fees: {0:.2f}".format(fees))

if __name__ == "__main__":
    # execute only if run as a script
    exit(main())
