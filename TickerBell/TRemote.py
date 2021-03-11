import TickerBell
import TAlert
import TConfig
import TPasswords
import imaplib
from multiprocessing import Process
import email
from email.header import decode_header
from time import sleep
from io import StringIO
import sys
import os

remoteAccess = None

def handleEmailAttachment(filename):
  """
  if a email is determined to be multipart then this function will be called to handle
  the commands within the attached .txt file

  Params:
    filename is the name of the attached file
  Return:
    a list of commands
  """
  if not filename.endswith('.txt'):
    return None
  commands = []
  fp = open(filename, "r")
  for line in fp:
    line = line.lower().strip()
    commands.append(line)
  return commands

def checkEmail(q):
  """process start function to repeatedly look into an email inbox for new emails"""
  username = TPasswords.tickerbell_email
  password = TPasswords.tickerbell_email_pw
  imap = imaplib.IMAP4_SSL("imap.gmail.com", '993')
  imap.login(username, password)
  while (1):
    status, messageCount = imap.select("INBOX")
    if status != 'OK':
      print("Could not connect to gmail inbox")
      return

    #get IDs of unread emails and put into a list named IDs
    #IDs SHOULD be in order oldest to newest
    status, IDs = imap.search(None, 'UnSeen')
    IDs = IDs[0].split()
    if len(IDs) > 0:
    for i, ID in enumerate(IDs):
      #IDs is now a list of ID strings
      IDs[i] = ID.decode('utf-8')
    for ID in IDs:
      status, msg = imap.fetch(ID, "(RFC822)")
      if status != 'OK':
        print("Email {0} could not be retrieved.".format(ID))
      else:
       #### https://www.thepythoncode.com/article/reading-emails-in-python ####
        for response in msg:
          if isinstance(response, tuple):
            # parse a bytes email into a message object
            msg = email.message_from_bytes(response[1])
            # decode the email subject
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
              # if it's a bytes, decode to str
              subject = subject.decode()
            # email sender
            from_ = msg.get("From")
            from_ = from_.split()
            from_ = from_[len(from_)-1].strip('<>')
            return_username = from_.split('@')[0]
            address = from_.split('@')[1]
            #AUTHORIZING RECIPIENT
            if from_ not in TAlert.emails and from_ not in TAlert.phoneNumbers:
                print("Email sender {0} invalid personnel".format(from_))
                break
            commands = []
            if msg.is_multipart():
              # iterate over email parts
              for part in msg.walk():
                # extract content type of email
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                try:
                  # get the email body
                  body = part.get_payload(decode=True).decode()
                except:
                  pass
                if content_type == "text/plain" and "attachment" not in content_disposition:
                  # print text/plain emails and skip attachments
                  for line in body.splitlines():
                    commands.append(line)
                elif "attachment" in content_disposition:
                  # download attachment
                  filename = part.get_filename()
                  if filename:
                      filepath = os.path.join(os.getcwd(), filename)
                      # download attachment and save it
                      open(filepath, "wb").write(part.get_payload(decode=True))
                      commands = handleEmailAttachment(filename)
                      os.remove(filepath)
            else:
              # extract content type of email
              content_type = msg.get_content_type()
              # get the email body
              body = msg.get_payload(decode=True).decode()
              if content_type == "text/plain":
                # print only text email parts
                for line in body.splitlines():
                  commands.append(line.lower().strip())
            #redirect stdout temporarily
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            for command in commands:
              if command == "alert start":
                q.put(('alert start'))
              elif command not in ["alert start", "remote on", "quit"]:
                TickerBell.handleInput(command)
            sys.stdout = old_stdout
            message = mystdout.getvalue()
            if from_ in TAlert.emails:
                TAlert.sendEmail(message, receiver)
            else:
              for i in range(0, int(len(message) / 160)):
                start = i * 160
                end = start + 159
                TAlert.sendEmail(message[start:end], from_)
    sleep(2)
  imap.close()
  imap.logout()

def startRemote():
  """creates and runs the child process responsible for handling remote access"""
  remoteAccess = Process(target=checkEmail, args=(TConfig.q,))
  remoteAccess.daemon=True
  remoteAccess.start()

def handleRemote(inpt):
  """
  handles remote command input and distributes work to TRemote functions.

  Params:
    inpt (String) - remote command user input
  """
  if (inpt == "on"):
    startRemote()
  elif (inpt == "off"):
    if remoteAccess is not None:
      remoteAccess.terminate()
  else:
    print("Invalid Remote Command: {0}".format(inpt))
    return -1
