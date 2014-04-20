from __future__ import absolute_import

from random import randint, choice

import HTMLParser
import getopt
import os

import sys
import traceback
import time
import urllib2

sys.path.append(os.path.join(os.path.dirname(__file__), "pkg"))

from bingAuth import BingAuth, AuthenticationError
from bingRewards import BingRewards
from config import BingRewardsReportItem, Config, ConfigError
import bingCommon
import bingFlyoutParser as bfp
import helpers

_report = list()

def earnRewards(httpHeaders, reportItem, password, config):
	print "earnRewards()"
	try:
		if reportItem is None: raise ValueError("reportItem is None")
		if reportItem.accountType is None: raise ValueError("reportItem.accountType is None")
		if reportItem.accountLogin is None: raise ValueError("reportItem.accountLogin is None")
		if password is None: raise ValueError("password is None")
		
		print "earnRewards, begining rewards"
		bingRewards = BingRewards(httpHeaders, config)
		print "calling bing auth ", bingRewards.opener
		bingAuth	= BingAuth(httpHeaders, bingRewards.opener)
		print "calling bingAuth.auth "
		bingAuth.authenticate(reportItem.accountType, reportItem.accountLogin, password)
		print "auth complete"
		reportItem.oldPoints = bingRewards.getRewardsPoints()
		print "old points: ", reportItem.oldPoints
		rewards = bfp.parseFlyoutPage(bingRewards.requestFlyoutPage(), bingCommon.BING_URL)
		print "parsed flyout page"
		print "bing rewards.process"
		results = bingRewards.process(rewards)
		
		print "bingrewards.printResults"
		bingRewards.printResults(results, True)

		reportItem.newPoints = bingRewards.getRewardsPoints()
		reportItem.lifetimeCredits = bingRewards.getLifetimeCredits()
		reportItem.pointsEarned = reportItem.newPoints - reportItem.oldPoints
		reportItem.pointsEarnedRetrying += reportItem.pointsEarned
		print
		print "%s - %s" % (reportItem.accountType, reportItem.accountLogin)
		print
		print "Points before:	%6d" % reportItem.oldPoints
		print "Points after:	 %6d" % reportItem.newPoints
		print "Points earned:	%6d" % reportItem.pointsEarned
		print "Lifetime Credits: %6d" % reportItem.lifetimeCredits
		print
		print "-" * 80

	except AuthenticationError, e:
		reportItem.error = e
		print "AuthenticationError:\n%s" % e

	except HTMLParser.HTMLParseError, e:
		reportItem.error = e
		print "HTMLParserError: %s" % e

	except urllib2.HTTPError, e:
		reportItem.error = e
		print "The server couldn't fulfill the request."
		print "Error code: ", e.code

	except urllib2.URLError, e:
		reportItem.error = e
		print "Failed to reach the server."
		print "Reason: ", e.reason

	except Exception, e:
		print "earnRewards exception, possibly login issue withaccount: ", reportItem.accountLogin
		print "message: ", e

		for frame in traceback.extract_tb(sys.exc_info()[2]):
		    fname,lineno,fn,text = frame
		    print "Error in %s on line %d" % (fname, lineno)
   	finally:
		print
		print "For: %s - %s" % (reportItem.accountType, reportItem.accountLogin)
		print
		print "-" * 80

def __stringifyAccount(reportItem, strLen):
	if strLen < 15:
		raise ValueError("strLen too small. Must be > " + 15)

	s = ""
	if reportItem.accountType == "Facebook":
		s += " fb "
	elif reportItem.accountType == "Live":
		s += "live"
	else:
		raise ValueError("Account type (" + reportItem.accountType + ") is not supported")

	s += " - "

	l = strLen - len(s)

	if len(reportItem.accountLogin) < l:
		s += reportItem.accountLogin
	else:
		s += reportItem.accountLogin[:(l - 3)]
		s += "..."

	return s

##############################################################################
###### ReportItem __process_account ( Account account, Config cfg ) ######
##### Parameters - Account, the current account that should be processed
# cfg, the Config() to use while processing the account
#### Returns - ReportItem, report generated durring account processing
##############################################################################
# Function is controller of the account processing process, it drives earning 
# rewards, managing setup and tear down, retrys, report generation, etc.
##############################################################################
def __process_account(account, cfg):
	print "__processAccount(): "	
	
	# generate report item for later use
	reportItem = BingRewardsReportItem(account)
	
	# generate headers for http requests (including spoofed agent string) 
	httpHeaders = __generate_headers() # #$REFACTOR_HTTP$#
	
	#earn the rewards
	earnRewards(httpHeaders, reportItem, account.password, cfg)
	
	#if the earning was not successful, sleep and recurse
	if reportItem.error is not None:
		# we have to keep retry count; and other things, correct...
		print "__process_acount(): process failure, ", reportItem.retries, \
		" attempts made"			
		reportItem.retries += 1
		reportItem.accountStatus = 1
	else:
		reportItem.accountStatus = 0
		
	return reportItem 

##############################################################################
###### string __generate_headers ( ) ######
##### Parameters - 
#### Returns - string, the HTTPHeaderString to use for client connections
##############################################################################
# Function is simple helper to grab a random user agent from bingCommon def's
# should be moved into a HTTPHelpers area later on. #$REFACTOR_HTTP$#
##############################################################################
def __generate_headers():
	print "__generate_headers()"
	httpHeaders = bingCommon.HEADERS
	userAgentString = choice(bingCommon.USER_AGENTS_PC)
	httpHeaders["User-Agent"] = userAgentString
	print "__generate_headers(): userAgentString = ", userAgentString
	return httpHeaders

##############################################################################
###### int __run ( Config cfg ) ######
##### Parameters - Config, class contains info and methods for program state
#### Returns - int, the number of accounts that were successfully ran
##############################################################################
# Function is the running loop for account persecution, it iterates through
# all accounts in the config, and causes each to earn rewards if possible
# it returns the number of accounts that it was able to successfully process
# a successful account process is one that does not result in exceptions :)
##############################################################################
def __run(cfg):
	print "__run(Config): ", cfg

	# get the accounts to run
	accounts = cfg.accounts
	accountCounter = 0
	
	# randomly skip through the accounts list so as not to raise suspicions
	while len(accounts) > 0:
		# pick a random account to process
		key = choice(accounts.keys())
		currentAccount = accounts[key]
		print "-" * 40
		print "__run(): currentAccount = ", currentAccount.getRef(), 
		print
								
		# process the account
		print "processing account "
		reportItem = __process_account(currentAccount, cfg)
		
		accountStatus = reportItem.accountStatus
		print "account processed, accountstatus = ", accountStatus		
		
		# if the account does not require a retry, delete it from the dict 
		if accountStatus != 0:
			print "deleting: ", key, " from the account dict"
			del accounts[key]
			accountCounter += 1

		# add report item to report
		print "account processed, appending reportItem to reports"
		_report.append(reportItem)
				
		# sleep with jitter for more confusion >:)
		secs = cfg.general.getSleepBetweenAccounts()
		print "sleeping between accounts for ", secs, " seconds"
		time.sleep(secs)
		print "__run(): looping, ", len(accounts), " accounts left"
######## EOL

	helpers.printAccountReport(_report)
	
	return accountCounter
	
###############################################################################
### Main entry point for Indra 
###############################################################################
if __name__ == "__main__":	

	cf = os.path.join(os.path.dirname(__file__), "config.xml")	
	cfg = Config()
	
	try:
		cfg.parseFromFile(cf)
	except IOError, e:
		print "IOError: %s" % e
		sys.exit(2)
	except ConfigError, e:
		print "ConfigError: %s" % e
		sys.exit(2)
	except Exception, r:
		print "Unknown exception in config.from_file(): ", r
		sys.exit(2)

	try:
		__run(cfg)
	except BaseException, e:
		print "Error: Main: ", BaseException, " Message: ", e
		for frame in traceback.extract_tb(sys.exc_info()[2]):
		    fname,lineno,fn,text = frame
		    print "Error in %s on line %d" % (fname, lineno)
