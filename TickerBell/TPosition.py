import alpaca_trade_api as ata
import os
import TPasswords

os.environ["APCA_API_KEY_ID"] = TPasswords.alpaca_key_id
os.environ["APCA_API_SECRET_KEY"] = TPasswords.alpaca_secret_key
os.environ["APCA_API_BASE_URL"] = TPasswords.alpaca_base_url
api = ata.REST()

Positions = {}

def updatePosition(inpt):
  """
  adds or updates the Positions global to include the user inputted position

  Params:
    inpt (String): should contain the ticker, avg price, and quantity of the position
  """
  args = inpt.split(' ')
  if (len(args) != 3):
    print("Invalid number of arguments: {0}".format(len(args)))
    return
  try:
    ticker = args[0]
    api.get_last_trade(ticker.upper())
  except:
    print("Invalid ticker symbol: {0}".format(ticker))
    return
  try:
    price = float(args[1])
  except ValueError:
    print("Invalid price: {0}".format(args[1]))
    return
  try:
    qty = int(args[2])
  except ValueError:
    print("Invalid quantity: {0}".format(args[2]))
    return

  Positions[ticker] = [price, qty]

def removePosition(inpt):
  """
  removes a position from the global Positions list

  Params:
    inpt (String): should contain the ticker symbol for the position to remove
  """
  ticker = inpt
  try:
    del Positions[ticker]
  except:
    print("Invalid ticker symbol: {0}".format(ticker))
    return

def printPositions(inpt = None):
  """
  prints positions currently held and recorded in the Positions global

  Params:
    inpt (String): Optional argument for only printing positions for a single ticker
  """
  print("|{0:^10}|{1:^14}|{2:^10}|".format("Ticker", "Price", "Quantity"))
  print("|----------+--------------+----------|")
  if inpt == None:
    for key, value in Positions.items():
      ticker = key
      price = value[0]
      quantity = value[1]
      print("|{0:^10}|  {1:<10.4f}  |  {2:<6}  |".format(ticker, price, quantity))
  else:
    try:
      ticker = inpt
      price = Positions[ticker][0]
      quantity = Positions[ticker][1]
      print("|{0:^10}|  {1:<10.4f}  |  {2:<6}  |".format(ticker, price, quantity))
    except KeyError:
      print("No position with ticker {0} is being held".format(ticker))

def positionStatus(inpt = None):
  """
  gets the current profit/loss by dollar and percent for a position or all positions

  Params:
    inpt (String): Optional. Specifies which ticker to display the status of.
  """
  if inpt == None:
    for key, value in Positions.items():
      ticker = key
      price = value[0]
      quantity = value[1]
      livePrice = api.get_last_trade(ticker.upper()).price
      diff = livePrice - price
      pl = diff * quantity
      percent = pl / (price * quantity)
      print("|{0:^10}|{1:^10}|{2:^14}|{3:^12}|".format("Ticker", "Quantity", "P/L", "% Diff"))
      print("|----------+----------+--------------+------------|")
      print("|{0:^10}|  {1:<6}  |  ${2:<8.4f}   | {3:>8.4}% |".format(ticker, quantity, pl, percent))
  else:
    try:
      ticker = inpt
      price = Positions[ticker][0]
      quantity = Positions[ticker][1]
      livePrice = api.get_last_trade(ticker.upper()).price
      diff = livePrice - price
      pl = diff * quantity
      percent = pl / (price * quantity)
      print("|{0:^10}|{1:^10}|{2:^14}|{3:^12}|".format("Ticker", "Quantity", "P/L", "% Diff"))
      print("|----------+----------+--------------+------------|")
      print("|{0:^10}|  {1:<6}  |  ${2:<8.4f}   | {3:>8.4}% |".format(ticker, quantity, pl, percent))
    except KeyError:
      print("No Position with ticker {0} is being held".format(ticker))

def handlePosition(inpt):
  """
  takes input from TickerBell main input stream and distributes
  work across Position module functions.

  Params:
    inpt (String): contains the user input position commands
  """
  args = inpt.split(' ')
  cmd = args[0]
  if (cmd == "add"):
    updatePosition(inpt[4:])
  elif (cmd == "update"):
    if args[1] not in Positions:
      print("A position in stock {0} was not currently being held.".format(args[1]))
      print("Your update command has been changed to an add command.")
    updatePosition(inpt[7:])
  elif (cmd == "remove"):
    removePosition(inpt[7:])
  elif (cmd == "print"):
    if (len(args) == 1):
      printPositions()
    else:
      printPositions(inpt[6:])
  elif (cmd == "status"):
    if (len(args) == 1):
      positionStatus()
    else:
      positionStatus(inpt[7:])
  else:
    print("Invalid Position Command: {0}".format(cmd))
    return -1
