'''
Created on Apr 20, 2015

@author: talbpaul
'''
#for future compatibility with Python 3--------------------------------------------------------------
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)
if not 'xrange' in dir(__builtins__):
  xrange = range
#End compatibility block for Python 3----------------------------------------------------------------

#External Modules------------------------------------------------------------------------------------
import platform
import os
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
import utils
#Internal Modules End--------------------------------------------------------------------------------

# set a global variable for backend default setting
if platform.system() == 'Windows': disAvail = True
else:
  if os.getenv('DISPLAY'): disAvail = True
  else:                    disAvail = False

#custom exceptions
class NoMoreSamplesNeeded(GeneratorExit): pass

class MessageUser(object):
  """
    Inheriting from this class grants access to methods used by the message handler.
  """
  def raiseAnError(self,etype,message,tag='ERROR',verbosity='silent'):
    """
      Raises an error. By default shows in all verbosity levels.
      @ In, etype, Exception class to raise (e.g. IOError)
      @ In, message, the message to display
      @ OPTIONAL In, tag, the printed error type (default ERROR)
      @ OPTIONAL In, verbosity, the print priority of the message (default 'silent', highest priority)
      @ Out, None
    """
    self.messageHandler.error(self,etype,str(message),str(tag),verbosity)

  def raiseAWarning(self,message,tag='Warning',verbosity='quiet'):
    """
      Prints a warning. By default shows in 'quiet', 'all', and 'debug'
      @ In, message, the message to display
      @ OPTIONAL In, tag, the printed warning type (default Warning)
      @ OPTIONAL In, verbosity, the print priority of the message (default 'quiet')
      @ Out, None
    """
    self.messageHandler.message(self,str(message),str(tag),verbosity)

  def raiseAMessage(self,message,tag='Message',verbosity='all'):
    """
      Prints a message. By default shows in 'all' and 'debug'
      @ In, message, the message to display
      @ OPTIONAL In, tag, the printed message type (default Message)
      @ OPTIONAL In, verbosity, the print priority of the message (default 'all')
      @ Out, None
    """
    self.messageHandler.message(self,str(message),str(tag),verbosity)

  def raiseADebug(self,message,tag='DEBUG',verbosity='debug'):
    """
      Prints a debug message. By default shows only in 'debug'
      @ In, message, the message to display
      @ OPTIONAL In, tag, the printed message type (default DEBUG)
      @ OPTIONAL In, verbosity, the print priority of the message (default 'debug')
      @ Out, None
    """
    self.messageHandler.message(self,str(message),str(tag),verbosity)

  def getLocalVerbosity(self,default=None):
    """
      Attempts to learn the local verbosity level of itself
      @ OPTIONAL In, default, the verbosity level to return if not found
      @ Out, string, verbosity type (e.g. 'all')
    """
    try: return self.verbosity
    except AttributeError: return default


class MessageHandler(MessageUser):
  """
  Class for handling messages, warnings, and errors in RAVEN.  One instance of this
  class should be created at the start of the Simulation and propagated through
  the readMoreXML function of the BaseClass.  The utils handlers for raiseAMessage,
  raiseAWarning, raiseAnError, and raiseDebug will access this handler.
  """
  def __init__(self):
    """
      Init of class
      @In, None
      @Out, None
    """
    self.printTag     = 'MESSAGE HANDLER'
    self.verbosity    = None
    self.suppressErrs = False
    self.verbCode     = {'silent':0, 'quiet':1, 'all':2, 'debug':3}

  def initialize(self,initDict):
    """
      Initializes basic instance attributes
      @ In, initDict, dictionary of global options
      @ Out, None
    """
    self.verbosity     = initDict['verbosity'   ] if 'verbosity'    in initDict.keys() else 'all'
    self.callerLength  = initDict['callerLength'] if 'callerLength' in initDict.keys() else 25
    self.tagLength     = initDict['tagLength'   ] if 'tagLength'    in initDict.keys() else 15
    self.suppressErrs  = initDict['suppressErrs'] in utils.stringsThatMeanTrue() if 'suppressErrs' in initDict.keys() else False

  def getStringFromCaller(self,obj):
    """
      Determines the appropriate print string from an object
      @ In, obj, preferably an object with a printTag method; otherwise, a string or an object
      @ Out, tag, string to print
    """
    if type(obj) in [str,unicode]: return obj
    try: obj.printTag
    except AttributeError: tag = str(obj)
    else: tag = str(obj.printTag)
    return tag

  def getDesiredVerbosity(self,caller):
    """
      Tries to use local verbosity; otherwise uses global
      @ In, caller, the object desiring to print
      @ Out, integer, integer equivalent to verbosity level
    """
    localVerb = caller.getLocalVerbosity(default=self.verbosity)
    if localVerb == None: localVerb = self.verbosity
    return self.checkVerbosity(localVerb) #self.verbCode[str(localVerb).strip().lower()]

  def checkVerbosity(self,verb):
    """
      Converts English-readable verbosity to computer-legible integer
      @ In, verb, the string verbosity equivalent
      @ Out, integer, integer equivalent to verbosity level
    """
    if str(verb).strip().lower() not in self.verbCode.keys():
      raise IOError('Verbosity key '+str(verb)+' not recognized!  Options are '+str(self.verbCode.keys()+[None]),'ERROR','silent')
    return self.verbCode[str(verb).strip().lower()]

  def error(self,caller,etype,message,tag='ERROR',verbosity='silent'):
    """
      Raise an error message, unless errors are suppressed.
      @ In, caller, the entity desiring to raise an error
      @ In, etype, the type of error to throw
      @ In, message, the accompanying message for the error
      @ OPTIONAL In, tag, the printed error type (default ERROR)
      @ OPTIONAL In, verbosity, the print priority of the message (default 'silent', highest priority)
      @ Out, None
    """
    verbval = self.checkVerbosity(verbosity)
    okay,msg = self._printMessage(caller,message,tag,verbval)
    if okay:
      if not self.suppressErrs: raise etype(msg)
      else: print(msg)

  def message(self,caller,message,tag,verbosity):
    """
      Print a message
      @ In, caller, the entity desiring to print a message
      @ In, message, the message to print
      @ In, tag, the printed message type (usually Message, Debug, or Warning, and sometimes FIXME)
      @ In, verbosity, the print priority of the message
      @ Out, None
    """
    verbval = self.checkVerbosity(verbosity)
    okay,msg = self._printMessage(caller,message,tag,verbval)
    if okay: print(msg)

  def _printMessage(self,caller,message,tag,verbval):
    """
      Checks verbosity to determine whether something should be printed, and formats message
      @ In, caller, the entity desiring to print a message
      @ In, message, the message to print
      @ In, tag, the printed message type (usually Message, Debug, or Warning, and sometimes FIXME)
      @ In, verbval, the print priority of the message
      @ Out, bool, indication if the print should be allowed
      @ Out, msg, the formatted message
    """
    #allows raising standardized messages
    shouldIPrint = False
    desired = self.getDesiredVerbosity(caller)
    if verbval <= desired: shouldIPrint=True
    if not shouldIPrint: return False,''
    ctag = self.getStringFromCaller(caller)
    msg=self.stdMessage(ctag,tag,message)
    return shouldIPrint,msg

  def stdMessage(self,pre,tag,post):
    """
      Formats string for pretty printing
      @ In, pre, string of who is printing the message
      @ In, tag, the type of message being printed (Error, Warning, Message, Debug, FIXME, etc)
      @ In, post, the actual message body
      @ Out, string, formatted message
    """
    msg = ''
    msg+=pre.ljust(self.callerLength)[0:self.callerLength] + ': '
    msg+=tag.ljust(self.tagLength)[0:self.tagLength]+' -> '
    msg+=post
    return msg
