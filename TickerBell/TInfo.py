import alpaca_trade_api as ata
import os
import yfinance as yf
import TPasswords
import datetime
import sys
import tempfile

os.environ["APCA_API_KEY_ID"] = TPasswords.alpaca_key_id
os.environ["APCA_API_SECRET_KEY"] = TPasswords.alpaca_secret_key
os.environ["APCA_API_BASE_URL"] = TPasswords.alpaca_base_url
api = ata.REST()

def getLivePrice(ticker):
  """
  Get and return the price of a stock from the ticker

  Params
    ticker (String) - ticker for the stock to check
  """
  try:
    return api.get_last_trade(ticker.upper()).price
  except:
    print("Invalid Ticker Symbol: {0}".format(ticker))
    return None

def getOpenPrice(ticker):
  """
  Get and return the price of a stock at the current day's open

  Params
    ticker (String) - ticker for the stock to check
  """
  try:
    today = datetime.datetime.today()
    stock = yf.Ticker(ticker)
    history = stock.history(interval = "1d", start = today, end = today).values.tolist()
    return history[0][0]
  except:
    print("Invalid Ticker Symbol: {0}".format(ticker))
    return None

def getClosePrice(ticker):
  """
  Get and return the price of a stock at the previous day's close

  Params
    ticker (String) - ticker for the stock to check
  """
  try:
    yesterday = datetime.datetime.today() - datetime.timedelta(days = 1)
    stock = yf.Ticker(ticker)
    history = stock.history(interval = "1d", start = yesterday, end = yesterday).values.tolist()
    return history[0][3]
  except AssertionError:
    print("Invalid Ticker Symbol: {0}".format(ticker))
    return None

def getLiveVolume(ticker):
  """
  Gets and returns the current days regular hours volume

  Params
    ticker (String) - ticker for the stock to check
  """
  try:
    today = datetime.datetime.today()
    stock = yf.Ticker(ticker)
    history = stock.history(interval = "1d", start = today, end = today).values.tolist()
    return history[0][4]
  except:
    print("Invalid Ticker Symbol: {0}".format(ticker))
    return None

def handleInfo(inpt):
  """
  takes input from TickerBell main input stream and distributes
  work across Info module functions.

  Params:
    inpt (String): contains the user input info commands
  """
  args = inpt.split(' ')
  cmd = args[0]
  params = args[1:]
  if (cmd.lower() == "price"):
    ticker = params[0]
    if (len(params) == 2 and params[1].lower() == "open"):
      price = getOpenPrice(ticker)
      if price is not None:
        print("Price of {0} at open: {1:.4f}".format(ticker, price))
    elif (len(params) == 2 and params[1].lower() == "close"):
      price = getClosePrice(ticker)
      if price is not None:
        print("Price of {0} at previous close: {1:.4f}".format(ticker, price))
    elif (len(params) == 1):
      price = getLivePrice(ticker)
      if price is not None:
        print("Price of {0}: {1:.4f}".format(ticker, price))
    else:
      print("Invalid price arguments: {0}".format(inpt))
  elif (cmd.lower() == "volume"):
    ticker = params[0]
    volume = getLiveVolume(ticker)
    if volume is not None:
        print("Volume of {0}: {1:,}".format(ticker, volume))
  else:
    print("Invalid Info Command: {0}".format(cmd))
    return -1
