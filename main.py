from __future__ import absolute_import

from random import randint, choice

import getopt
import os

import sys
import traceback
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "pkg/account"))
from account import Account
from account_manager import AccountManager


###############################################################################
### Main entry point for Indra 
###############################################################################
if __name__ == "__main__":	

	try:
		cf = os.path.join(os.path.dirname(__file__), "config/accounts.json")	
		print cf
		
		acctMgr = AccountManager(cf)
		
		acctMgr.print_accounts()
		
	except Exception, e:		
		print "Error: Main: ", Exception, " Message: ", e
		for frame in traceback.extract_tb(sys.exc_info()[2]):
		    fname,lineno,fn,text = frame
		    print "Error in %s on line %d" % (fname, lineno)
		
