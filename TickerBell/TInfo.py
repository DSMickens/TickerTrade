import yfinance as yf
import yahoo_fin.stock_info as si
import time
import sys
import tempfile

def getLivePrice(ticker):
  """
  Get and return the price of a stock from the ticker

  Params
    ticker (String) - ticker for the stock to check
  """
  try:
    return si.get_live_price(ticker)
  except AssertionError:
    print("Invalid Ticker Symbol: {0}".format(ticker))
    return None

def getOpenPrice(ticker):
  """
  Get and return the price of a stock at the current day's open

  Params
    ticker (String) - ticker for the stock to check
  """
  try:
    today = time.strftime("%m/%d/%y")
    open = list(si.get_data(ticker, start_date=today).to_dict()["open"].values())[0]
    return open
  except AssertionError:
    print("Invalid Ticker Symbol: {0}".format(ticker))
    return None

def getClosePrice(ticker):
  """
  Get and return the price of a stock at the previous day's close

  Params
    ticker (String) - ticker for the stock to check
  """
  try:
    yesterday = time.strftime("%m/%d/%y", time.localtime(time.time() - 86400))
    close = list(si.get_data(ticker, start_date=yesterday).to_dict()["close"].values())[0]
    return close
  except AssertionError:
    print("Invalid Ticker Symbol: {0}".format(ticker))
    return None

#def getExtendedPrice(ticker):
 # ""Get and return the current days extended hours price""
  #today = time.strftime("%Y-%m-%d")
  #redirect output for the unneceesary download output
  #price = yf.download(ticker, prepost=True, start=today).to_dict()
  #print(price)
  #return price

def getData(ticker):
  """
  Get and return all of one stock's info data for the current day

  Params
    ticker (String) - ticker for the stock to check
  """
  try:
    today = time.strftime("%m/%d/%y")
    data = si.get_data(ticker, start_date=today).to_dict()
    return data
  except AssertionError:
    print("Ticker {0} does not exist".format(ticker))
    return None

def getLiveVolume(ticker):
  """
  Gets and returns the current days regular hours volume

  Params
    ticker (String) - ticker for the stock to check
  """
  today = time.strftime("%m/%d/%y")
  try:
    volume = list(si.get_data(ticker, start_date=today).to_dict()["volume"].values())[0]
    return volume
  except AssertionError:
    print("Ticker {0} does not exist".format(ticker))
    return None

def priceHandler(inpt):
  """
  Handles the user input for the price command

  Params:
    inpt (string): The input line for price command
  """
  args = inpt.split(' ')
  ticker = args[0]
  if (len(args) == 2 and args[1] == "open"):
    price = getOpenPrice(ticker)
    if price is not None:
      print("Price of {0} at open: {1:.4f}".format(ticker, price))
  elif (len(args) == 2 and args[1] == "close"):
    price = getClosePrice(ticker)
    if price is not None:
      print("Price of {0} at previous close: {1:.4f}".format(ticker, price))
  elif (len(args) == 1):
    price = getLivePrice(ticker)
    if price is not None:
      print("Price of {0}: {1:.4f}".format(ticker, price))
  else:
    print("Invalid price arguments: {0}".format(inpt))

def volumeHandler(inpt):
  """
  Handles the user input for the volume command

  Params:
    inpt (String): The input line for volume command
  """
  args = inpt.split(' ')
  ticker = args[0]
  volume = getLiveVolume(ticker)
  if volume is not None:
    print("Volume of {0}: {1:,}".format(ticker, volume))

def handleInfo(inpt):
  """
  takes input from TickerBell main input stream and distributes
  work across Info module functions.

  Params:
    inpt (String): contains the user input info commands
  """
  args = inpt.split(' ')
  cmd = args[0]

  if (cmd == "price"):
    priceHandler(inpt[6:])
  elif (cmd == "volume"):
    volumeHandler(inpt[7:])
  elif (cmd == "data"):
    data = getData(inpt[5:])
    if data is not None:
      print(data)
  else:
    print("Invalid Info Command: {0}".format(cmd))
    return -1
