# Scrape charity policy details
# Diarmuid McDonnell
# 11/10/18

# This file scrapes policy information for a given charity from the Charity Commission website.
# Note this information is only available for registered charities.
# Scraping is necessary as this information is not available via the data download at http://data.charitycommission.gov.uk/


####### Import packages #######
import os
import argparse
from datetime import datetime as dt
from downloaddate_function import downloaddate
import csv
import re
import dropbox
import logging
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as soup
import dateutil.parser


####### Global params #######
sleeptime = 0 # Sleep time used when the scraper hits and erro
showalreadyscraped = 0 # Set to 1 to see already scraped charities in console window - runs faster when set to 0


####### Main program #######

# Run the downloaddate function to get the current date
ddate = downloaddate()

# Fetch Dropbox authentication
dbtokenpath = 'C:/Users/mcdonndz-local/Desktop/admin/db_token.txt'
#dbtokenpath_pi = '/home/pi/admin/dp_token.txt'
dbtokenfile = open(dbtokenpath, "r")
dbapitoken = dbtokenfile.read()
print(dbapitoken)

dbx = dropbox.Dropbox(dbapitoken) # Create an object for accessing Dropbox API

# log_starttime = longtime() # Get the current date and time

# Define paths
projpath = './' # Location of syntax
rawdatapath = 'C:/Users/mcdonndz-local/Desktop/data/ew_charity_data/data_raw/'
cleandatapath = 'C:/Users/mcdonndz-local/Desktop/data/ew_charity_data/data_clean/'
downloadpath = cleandatapath + 'policy_scrape/'
if not os.path.exists(downloadpath):
    os.makedirs(downloadpath)

# Set the filenames
inputfile = rawdatapath + 'extract_main_charity.csv' # This file is downloaded by ew_download.py
outputfilename = 'ew_policy_data_' + ddate + '.csv' # This is the main output data
outputfile = downloadpath + outputfilename
status = downloadpath + 'ew_policy_data_status_'  + ddate + '.txt' # Status is a text file which records the last charity which the scraper atempted to parse, can be used for debugging failue. This is automatically removed when the script completes.

print('\n>>> Run started') # Header of the output, with the start time.

# Create a panda's dataframe from the input CSV #
#pd.set_option('precision', 0)

with open(inputfile, 'rb') as f: # Open the input file
	df = pd.read_csv(f)

df['regno'] = df['regno'].fillna(0).astype(np.int64) # Remove decimals from regno

df.reset_index(inplace=True) 
df.set_index(['regno'], inplace=True) 
regno_list = df.index.values.tolist() # Make a list of all charity numbers from the input dataframe
print('Example regnumbers: ',regno_list[0:5])
print('Number of regnumbers: ',len(regno_list))
#shuffle(regno_list)


# Define variable names for the output files
if not os.path.exists(outputfile):
	varnames = ['Row ID', 'Execution Time', 'FYE', 'Policies', 'Other Regulators', 'Reason for Removal', 'Registered', 'Scrape Time', 'Status Code', 'URL', 'Charity Number', 'Charity Name']
	with open(outputfile, 'a', newline='') as f:
		writer = csv.writer(f, varnames)
		writer.writerow(varnames)

# Define a counter to track how many rows of the input file the script processes
counter = 1

# prev_df = pd.read_csv(outputfile, encoding='cp1252') # Read in the output file to check for perviously scraped charities, this avoids double scraping and it means the script can be restarted from where it left off
# prev_suc = prev_df['Charity Number'].tolist()

# Loop through list of charity numbers and scrape info from webpages
for ccnum in regno_list[0:2]:

	starttime = dt.now() # Track how long it takes to scrape data for each charity

	webadd = 'https://beta.charitycommission.gov.uk/charity-details/?regId=' + str(ccnum) +'&subId=0'
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'} # Spoof the user-agent of the request to return the content seen by Chrome.
	
	rorg = requests.get(webadd, headers=headers) # Grab the page using the URL and headers.
	html_org = rorg.text # Get the text elements of the page.
	soup_org = soup(html_org, 'html.parser') # Parse the text as a BS object.

	################################# Charity and Trustee info #################################

	# Capture charity name
	charname = soup_org.find("h1", class_="pcg-charity-details__title").text
	print(charname)

	# Capture financial year end (FYE) the trustee information refers to
	fyetemp = soup_org.find('p', class_="pcg-charity-details__title-desc").text
	print(fyetemp)
	try:
		fye = re.search('(?<=ending )(\d\d \w+ \d\d\d\d)', fyetemp).group(1) # Grab financial year using regex
		#print(fye)
	except:
		fye = 'No financial year on record, may be overdue.'
	print(fye)

	# Capture policies
	exdetails = soup_org.find_all('div', {'class': 'pcg-charity-details__block col-lg-6'})
	print(exdetails)

	policies = []

	for el in exdetails:
		try:
			sptags = el.find_all('span') # extract span tags
			for span in sptags:
				spinfo = span.text
				print(spinfo)
				policies.append(spinfo)
		except:
			print('No span tag')

	print(policies)
	del policies[0] # drop first element (founding doc and date info)