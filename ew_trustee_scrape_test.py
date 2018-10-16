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

#from downloaddate_function import downloaddate


# ==========================================================

# ==========================================================

# Define project and data paths

#projpath = 'C:/Users/mcdonndz-local/Desktop/github/ew_charity_data/'
#rawdatapath = 'C:/Users/mcdonndz-local/Desktop/data/ew_charity_data/data_raw/'
rawdatapath = './'

inputfile = rawdatapath + '/ew_charlist.csv'

#Scraper function
def scraper(regno):

	regno=str(regno) 
	webadd = 'http://beta.charitycommission.gov.uk/charity-details/?regid=' + regno + '&subid=0'
	
	try:
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
	except:
		print('>>> Error <<<')
		trustee = '.'
		other_trusteeships = '.'
		other_trusteeships_link = '.'
	
	return (trustee, other_trusteeships, other_trusteeships_link)

#Main program

df = pd.DataFrame.from_csv(inputfile) # Create a panda's dataframe from the CSV

df.reset_index(inplace=True) 
df.set_index(['regno'], inplace=True) 
regno_list = df.index.values.tolist()

trustee_list=[]
other_trusteeships_list=[]
other_trusteeships_link_list=[]

for regno in regno_list:
	trustee, other_trusteeships, other_trusteeships_link = scraper(regno)
	trustee_list.append(trustee)
	other_trusteeships_list.append(other_trusteeships)
	other_trusteeships_link_list.append(other_trusteeships_link)

dicto = {'Regno':regno_list, 'Trustee': trustee_list, 'Other trusteeships':other_trusteeships_list, 'Links':other_trusteeships_link_list}

df_json = pd.DataFrame(dicto)
df_json.set_index(['Regno'], inplace=True)
df_json.to_json(path_or_buf='Trustee_test_data_loop.json', orient='index')