#!/anaconda3/bin/python3

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
import datetime
import yfinance as yf
import pandas as pd
import os
import cgi, cgitb
import alpaca_trade_api as ata

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

print("Content-type: text\n\n")

def create_ticker_graph(ticker, day):

    #check to make sure all trades have same date
    #check to make sure date is within range of history

    date = datetime.datetime.strptime(day, "%Y-%m-%d %H:%M:%S")
    start = date.replace(hour = 9, minute = 30, second = 0, microsecond = 0)
    end = date.replace(hour = 16, minute = 0, second = 0, microsecond = 0)

    stk = yf.Ticker(ticker)
    his = stk.history(interval="5m", start=start, end=end).values.tolist() #open - high - low - close - volume
    x = []
    y = []
    count = 0
    five_minutes = datetime.timedelta(minutes = 5)
    for bar in his:
        x.append((start + five_minutes * count, bar[0], bar[1], bar[2], bar[3], bar[4]))
        count = count + 1
    df = pd.DataFrame(x, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df.set_index('Date', inplace=True)

    working_root_dir = os.path.abspath(os.path.join(__file__ ,"../../.."))

    try:
        os.mkdir(working_root_dir + '/images/charts/{0}'.format(ticker))
    except OSError as error:
        print("Error Found")

    mpf.plot(df, type='candle', volume=True, style='charles',
             title = '{0} {1}'.format(ticker, start.strftime("%Y-%m-%d")),
             ylabel='', ylabel_lower='', savefig= working_root_dir + "/images/charts/{0}/{1}".format(ticker, date.strftime("%Y-%m-%d")))
    plt.close(plt.figure())

def create_daily_graph():
    # get portfolio history
    working_root_dir = os.path.abspath(os.path.join(__file__ ,"../../.."))
    filepath = working_root_dir + "/images/daily_pl.png"
    portfolio_history = api.get_portfolio_history(period="1M", timeframe="1D")
    x = [datetime.datetime.fromtimestamp(x) for x in portfolio_history.timestamp]
    y = portfolio_history.profit_loss
    plt.plot(x, y)
    if os.path.isfile(filepath):
        os.remove(filepath)
    plt.axhline(0, color='black')
    plt.xticks(rotation=45)
    plt.savefig(filepath)
    plt.close()

def handleInput(data):
    function = data.getvalue("function")
    if function == "ticker graph":
        ticker = data.getvalue("ticker")
        day = data.getvalue("day")
        create_ticker_graph(ticker, day)
    elif function == "daily graph":
        create_daily_graph()

def main():
    data= cgi.FieldStorage()
    handleInput(data)
    #create_daily_graph()
if __name__ == "__main__":
    # execute only if run as a script
    exit(main())
