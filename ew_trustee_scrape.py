## Python script to scrape trustee data
## of English & Welsh charities from the Charity Commission's beta website

# Diarmuid McDonnell, Tom Wallace
# Created: 08 October 2018
# Last edited: captured in Github file history


import csv
import requests
import os
import os.path
import errno
import zipfile
import io
from time import sleep
import random
import pandas as pd

from bs4 import BeautifulSoup

from downloaddate_function import downloaddate


# ==========================================================

# ==========================================================

# Define project and data paths

projpath = 'C:/Users/mcdonndz-local/Desktop/github/ew_charity_data/'
rawdatapath = 'C:/Users/mcdonndz-local/Desktop/data/ew_charity_data/data_raw/'

inputfile = rawdatapath + '/ew_charlist.csv'
ofile_json = rawdatapath + '/ew_trustees_info.json'
ofile_csv = rawdatapath + '/ew_trustees_info.csv'

# Open the input csv file in 'read' mode

with open(inputfile, 'r', newline='') as incsv: # I took out the following argument: , encoding='utf-8'
	reader = csv.reader(incsv)

	# Create a dictonary and add dummy values

	dicto_json = {'Charity Number': '0000000', 'Trustee Name':'John Doe', 'Other trusteeships': 'Nope', 'Other trusteeships link': 'http://fakelink.com'}

	for regno, name in reader: 
		webadd = 'http://beta.charitycommission.gov.uk/charity-details/?regid=' + regno + '&subid=0'
		rorg = requests.get(webadd)
		print(webadd, ' | ', rorg.status_code)

		html_org = rorg.text
		soup_org = BeautifulSoup(html_org, 'html.parser')
		boardinfo = soup_org.find("div", class_="detail-75") # Scrape the whole pnalle
		boardinfo = boardinfo.find_all('div', class_='item-row') # Find all the rows and store them as a list
		del boardinfo[0] # Delete the top line which is the headers

		trustee = list(map(lambda x : x.find('div', class_='trustee-name'), boardinfo)) # The name is in it's own tag so easy to find, map/lambda applies something to every item in a list
		trustee = list(map(lambda x : x.text, trustee)) # Extract the text

		otherboard = list(map(lambda x : x.find('div', class_='trustee-charity-name'), boardinfo)) # This line just says for every item in the list find the tag with the networking links
		other_trusteeships = list(map(lambda x : x.text, otherboard)) # Extract the text
		other_trusteeships = list(map(lambda x : x.replace('\t',''), other_trusteeships)) #These three lines just remove the white space, t is tab, n is newline, r is return
		other_trusteeships = list(map(lambda x : x.replace('\n',''), other_trusteeships))
		other_trusteeships = list(map(lambda x : x.replace('\r',''), other_trusteeships))

		other_trusteeships_link=[] # Initialize list
		for entry in otherboard: # This is grabbing the links and can't use a map function as not every entry has a link, hence the try/except which makes sure a missing character is appended to keep the list the right length
			try:
				otherboardlink = entry.find(href=True)
				otherboardlink = otherboardlink.get('href')
			except:
				otherboardlink = '.'
			other_trusteeships_link.append(otherboardlink)

		print(trustee[0]) # Just print to check it works but these could be turned into a dictionary or striped into a CSV like normal
		print(other_trusteeships[0])
		print(other_trusteeships_link[0])

		# Add to dictionary
	
		dicto_json = {'Charity Number':regno, 'Trustee Name':[trustee], 'Other trusteeships':[other_trusteeships], 'Other trusteeships link': [other_trusteeships_link]} # Store the new variables as a dictionary
		

		#Store as CSV
		#dicto_csv={'ccnum':ccnum, 'Trustee':trustee, 'Other trusteeships':other_trusteeships, 'Other trusteeships link': other_trusteeships_link} # Store the new variables as a dictionary
		#df_csv = pd.DataFrame(dicto_csv)
		#df_csv.to_csv(path_or_buf='Trustee_test_data.csv')

		print('\r')
		print(len(trustee) == len(other_trusteeships) == len(other_trusteeships_link)) # Validates lists are same length, don't need this in the final code

		print('>>> Found trustess for charity ' + name)

	# Write to JSON

	df_json = pd.DataFrame(dicto_json)
	#df_json.set_index(['regno'], inplace=True)
	#df_json.index+=1