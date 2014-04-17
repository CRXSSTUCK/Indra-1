import json
from pprint import pprint

class AccountManager():
	def __init__(self):
		self.accounts = list()
	
	def __init__(self, accountsJsonPath):
		self.accounts = list()
		accounts = self.__parse_accounts_json(accountsJsonPath)
		
	def __parse_accounts_json(self, path):
		if path is None:
			raise Exception("path to accounts.json is None")
		self.accounts = list()
		accountsFile = open(path, "r")		
		data = json.load(accountsFile)
		pprint(data)
		accountsFile.close()
		accounts = data.accounts		

	def print_accounts(self):
		for acct in self.accounts:
			print "-=-" * 20
			pprint(account)
			
