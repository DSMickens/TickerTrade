import yfinance as yf
import yahoo_fin.stock_info as si
import multiprocessing
import time
import sys
import threading
import TAlert
import TPosition
import TIO
import TInfo
import TRemote
import TConfig

def usage():
  """returns all usages of TickerBell"""
  return("""
  USAGE:
      alert create [ticker] [price] less/more (optional) on/off (optional)
      alert delete [ID/ticker]
      alert on/off [ID]
      alert print alerts/emails/numbers
      alert start/stop
      alert mode cli/email/text [on/off]
      alert email add/remove [address]
      alert phone add/remove [phone number] [carrier (spaces removed)]
      info data [ticker]
      info price [ticker] open/close (optional)
      info volume [ticker]
      io import/export [filename]
      position add/update [ticker] [price] [quantity]
      position remove [ticker]
      position print
      position status [ticker] (optional)
      remote on/off 
      help
      usage
      quit
  """)
  
def help():
  """returns help functions for all commands"""
  return("""
  ALERT:\n
      The alert command lets you manage alerts and the alert system.
  \n    CREATE\n
          create lets you create a brand new alert.
          It requires four parameters.\n
          ticker    - the ticker symbol for the stock you want to create an alert for
          price     - the price at which, if hit, the alert will go off
          less/more - the direction of price movement that will sound the alert
                    - ex. 'less' will cause the alert to go off if price is less
                      than or equal to the live stock price
                    - this is an optional argument that defaults to 'less'
          on/off    - the status of the alert. The alert will only occur if the status
                      is 'on'.
  \n    ON/OFF\n
          on/off lets you turn an alert on or off.
          It requires one parameter.\n
          ID    - the ID of the existing alert to be turned on or off
  \n    PRINT\n
          print lets you print out saved alerts, email addresses, or phone numbers.
          It requires one parameter.\n
          choice    - the data you want to print. Options: alerts, emails, or numbers
  \n    START/STOP\n
          start/stop lets you start or stop the alert system.
  \n    MODE\n
          mode lets you turn on or off different alert modes.
          It requires two parameters.\n
          mode      - the alert mode that you want to turn on/off.
                      Options: cli, email, text.
          on/off    - the status of the mode. The alert will be sent through this mode
                      only if the status is 'on
  \n    EMAIL\n
          email lets you add or remove an email to/from the alert system.
          It requires two parameters.\n
          add/remove    - whether you want to save or delete a saved email address
          address       - the email address to save or delete
  \n    PHONE\n
          phone lets you add or remove a phone number to/from the alert system.
          It requires three parameters.\n
          add/remove    - whether you want to save or delete a saved phone number
          phone number  - the phone number to save or delete
          carrier       - the service carrier for the phone number with all spaces removed
  
  INFO:\n
      The info command lets you get some info about specified stocks
  \n    PRICE\n
          price lets you get the price at certain times based on specified arguments
          It requires one parameter and has two optional parameters\n
          ticker - the ticker symbol of the stock to check
          open/close/extended - optional. If given, the price at the most recent open,
                                close, or current extended hours price will be given.
          diff - optional. Will show the difference between the chosen price and the price 
                 at the most recent open.
        VOLUME\n
          volume lets you get volume information for a stock
          It requires one parameter and has one optional parameter\n
          ticker - the ticker symbol of the stock to check.
          average - optional. Will return the average volume for this stock instead
                    of the current day's volume.
  
  IO:\n
      The io command lets you manage input/output with files
  \n    IMPORT/EXPORT\n
          import/export lets you resume/save current TickerBell system states.
          It requires one parameter.\n
          filename  - the name of the file to import from or export to

  POSITION:\n
      The position command lets you manage and check currently held positions.
  \n    ADD/UPDATE\n
          add/update lets you add a new position or update an existing position.
          It requires three parameters.\n
          ticker    - the ticker symbol for the stock
          price     - the average price per share being held
          quantity  - the number of shares purchased
  \n    REMOVE\n
          remove lets you remove a held position.
          It requires one parameter.\n
          ticker    - the ticker symbol for the stock
  \n    STATUS\n
          status lets you check the live status of your held positions.
          It has one optional parameter.\n
          ticker  - the ticker symbol for the stock. If no parameter is given,
                    then all position status's will be displayed

  REMOTE:\n
      The remote command lets you toggle on and off the remote access functionality.
      It requires one parameter.\n
      on/off - whether you want the remote functionality to be enabled or disabled.
        
  USAGE:\n
      The usage commands gives a format for how to use each of the other commands.

  QUIT:
      The quit command ends the current session.
  """)

def Banner():
  """returns the TickerBell welcome banner""" 
  return("""
           __________                          _____               
          |___    ___|                        |  _  \        _  _  
              |  | _   ___  _  __  ____   ___ | | | |  ____ | || | 
              |  ||_| / __|| |/ / / _  \ /   \| |_| / / _  \| || | 
              |  | _ | |   |   / | |_| || ||_||  _ | | |_| || || | 
              |  || || |   |   \ | ____|| |   | | | \| ____|| || | 
              |  || || |__ | |\ \| \___ | |   | |_| || \___ | || | 
              |__||_| \___||_| \_\\\____||_|   |_____/ \____||_||_|  
  """)
  
def checkQueue():
  """checkQueue continuously checks the queue for new messages"""
  while (1):
    time.sleep(3)
    if not TConfig.q.empty():
      event = TConfig.q.get()
      if event[0] == 'key':
        print("turning off alert")
        TAlert.toggleAlert(False, event[1])
      elif event == 'alert start':
        print("starting alert system")
        TAlert.startAlert()

def handleInput(inpt):
  """
  handles the user input line for stdin or from a file
  
  Params:
    inpt (String): user input line
    Return: fails if line can't be read in
  """
  args = inpt.split(' ')
  cmd = args[0]

  if ( cmd == "alert" ):
    if (TAlert.handleAlert(inpt[6:]) == -1):
      print(usage())
  elif ( cmd == "io" ):
    if (TIO.handleIO(inpt[3:]) == -1):
      print(usage())
  elif ( cmd == "help" ):
    print(help())
  elif ( cmd == "info" ):
    if (TInfo.handleInfo(inpt[5:]) == -1):
      print(usage())
  elif ( cmd == "usage" ):
    print(usage())
  elif ( cmd == "position" ):
    if (TPosition.handlePosition(inpt[9:]) == -1):
      print(usage())
  elif ( cmd == "remote" ):
    if (TRemote.handleRemote(inpt[7:]) == -1):
      print(usage())
  elif ( cmd != "quit" ):
    print("Invalid TickerBell Command: {0}".format(cmd))
    print(usage())
    return -1
    
def main():
  try:
    t = threading.Thread(target=checkQueue)
    t.daemon=True
    t.start()
            # Introduction Banner
    print(Banner())
            # Usage Report
    print(usage())
            # Input Prompt
    print(">> ", end = ' ')
            # Initial Input Received
    inpt = input().strip()
            # Input Loop
    while inpt != "quit":
            # Handle Input
      handleInput(inpt)
            # Input Reprompt
      print(">> ", end = ' ')
            # User Input
      inpt = input().strip()
            #Exit Message
    print("\nThank you for using TickerBell\n")
    return 0  
  except:
    type, value, traceback = sys.exc_info()
    print(type, value, traceback)
    return 1
if __name__ == "__main__":
    # execute only if run as a script
    exit(main())
