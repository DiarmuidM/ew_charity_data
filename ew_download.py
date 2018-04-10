## Python script to download monthly snapshot of England and Wales Register of Charities and SIR data:

# Diarmuid McDonnell
# Created: 28 March 2018
# Last edited: captured in Github file history

import json
import csv
import re
import requests, zipfile, io
import os
import os.path
import errno
import urllib
from time import sleep
from bs4 import BeautifulSoup
from downloaddate_function import downloaddate

# Run the downloaddate function to get the date 'benefacts_master.py' was executed.
ddate = downloaddate()

projpath = 'C:/Users/mcdonndz-local/Desktop/github/ew_charity_data/'
rawdatapath = 'C:/Users/mcdonndz-local/Desktop/data/ew_charity_data/data_raw/'
cleandatapath = 'C:/Users/mcdonndz-local/Desktop/data/ew_charity_data/data_clean/'

print(projpath)
print(rawdatapath)
print(cleandatapath)


# Define urls where Charity Registers can be downloaded #

main_url = 'http://data.charitycommission.gov.uk/default.aspx' # returns Data download webpage

# Request data from urls #

r = requests.get(main_url, allow_redirects=True)
soup = BeautifulSoup(r.text, 'html.parser')
print(soup)
links = soup.find_all('a')
print(links)
print('--------------------')
print('                    ')
print('--------------------')
#for link in links:
#   print(link.get('href'))
print('--------------------')
print('                    ')
print('--------------------') 
dlinks = soup.select("a[href*=extract1]")
print(dlinks) # Now I have a list of all of the a href elements we need.
print(len(dlinks))
numfiles = len(dlinks)
months = numfiles / 3
print('We have %s months of data extracts in total' %months)

# We only want the first three links as this corresponds to the most recent month of data.
latest_dlinks = dlinks[0:3]
print(latest_dlinks)

file_type = ['CharityRegister', 'SIR', 'TableBuild']
counter = 0

for el in latest_dlinks:
	print(el)
	link = el['href'] # Extract the href part of the <a> element.
	print(link)
	print(type(link))

	# Request the link and unzip to the correct folder
	r = requests.get(link, allow_redirects=True)
	print(r.status_code, r.headers) # I want to take this information and use it to name the files and folders
	metadata = r.headers
	print(metadata)
	print(type(metadata))
	lastmod = metadata['Last-Modified']
	print(lastmod)
	print(len(lastmod))
	udate = lastmod[8:16].replace(' ', '')
	print(udate) # Last modified date

	# Create a folder for the download to be saved in #
	try:
		os.mkdir(rawdatapath+udate)
		os.mkdir(cleandatapath+udate)
	except:
		print('Folder already exists')

	# Write the r.content to a file in the newly created folder #
	name = file_type[counter]

	file = rawdatapath + '/' + udate + '/' + 'cc_' + name + '_' + ddate + '.zip'
	print(file)
	outzip = open(file, 'wb')
	outzip.write(r.content)
	outzip.close()

	# Unzip the files using fimport.py #

	if name == 'CharityRegister': 

		from fimport import import_zip

		# Set working directory to clean data folder

		path = cleandatapath + '/' + udate
		os.chdir(path)
		import_zip(file)
		os.chdir('C:/Users/mcdonndz-local')

		counter +=1

	else:
		print('Not unzipping this file and moving onto the next')
		counter +=1
		

print('-----------------------')
print('                       ')
print('Finished downloading and unzipping latest copy of Charity Register')

############################################################################################################


# End of data download #

############################################################################################################
