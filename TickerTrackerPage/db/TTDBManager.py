import mysql.connector as mc
from sampleData import sampleData
import datetime
import os
import sys
import yfinance as yf
import alpaca_trade_api as ata
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

connection=mc.connect(
    host=TPasswords.db_host,
    user=TPasswords.db_user,
    password =TPasswords.db_password
    )

staged_db_rows = {}
daily_bar_histories = {}

def create_db():
    connection.cursor().execute("DROP DATABASE IF EXISTS TTDB;")

    create_db_query = "CREATE DATABASE IF NOT EXISTS TTDB;"
    connection.cursor().execute(create_db_query)

    use_database_query = "USE TTDB;"
    connection.cursor().execute(use_database_query)

def create_db_table():
    connection.cursor().execute("DROP TABLE IF EXISTS trades;")

    create_table_query = """
    CREATE TABLE IF NOT EXISTS trades(
        id CHAR (40) PRIMARY KEY,
        ticker CHAR (4) NOT NULL,
        is_long BOOL NOT NULL,
        open_time DATETIME NOT NULL,
        close_time DATETIME NOT NULL,
        success BOOL NOT NULL,
        p_l DECIMAL (5, 2) NOT NULL,
        engulfing_bars INT NOT NULL CHECK (engulfing_bars IN (2, 3)),
        engulfing_percentage DECIMAL (6, 2) NOT NULL,
        take_profit_percentage DECIMAL (4, 3) NOT NULL,
        stop_loss_percentage DECIMAL (4, 3) NOT NULL,
        max_profit_percentage DECIMAL (5, 4) NOT NULL,
        max_loss_percentage DECIMAL (5, 4) NOT NULL,
        dia_at_open DECIMAL (6, 2) NOT NULL,
        spy_at_open DECIMAL (6, 2) NOT NULL,
        qqq_at_open DECIMAL (6, 2) NOT NULL,
        position_closure_reason CHAR (20) NOT NULL CHECK (position_closure_reason IN ('eod', 'stop loss', 'take profit', 'engulfing'))
    );"""
    connection.cursor().execute(create_table_query)

def create_sample_db_table():

    connection.cursor().execute("DROP TABLE IF EXISTS sample_trades;")

    create_table_query = """
    CREATE TABLE IF NOT EXISTS sample_trades(
        id CHAR (40) PRIMARY KEY,
        ticker CHAR (4) NOT NULL,
        is_long BOOL NOT NULL,
        open_time DATETIME NOT NULL,
        close_time DATETIME NOT NULL,
        success BOOL NOT NULL,
        p_l DECIMAL (5, 2) NOT NULL,
        engulfing_bars INT NOT NULL CHECK (engulfing_bars IN (2, 3)),
        engulfing_percentage DECIMAL (6, 2) NOT NULL,
        take_profit_percentage DECIMAL (4, 3) NOT NULL,
        stop_loss_percentage DECIMAL (4, 3) NOT NULL,
        max_profit_percentage DECIMAL (5, 4) NOT NULL,
        max_loss_percentage DECIMAL (5, 4) NOT NULL,
        dia_at_open DECIMAL (6, 2) NOT NULL,
        spy_at_open DECIMAL (6, 2) NOT NULL,
        qqq_at_open DECIMAL (6, 2) NOT NULL,
        position_closure_reason CHAR (20) NOT NULL CHECK (position_closure_reason IN ('eod', 'stop loss', 'take profit', 'engulfing'))
    );"""
    connection.cursor().execute(create_table_query)

    delete_entries_query = "DELETE FROM sample_trades;"
    connection.cursor().execute(delete_entries_query)

    for t in sampleData:
        insert_data("sample_trades", t)

def insert_data(table_name, row_data):
    num_values = len(row_data)
    if num_values < 1:
        return;
    insert_query = "INSERT INTO {0} VALUES (%s".format(table_name) + ", %s" * (num_values - 1) +") "
    connection.cursor().execute(insert_query, row_data)
    connection.commit()

def get_daily_bars(date, tickers):
    global daily_bar_histories

    updated_tickers = []
    updated_tickers += list(tickers)
    updated_tickers.extend(["DIA", "SPY", "QQQ"])
    start = datetime.datetime.combine(date, datetime.time(hour = 9, minute = 30, second = 0))
    end = start.replace(hour = 16, minute = 0, second = 0)
    for ticker in updated_tickers:
        stock = yf.Ticker(ticker)
        #OHLCV
        history = stock.history(interval = "5m", start=start, end=end).values.tolist()
        daily_bar_histories[ticker] = history

def is_green(bar):
    return bar[0] <= bar[3]

def create_row(open_order, close_order):
    global daily_bar_histories

    id = open_order.id
    ticker = open_order.symbol
    is_long = (open_order.side == 'buy')
    open_time = datetime.datetime.strptime(str(open_order.filled_at).split('.')[0], "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours = 5)
    close_time = datetime.datetime.strptime(str(close_order.filled_at).split('.')[0], "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours = 5)
    if is_long:
        p_l = round(int(open_order.filled_qty) * (float(close_order.filled_avg_price) - float(open_order.filled_avg_price)), 2)
    else:
        p_l = round(int(open_order.filled_qty) * (float(open_order.filled_avg_price) - float(close_order.filled_avg_price)), 2)
    success = (p_l > 0)

    #### Getting more complicated Data revolving around intraday price action ####
    end_time = open_time.replace(minute = (open_time.minute - (open_time.minute % 5)), second = 0)
    #print(end_time)
    difference = end_time - end_time.replace(hour = 9, minute = 30, second = 0)
    minutes = difference.seconds / 60
    end_index = int(minutes / 5)
    start_index = int(end_index - 3)
    #print(open_time, daily_bar_histories[ticker][start_index:end_index])
    bar1 = daily_bar_histories[ticker][start_index]
    bar2 = daily_bar_histories[ticker][start_index + 1]
    bar3 = daily_bar_histories[ticker][end_index]
    engulfing_bars = 2 if (is_green(bar2) != is_green(bar3)) else 3
    if engulfing_bars == 2:
        if bar2[0] != bar2[3]:
            engulfing_percentage = abs(bar3[3] - bar2[3]) / abs(bar2[3] - bar2[0])
        else:
            engulfing_percentage = abs(bar3[3] - bar2[3]) / 0.01
    elif engulfing_bars == 3:
        if bar1[0] != bar1[3]:
            engulfing_percentage = abs(bar3[3] - bar1[3]) / abs(bar1[3] - bar1[0])
        else:
            engulfing_percentage = abs(bar3[3] - bar1[3]) / 0.01
    engulfing_percentage = round(engulfing_percentage * 100, 2)
    take_profit_percentage = 0.75
    stop_loss_percentage = abs((bar3[3] - bar2[0]) / bar3[3]) if engulfing_bars == 2 else abs((bar3[3] - bar1[0]) / bar3[3])
    ## max profit and loss. Find max/min of bars within open and close of position
    # get open_bar and close_bar (1st and last bars within position)
    time_count = end_time
    count = 1
    max_val = float(open_order.filled_avg_price)
    min_val = max_val
    while (time_count <= close_time.replace(minute = (close_time.minute - (close_time.minute % 5)), second = 0)):
        if daily_bar_histories[ticker][end_index + count][1] > max_val:
            max_val = daily_bar_histories[ticker][end_index + count][1]
        if daily_bar_histories[ticker][end_index + count][2] < min_val:
            min_val = daily_bar_histories[ticker][end_index + count][2]
        time_count += datetime.timedelta(minutes = 5)
    if is_long:
        max_profit_percentage = round((max_val - float(open_order.filled_avg_price)) / float(open_order.filled_avg_price) * 100, 2)
        max_loss_percentage = round((float(open_order.filled_avg_price) - min_val) / float(open_order.filled_avg_price) * 100, 2)
    else:
        max_profit_percentage = round((float(open_order.filled_avg_price) - min_val) / float(open_order.filled_avg_price) * 100, 2)
        max_loss_percentage = round((max_val - float(open_order.filled_avg_price)) / float(open_order.filled_avg_price) * 100, 2)

    dia_at_open = daily_bar_histories["DIA"][end_index][3]
    spy_at_open = daily_bar_histories["SPY"][end_index][3]
    qqq_at_open = daily_bar_histories["QQQ"][end_index][3]

    if close_time.time() >= close_time.replace(hour = 15, minute = 45, second = 0, microsecond = 0).time():
        closure_reason = "eod"
    elif close_order.type == "limit":
        closure_reason = "take profit"
    elif close_order.type == "stop":
        closure_reason = "stop loss"
    elif close_order.type == "market":
        closure_reason = "engulfing"

    row_data = [id, ticker, is_long, open_time, close_time, success, p_l, engulfing_bars, engulfing_percentage, take_profit_percentage, stop_loss_percentage, max_profit_percentage, max_loss_percentage, dia_at_open, spy_at_open, qqq_at_open, closure_reason]
    print(ticker, id)
    insert_data("trades", row_data)


def get_daily_updates(date = datetime.date.today() - datetime.timedelta(days = 1)):
    #all of the orders for day "date"
    tomorrow = date + datetime.timedelta(days=1)
    orders = api.list_orders(until=tomorrow, after=date, status='all', limit=500, nested=True, direction='asc')
    obt = {} #orders by ticker
    for order in orders:
        if order.symbol in obt.keys():
            obt[order.symbol].append(order)
        else:
            obt[order.symbol] = [order]

    get_daily_bars(date, obt.keys())

    for ticker in obt.keys():
        print(ticker)

        count = 0
        #find first order w/ legs where filled_qty > 0
        #check legs to see if either has filled_qty > 0
            #if neither leg has filled_qty > 0, check next order
                #if next order does not have filled_qty > 0, check current positions
                    #if no current position, Error
        while (count < len(obt[ticker])):
            if obt[ticker][count].status == 'filled' and obt[ticker][count].legs != 'null':
                open_order = obt[ticker][count]
                if open_order.legs[0].status == 'filled':
                    close_order = open_order.legs[0]
                    create_row(open_order, close_order)
                elif open_order.legs[1].status == 'filled':
                    close_order = open_order.legs[1]
                    create_row(open_order, close_order)
                else:
                    if (int(obt[ticker][count+1].filled_qty) == int(open_order.filled_qty) and
                        obt[ticker][count+1].side != open_order.side and obt[ticker][count+1].type == 'market'):
                        close_order = obt[ticker][count+1]
                        create_row(open_order, close_order)
                        count += 1
            count += 1



def main():
    try:
        create_db()
        create_sample_db_table()
        create_db_table()
        get_daily_updates()
    except mc.Error as e:
        print(e)

if __name__ == "__main__":
    # execute only if run as a script
    exit(main())
