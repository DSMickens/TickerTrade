import yfinance as yf
import yahoo_fin.stock_info as si
import smtplib
import ssl
import TickerBell
from multiprocessing import Process
from time import sleep, time
from random import seed
from random import randint
import TPasswords
from
import TConfig

#globals
alertProcess = None
alerts = {}
mode = {"cli":True, "email":False, "text":False}
emails = []
phoneNumbers = []
carriers = {"xfinity":"@vtext.com","verizon":"@vtext.com", "at&t":"@txt.att.net",
            "tmobile":"tmomail.net", "sprint":"@messaging.sprintpcs.com",
            "googlefi":"@msg.fi.google.com"}
def sendEmail(message, receiver):
  """
  sends a message from tickerbell email to a receiver

  Params:
    message is the email body
    receiver is the email address to send to
  """
  receiver = '9198969566@vtext.com'
  #set up server for email/text message
  port = 465
  password = 'T1ck3rB3ll'
  context = ssl.create_default_context()
  with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login(TPasswords.tickerbell_email, TPasswords.tickerbell_password)
    server.sendmail(TPasswords.tickerbell_email, receiver, message)

def checkAlerts(q):
  """
  Continuously checks a dictionary of specified alert stocks and prices
  and sends an alert via cli/email/text if the price of the stock is hit.

  Params:
    alerts (Dictionary{int:[string, float, bool, bool]}: a dictionary of stock alerts
  """
  def printAlert(ticker, price):
    """
    Prints/sends the alert message for the specified alert. The alert will be
    printed on the command line, and/or sent via email and/or text message based on the choices
    the user has previously made for the 'mode' global

    Params:
      value ([string, float, bool, bool]: a dictionary entry value for the alert
      price (float): the current price of the stock
    """
    #send out cli alert
    if (mode["cli"]):
      #create message for alert
      message ="""
      ******************************************
      *                 ALERT                  *
      *        {0:4}           ${1:<9.4f}      *
      ******************************************
      """.format(ticker, price)
      print(message)
      print(">>", end = ' ')
    #send out email alert to each email
    if (mode["email"]):
      message = """\
      From: TickerBell\nSubject: New TickerBell Alert\n\n

      You have 1 new TickerBell Alert!

      Ticker: {0}
      Price: ${1:.4f}
      """.format(ticker, price)
      for email in emails:
        sendEmail(message, email)
    #send out text alert to each number
    if (mode["text"]):
      message ="""
      You have 1 new TickerBell Alert!

      Ticker: {0}
      Price: ${1:.4f}
      """.format(ticker, price)
      for number in phoneNumbers:
        sendEmail(message, number)
  global alerts
  curtime = time()
  while (True):
    for key, value in alerts.items():
      #separate input arguments
      ticker = value[0]
      alertPrice = value[1]
      alertIsLess = value[2]
      alertIsOn = value[3]

      if alertIsOn:
        price = si.get_live_price(ticker)
        if alertIsLess:
          if (float("{:.4f}".format(price)) <= alertPrice):
            printAlert(ticker, price)
            alerts[key][3] = False
            TConfig.q.put(('key', key))
        else:
          if (float("{:.4f}".format(price)) >= alertPrice):
            printAlert(ticker, price)
            alerts[key][3] = False
            TConfig.q.put(('key', key))
        print(">> ", end = ' ')
    while time() <= (curtime + 2):
      sleep(2)
    curtime = time()

def deleteAlert(inpt):
  """
  deletes a specified alert from the dictionary of alerts by it's key, ID

  Params:
    inpt (string): the ID of the alert to delete
  """
  global alerts
  delete = []
  try:
    ID = int(inpt)
    del alerts[ID]
  except KeyError:
    print("ID: {0} does not exist".format(ID))
  except ValueError:
    foundAlert = False
    for key, value in alerts.items():
      if (value[0] == inpt):
        #cannot delete keys from dictionary while iterating, keep track and delete later
        delete.append(key)
    if len(delete) == 0:
      print("No alerts for ticker: {0} found".format(inpt))
    else:
      for key in delete:
        del alerts[key]

def createAlert(inpt):
  """
  Takes the alert command input and adds the fields to the alert dictionary

  Params:
    inpt (string): user input for creating alerts
  """
  #using global alerts
  global alerts

  #check if dictionary is max capacity (half of random numbers)
  if (len(alerts) == 50000):
    print("Dictionary Full!")
    return

  #seed random number generator, generate random ID
  seed(time())
  ID = randint(0,99999)
  while ID in alerts:
    ID = randint(0,99999)

  #split input
  args = inpt.split(' ')

  #default arguments
  isLess = True
  isOn = True
  
  #if number of arguments is not in the acceptable range of arguments, fail
  if (len(args) > 4 or len(args) < 2):
    print("Invalid number of input arguments: {0}".format(len(args)))
    return
  #if ticker symbol or price are invalid, fail
  try:
    yf.Ticker(args[0])
    ticker = args[0]
    price = float(args[1])
  except ValueError:
    print("Invalid price: {0}".format(args[1]))
    return
  except:
    print("Invalid ticker symbol: {0}".format(args[0]))
    return

  #if optional isLess argument is invalid, fail
  if (len(args) >= 3):
    isLessString = args[2].lower()
    if isLessString in ["more", "greater", "more than", "greater than", ">", ">="]:
      isLess = False
    elif isLessString not in ["less", "fewer", "fewer than", "less than", "<", "<="]:
      print("Invalid argument: {0}".format(isLessString))
      return

  #if optional isOn argument is invalid, fail
  if (len(args) == 4):
    isOnString = args[3].lower()
    if (isOnString == "off"):
      isOn = False
    elif (isOnString != "on"):
      print("Invalid argument: {0}".format(isOnString))
      return

  #create the alert entry in the dictionary
  alerts[ID] = [ticker, price, isLess, isOn]

def startAlert():
  """Begins a new process to run and check for alerts constantly."""
  global alertProcess
  global alerts
  if len(alerts) == 0:
    print("No alerts have been made. .")
  alertProcess = Process(target=checkAlerts, args = (TConfig.q,))
  alertProcess.daemon=True
  alertProcess.start()

def stopAlert():
  """Terminates the alertProcess."""
  global alertProcess
  if alertProcess is not None:
    alertProcess.terminate()
    alertProcess = None
  else:
    print("Alert System not currently running")

def toggleAlert(status, inpt):
  """
  Turns an existing alert on or off

  Params:
    status (boolean): True if alert should be on, False if not
    inpt (string): input string containing the ID of the alert to change
  """
  global alerts
  try:
    ID = int(inpt)
    if (status):
      alerts[ID][3] = True
    else:
      alerts[ID][3] = False
  except ValueError:
    print("Invalid ID: {0}. Use 'alert print alerts' to check IDs.".format(inpt))
  except KeyError:
    print("No alert with ID: {0} Use 'alert print alerts' to check IDs.".format(ID))

def setEmail(inpt):
  """
  Adds or removes an email from the global mailing list for alerts

  Params:
    inpt (String): User input containing the add/remove specifier and the email address to add/remove
  """
  args = inpt.split(' ')
  addOrRemove = args[0]
  email = args[1]
  if (len(args) != 2):
    print("Invalid number of arguments: {0}".format(len(args)))
    return
  if addOrRemove == "add":
    emails.append(email)
  elif addOrRemove == "remove":
    for item in emails:
      if item == email:
        emails.remove(item)
        return
    print("That email has not been saved")
    return

def setPhone(inpt):
  """
  Adds or removes a phone number from the global list of contact numbers

  Params:
    inpt (String): User input containing the add/remove specifier, the phone number, and the carrier
  """
  global carriers
  args = inpt.split(' ')
  addOrRemove = args[0]
  try:
    number = args[1]
    carrier = carriers[args[2]]
  except ValueError:
    print("Invalid number: ".format(args[1]))
    return
  except KeyError:
    print("Invalid carrier: ".format(args[2]))
    return
  if (len(args) != 3):
    print("Invalid number of arguments: {0}".format(args.len()))
    return
  if (addOrRemove == "add"):
    phoneNumbers.append(number + carrier)
  elif (addOrRemove == "remove"):
    try:
      phoneNumbers.remove(number + carrier)
    except ValueError:
      print("That phone number has not been saved")
      return

def setAlertMode(inpt):
  """
  turns on or off the cli/email/text alert modes

  Params:
    inpt (String): user input for alert mode specifiers
  """
  args = inpt.split(' ')
  inputMode = args[0].lower()
  isOn = args[1]
  if (inputMode == "cli"):
    if (isOn == "on"):
      mode["cli"] = True
    if (isOn == "off"):
      mode["cli"] = False
  elif (inputMode == "text"):
    if (isOn == "on"):
      mode["text"] = True
    if (isOn == "off"):
      mode["text"] = False
  elif (inputMode == "email"):
    if (isOn == "on"):
      mode["email"] = True
    if (isOn == "off"):
      mode["email"] = False

def printer(inpt):
  """
  prints specified alerts, emails, or phone numbers

  Params
    inpt (String) - user input for printing specifications
  """

  def printAlerts():
    """ Prints contents of dictionary param (alerts) in a easy to read format"""
    global alerts
    print("|   {0}   | {1} |    {2}    | {3} |".format("ID", "Ticker", "Trigger", "Status"))
    print("|--------+--------+---------------+--------|")
    for key, value in alerts.items():
      ticker = value[0]
      price = value[1]
      operator = "<=" if value[2] else ">="
      status = "on" if value[3] else "off"
      print("| {0:<6d} |  {1:<4}  |  {2} {3:<9.4f} |  {4:>3}   |".format(key, ticker, operator, price, status))

  def printEmails():
    """Prints currently saved email addresses"""
    global emails
    for email in emails:
      print(email)

  def printPhoneNumbers():
    """Prints currently saved phone numbers"""
    global phoneNumbers
    for phone in phoneNumbers:
      number = phone.split('@')
      print(number[0])

  if (inpt == "alerts"):
    printAlerts()
  elif (inpt == "emails"):
    printEmails()
  elif (inpt == "numbers"):
    printPhoneNumbers()
  else:
    print("Invalid selection: {0}".format(inpt))

def handleAlert(inpt):
  """
  takes input from TickerBell main input stream and distributes
  work across Alert module functions.

  Params:
    inpt (String) - input for the alert function
  """
  global alerts
  args = inpt.split(' ')
  cmd = args[0]

  if cmd == "print":
    printer(inpt[6:])
  elif cmd == "create":
    createAlert(inpt[7:])
  elif cmd == "start":
    if alertProcess is not None:
      print("You must stop an existing alert system before starting a new one")
    else:
      startAlert()
  elif cmd == "stop":
    stopAlert()
  elif cmd == "delete":
    deleteAlert(inpt[7:])
  elif cmd == "on":
    toggleAlert(True, inpt[3:])
  elif cmd == "off":
    toggleAlert(False, inpt[4:])
  elif cmd == "mode":
    setAlertMode(inpt[5:])
  elif cmd == "email":
    setEmail(inpt[6:])
  elif cmd == "phone":
    setPhone(inpt[6:])
  else:
    print("Invalid Alert Command: {0}".format(inpt))
    return -1
