

import logging
import colorama as clr

import threading
import os.path
import sys
import time
import traceback
# Pylint can't figure out what's in the record library for some reason
#pylint: disable-msg=E1101

LOGGING_CONFIGURED = False

def checkInit():
	global LOGGING_CONFIGURED
	if LOGGING_CONFIGURED:
		return False

	LOGGING_CONFIGURED = True
	return True


colours = [clr.Fore.BLUE, clr.Fore.RED, clr.Fore.GREEN, clr.Fore.YELLOW, clr.Fore.MAGENTA, clr.Fore.CYAN, clr.Back.YELLOW + clr.Fore.BLACK, clr.Back.YELLOW + clr.Fore.BLUE, clr.Fore.WHITE]

def getColor(idx):
	return colours[idx%len(colours)]

class ColourHandler(logging.Handler):

	def __init__(self, level=logging.DEBUG):
		logging.Handler.__init__(self, level)
		self.formatter = logging.Formatter('\r%(name)s%(padding)s - %(style)s%(levelname)s - %(message)s'+clr.Style.RESET_ALL)
		clr.init()

		self.logPaths = {}

	def emit(self, record):

		# print record.levelname
		# print record.name

		segments = record.name.split(".")
		tname = threading.current_thread().name
		segments.append(tname)
		if segments[0] == "Main" and len(segments) > 1:
			segments.pop(0)
			segments[0] = "Main."+segments[0]

		nameList = []

		for indice, pathSegment in enumerate(segments):
			if not indice in self.logPaths:
				self.logPaths[indice] = [pathSegment]
			elif not pathSegment in self.logPaths[indice]:
				self.logPaths[indice].append(pathSegment)

			name = clr.Style.RESET_ALL
			name += getColor(self.logPaths[indice].index(pathSegment))
			name += pathSegment
			name += clr.Style.RESET_ALL
			nameList.append(name)


		record.name = ".".join(nameList)

		if record.levelname == "DEBUG":
			record.style = clr.Style.DIM
		elif record.levelname == "WARNING":
			record.style = clr.Style.BRIGHT
		elif record.levelname == "ERROR":
			record.style = clr.Style.BRIGHT+clr.Fore.RED
		elif record.levelname == "CRITICAL":
			record.style = clr.Style.BRIGHT+clr.Back.BLUE+clr.Fore.RED
		else:
			record.style = clr.Style.NORMAL

		record.padding = ""


		sys.stdout.write("\r")
		sys.stdout.write(self.format(record))
		sys.stdout.write("\n")
		sys.stdout.flush()

class RobustFileHandler(logging.FileHandler):
	"""
	A handler class which writes formatted logging records to disk files.
	"""



	def emit(self, record):
		"""
		Emit a record.

		If the stream was not opened because 'delay' was specified in the
		constructor, open it before calling the superclass's emit.
		"""
		failures = 0
		while self.stream is None:
			try:
				self.stream = self._open()
			except:

				time.sleep(1)
				if failures > 3:
					traceback.print_exc()
					print("Cannot open log file?")
					return
				failures += 1
		failures = 0
		while failures < 3:
			try:
				logging.StreamHandler.emit(self, record)
				break
			except:
				failures += 1
		else:
			traceback.print_stack()
			print("Error writing to file?")


		self.close()


def exceptHook(exc_type, exc_value, exc_traceback):
	if issubclass(exc_type, KeyboardInterrupt):
		sys.__excepthook__(exc_type, exc_value, exc_traceback)
		return
	mainLogger = logging.getLogger("Main")			# Main logger
	mainLogger.critical('Uncaught exception!')
	mainLogger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))



def initLogging(logLevel=logging.INFO):

	mainLogger = logging.getLogger("Main")			# Main logger
	mainLogger.setLevel(logLevel)

	if not checkInit():
		print("Logger already initialized")
		return
	else:

		ch = ColourHandler()
		mainLogger.addHandler(ch)

	print("Setting up loggers....")


	logName	= "Error - %s.txt" % (time.strftime("%Y-%m-%d %H;%M;%S", time.gmtime()))
	if not os.path.exists("./logs"):
		os.mkdir("./logs")
	errLogHandler = RobustFileHandler(os.path.join("./logs", logName))
	errLogHandler.setLevel(logging.WARNING)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	errLogHandler.setFormatter(formatter)

	mainLogger.addHandler(errLogHandler)

	# Install override for excepthook, to catch all errors
	sys.excepthook = exceptHook

	print("done")
	return errLogHandler
