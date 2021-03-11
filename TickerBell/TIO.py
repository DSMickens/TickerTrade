import TickerBell
import TAlert
import TPosition

def importState(filename):
  """
  imports a saved state from an import file. Uses
  normal TickerBell commands to import file

  Params:
    filename (String): the name of the import file
  """
  try:
    fp = open(filename)
  except:
    print(sys.exec_info())
    print("Could not open file: {0}".format(filename))
    return

  for line in fp:
    line = line.strip()
    TickerBell.handleInput(line)

  fp.close()

def exportState(filename):
  """
  exports the current state into an export file. Produces a file
  with TickerBell commands to enable importing later.

  Params:
    filename (String): the name of the export file
  """
  try:
    fp = open(filename, 'w')
  except:
    print(sys.exec_info())
    print("Could not open file: {0}".format(filename))
    return

  #exporting alerts
  for key, value in TAlert.alerts.items():
    ticker = value[0]
    price = value[1]
    trigger = "less" if value[2] else "more"
    status = "on" if value[3] else "off"
    fp.write("alert create {0} {1} {2} {3}\n".format(ticker, price, trigger, status))

  #exporting mode status
  for key, value in TAlert.mode.items():
    mode = key
    status = "on" if value else "off"
    fp.write("alert mode {0} {1}\n".format(mode, status))

  #exporting emails
  for email in TAlert.emails:
    fp.write("alert email add {0}\n".format(email))

  numbers = []
  #exporting phone Numbers
  for phone in TAlert.phoneNumbers:
    address = phone.split('@')
    number = address[0]
    if number not in numbers:
      numbers.append(number)
      gate = "@" + address[1]
      carrier = None
      for key, value in TAlert.carriers.items():
        if gate == value:
          carrier = key
      if (carrier is not None):
        fp.write("alert phone add {0} {1}\n".format(number, carrier))

  #exporting Positions
  for key, value in TPosition.Positions.items():
    ticker = key
    price = value[0]
    quantity = value[1]
    fp.write("position add {0} {1} {2}\n".format(ticker, price, quantity))

  fp.close()

def handleIO(inpt):
  """
  parses user input and distributes work over TIO functions

  Params:
    inpt (String): user input commands
  """
  args = inpt.split(' ')
  cmd = args[0]
  if len(args) != 2:
    print("Invalid number of arguments")
    return -1
  filename = args[1]
  if (cmd == "import"):
    importState(filename)
  elif (cmd == "export"):
    exportState(filename)
  else:
    print("Invalid IO Command: {0}".format(inpt))
    return -1
