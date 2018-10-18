#Scrape Trustee details
#Tom Wallace, Diarmuid McDonnell
#11/10/18
#This file scrapes trustee information from the Charity Commission website.

################################# Import packages #################################
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
from lxml.html import fromstring
from itertools import cycle
from datetime import datetime
from downloaddate_function import downloaddate
from time import sleep
import requests
import glob
import dropbox
import pandas as pd
import csv
import os
import io
import numpy as np

# Define a function for generating proxies
def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

# Get the current date
ddate = downloaddate()

# Set paths
rawdatapath = 'C:/Users/mcdonndz-local/Desktop/data/trustee_data'
projpath = './'
ew_inputfile = rawdatapath + '/extract_main_charity.csv'
ni_inputfile = rawdatapath + '/ni_charity_register.csv
outcsv = projpath + '/trustee_test_data' + ddate + '.csv'

# Delete output file if already exists
try:
    os.remove(ew_outcsv, ni_outcsv)
except OSError:
    pass

'''
# Download latest copy of EW charity register from the Commission's data portal
import ew_download
print('Finished executing ew_download.py')
print('                                             ')
print('---------------------------------------------')
print('                                             ')
sleep(10)
'''

'''
# Download latest copy of NI charity register from the Commission's data portal
import ni_download
print('Finished executing ew_download.py')
print('                                             ')
print('---------------------------------------------')
print('                                             ')
sleep(10)
'''


print(' ') # Whitespace used to make the output window more readable
print('>>> Run started') # Header of the output, with the start time.
print('\r')

# Create a panda's dataframe from the England & Wales CSV #
pd.set_option('precision', 0)

df = pd.read_csv(r'C:/Users/mcdonndz-local/Desktop/data/ew_charity_data/data_raw/extract_main_charity.csv') # skiprows doesn't work as it skips the headers
print(df.dtypes)

df['regno'] = df['regno'].fillna(0).astype(np.int64) # Remove decimals from regno

df.reset_index(inplace=True) 
df.set_index(['regno'], inplace=True) 
regno_list = df.index.values.tolist()

# Create a panda's dataframe from the Northern Ireland CSV #
pd.set_option('precision', 0)

df = pd.read_csv(r'C:/Users/mcdonndz-local/Desktop/data/ew_charity_data/data_raw/extract_main_charity.csv') # skiprows doesn't work as it skips the headers
print(df.dtypes)

df['regno'] = df['regno'].fillna(0).astype(np.int64) # Remove decimals from regno

df.reset_index(inplace=True) 
df.set_index(['regno'], inplace=True) 
regno_list = df.index.values.tolist()


varnames_csv = ['Row ID', 'FYE', 'Other Trusteeship', 'Link to Other Trusteeship Charity', 'Reason for Removal', 'Registered', 'Trustee Name', 'Charity Number', 'Charity Name']

outcsvlist = [ew_outcsv]

with open(ew_outcsv, 'a') as f: # Add some code that deletes this file if it exists
	writer = csv.writer(f, varnames_csv)
	writer.writerow(varnames_csv)

# Open logfile
logfilepath = projpath + 'trustte_log_' + ddate + '.csv'
logfile = open(logfilepath, 'w', newline='')
logcsv = csv.writer(logfile)
logcsv.writerow(['timestamp', 'regno', 'url', 'status code', 'execution time'])

# Define a counter to track how many rows of the input file the script processes
counter = 1

# Scrape proxies
proxies = get_proxies()
print(proxies) 
proxy_pool = cycle(proxies)


# Loop through list of charity numbers and scrape info from webpages
for ccnum in regno_list: # use '[:]' option if I want the script to start on a particular row of the dataframe 
 
	starttime = datetime.now() # Track how long it takes to scrape data for each charity
	proxy = next(proxy_pool) # Grab a proxy from the pool

	webadd = 'http://beta.charitycommission.gov.uk/charity-details/?regid=' + str(ccnum) +'&subid=0'
	headers = {'http': proxy, 'https': proxy, 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'} # Spoof the user-agent of the request to return the content seen by Chrome.
	
	# Define counters to track number of webpage request attempts
	attempt = 1
	failures = 0

	rorg = requests.get(webadd, headers=headers) # Grab the page using the URL and headers.
	print(proxy) # Checks if script is cycling through proxies
	
	if rorg.status_code==200: # Only proceed if the webpage can be requested successfully
		html_org = rorg.text # Get the text elements of the page.
		soup_org = soup(html_org, 'html.parser') # Parse the text as a BS object.

		################################# Charity and Trustee info #################################

		if not soup_org.find('div', {"class": "status removed"}): # If the charity isn't removed from the Register then proceed with scraping trustee info
			try: # This try captures instances where the webpage request was successful but the result is blank page i.e. no charity information
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

				otherboard = list(map(lambda x : x.find_all('div', class_='trustee-charity-name'), boardinfo)) # This line just says for every item in the list find the tag with the networking links
				other_trusteeships = []
				for el in otherboard:
					ot_text = list(map(lambda x : x.text, el)) # Extract the text
					ot_text = list(map(lambda x : x.replace('\t',''), ot_text)) #These three lines just remove the white space, t is tab, n is newline, r is return
					ot_text = list(map(lambda x : x.replace('\n',''), ot_text))
					ot_text = list(map(lambda x : x.replace('\r',''), ot_text))
					other_trusteeships.append(ot_text)
				print(other_trusteeships)

				other_trusteeships_link=[] # Initialize list

				for entry in otherboard:
					print(entry)
					try:
						otherboardlink = []
						for el in entry:
							atag = el.find('a', href=True) # Find <a> tags with ['href'] elements
							link = atag['href'] # Extract the link from ['href']
							otherboardlink.append(link)
					except:
						link = '.'
						otherboardlink.append(link)
					other_trusteeships_link.append(otherboardlink)

				print(trustee, other_trusteeships, other_trusteeships_link)

				# Data management #

				# Create variables capturing the number of trustees, number of other trusteeships per trustee, and adjust Row ID to begin at 1 

				# Write to JSON and CSV
				dicto = {'ccnum':ccnum,  'FYE': fye, 'charname': charname, 'Trustee':trustee, 'Other trusteeships':other_trusteeships, 'Other trusteeships link': other_trusteeships_link, 'Registered': '1', 'Reason for removal': '.'} # Store the new variables as a dictionary

				#df_json = pd.DataFrame(dicto)
				#df_json.set_index(['ccnum'], inplace=True)
				#df_json.to_json(path_or_buf='Trustee_test_data_loop.json', orient='index')

				df_csv = pd.DataFrame(dicto)
				print(df_csv)
				with open(outcsv, 'a') as f:
					df_csv.to_csv(f, header=False)
			except:
				print('\r')
				print('No information available for this charity | regno: ' + str(ccnum))
				print('\r')

		elif soup_org.find('div', {"class": "status removed"}): # Charity has been removed and therefore trustee information does not exist
			try: # This try captures instances where the webpage request was successful but the result is blank page i.e. no charity information
				remreason = soup_org.find('div', {'class': 'remove-description'})
				remreason = remreason.text
				print(remreason)

				# Capture charity name
				charityname = soup_org.find('div', {"class": "charity-heading-panel"}).h1
				print(charityname)
				charname = charityname.text

				# Write to CSV
				dicto_csv={'ccnum':ccnum,  'FYE': '.', 'charname': charname, 'Trustee':'.', 'Other trusteeships':'.', 'Other trusteeships link': '.', 'Registered': '0', 'Reason for removal': remreason} # Store the new variables as a dictionary
				df_csv = pd.DataFrame(dicto_csv, index=[1])
				print(df_csv)
				with open(outcsv, 'a') as f:
					df_csv.to_csv(f, header=False)
			except:
				print('\r')
				print('No information available for this charity | regno: ' + str(ccnum))
				print('\r')
		print('\r')
		print('Processed ' + str(counter) + ' rows in the input file')
		counter +=1
	else:
		print('\r')
		print(rorg.status_code, '| Could not resolve address of webpage')
		print('Will try at a later date')

	# Export results of script to log file
	runtime = datetime.now() - starttime
	logcsv.writerow([datetime.today().strftime('%Y%m%d %H:%M'), ccnum, webadd, rorg.status_code, runtime])

print('\r')
print('>>> Finished')