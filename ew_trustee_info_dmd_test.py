#Scrape Trustee details
#Tom Wallace
#11/10/18
#This file scrapes trustee linking info from the charity commission website.

################################# Import packages #################################
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
import requests
import pandas as pd
import csv
import os

# Set paths #

rawdatapath = './'
outcsv = rawdatapath + '/trustee_test_data.csv'

# Delete output file if already exists
try:
    os.remove(outcsv)
except OSError:
    pass

################################# Grab the page #################################

print(' ') # Whitespace used to make the output window more readable
print('>>> Run started') # Header of the output, with the start time.
print('\r')

ccnumlist = ['1124004', '327889', '510842']
varnames_csv = ['Row ID', 'FYE', 'Other Trusteeship', 'Link to Other Trusteeship Charity', 'Trustee Name', 'Charity Number', 'Charity Name']

with open(outcsv, 'a') as f: # Add some code that deletes this file if it exists
	writer = csv.writer(f, varnames_csv)
	writer.writerow(varnames_csv)

for ccnum in ccnumlist:

	webbaddress = 'http://beta.charitycommission.gov.uk/charity-details/?regid=' + ccnum +'&subid=0'

	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'} # Spoof the user-agent of the request to return the content seen by Chrome.
	rorg = requests.get(webbaddress, headers=headers) # Grab the page using the URL and headers.
	html_org = rorg.text # Get the text elements of the page.
	soup_org = soup(html_org, 'html.parser') # Parse the text as a BS object.

	################################# Charity and Trustee info #################################

	# Capture charity name
	charityname = soup_org.find('div', {"class": "charity-heading-panel"}).h1
	print(charityname)
	charname = charityname.text

	# Capture financial year end (FYE) the trustee information refers to
	fyedetails = soup_org.find('div', {"id": "ContentPlaceHolderDefault_cp_content_ctl00_CharityDetails_4_lSubHeadingPanel"})
	print(fyedetails)
	fyetemp = fyedetails.text
	fye = fyetemp[32:]
	print(fye)

	# Capture trustee information
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

	print(len(trustee) == len(other_trusteeships) == len(other_trusteeships_link)) # Validates lists are same length, don't need this in the final code
	
	#Store as JSON
	#dicto_json= {'ccnum':ccnum, 'FYE': fye, 'Trustee':[trustee], 'Other trusteeships':[other_trusteeships], 'Other trusteeships link': [other_trusteeships_link]} # Store the new variables as a dictionary
	#df_json = pd.DataFrame(dicto_json)
	#df_json.index+=1
	#df_json.set_index(['ccnum'], inplace=True)
	#df_json.to_json(path_or_buf='Trustee_test_data.json', orient='index')

	#Store as CSV
	dicto_csv={'ccnum':ccnum,  'FYE': fye, 'charname': charname, 'Trustee':trustee, 'Other trusteeships':other_trusteeships, 'Other trusteeships link': other_trusteeships_link} # Store the new variables as a dictionary
	df_csv = pd.DataFrame(dicto_csv)
	with open('Trustee_test_data.csv', 'a') as f:
		df_csv.to_csv(f, header=False)

print('\r')
print('>>> Finished')
