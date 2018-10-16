#Scrape Trustee details
#Diarmuid McDonnell
#11/10/18
#This file scrapes trustee linking info from the Companies House website.

'''
    The aim of this script:
        1. Search for the accounts filing history (search_client.filing_history) using company numbers contained in a .csv
        2. Find the url to the PDF of the accounts
        3. Execute the urls and store the PDFs in an appropriate directory
        4. Output success (or failure) of searches to .csv files
'''

## 'pip install chwrapper' is run on the command line, not in python

## Import relevant packages for use in this script
import chwrapper
import json
import csv
import re
import requests
import pandas as pd
import os
import os.path
import errno
from time import sleep
from datetime import datetime
from downloaddate_function import downloaddate

ddate = downloaddate() # Get today's date


##Define the path where my API key is
tokenpath = "C:/Users/mcdonndz-local/Desktop/admin/chapitoken.txt" # "C:/Users/mcdonndz-local/Desktop/admin/chapitoken.txt"

# Open chapitoken.txt in read mode, print to the screen and create an object that stores the API access request
tokenfile = open(tokenpath, "r")
chapitoken = tokenfile.read()
print(chapitoken)
search_client = chwrapper.Search(access_token=chapitoken)

# Define a function to search for directors
def downloaddirectors(compid):
    response = search_client.officers(compid, order_by='surname', start_index='0', items_per_page='100')
    print('Metadata  |  ', response.status_code)
    return response

# Define a function to search for appointments of directors
def downloadappointments(dirid):
    response = search_client.appointments(dirid, start_index='0', items_per_page='100')
    print('Metadata  |  ', response.status_code)
    return response


# Test the functions #

response = downloaddirectors('01000490') # Valid company number
print(response.status_code)

#response = downloaddirectors('12345678') # Invalid company number
#print(response.status_code) # 404 error and program breaks


############### Main program ################

# Define the project and accounts paths, the file where company numbers will be read from, and an output file to store the results
rawdatapath = './'
projpath = './'
inputfile = rawdatapath + '/ew_complist_test.csv'
outcsv_dir = rawdatapath + '/ch_trustee_test_data.csv'
outcsv_app = rawdatapath + '/ch_appointments_test_data.csv'
outjson_dir = rawdatapath + '/ch_trustee_test_data.json'
outjson_app = rawdatapath + '/ch_appointment_test_data.json'

# Open director search logfile
logfilepath_dir = projpath + 'ch_dir_log_' + ddate + '.csv'
logfile_dir = open(logfilepath_dir, 'w', newline='')
logcsv_dir = csv.writer(logfile_dir)
logcsv_dir.writerow(['timestamp', 'coyno', 'success', 'status code'])

# Open appointment search logfile
logfilepath_app = projpath + 'ch_app_log_' + ddate + '.csv'
logfile_app = open(logfilepath_app, 'w', newline='')
logcsv_app = csv.writer(logfile_app)
logcsv_app.writerow(['timestamp', 'coyno', 'pid', 'success', 'status code'])

# Delete output files if already exist
flist = [outcsv_app, outcsv_dir]
for f in flist:
    try:
        os.remove(f)
    except OSError:
        pass

# Define a counter to track how many rows of the input file the script processes
counter = 1

# Begin API search #

print(' ') # Whitespace used to make the output window more readable
print('>>> Run started') # Header of the output, with the start time.
print('\r')

# Create a panda's dataframe from the CSV #

df = pd.read_csv(inputfile) # skiprows doesn't work as it skips the headers
df.reset_index(inplace=True) 
df.set_index(['coyno'], inplace=True) 
coyno_list = df.index.values.tolist()
print(df.shape)

requestcount = 0 # Create a counter for tracking how many requests are made to the API
dir_list = [] # Create a list for storing the results of the API requests

for coyno in coyno_list:
    #while len(coyno)<8:
        #coyno = '0' + coyno # The missing zero does not seem to be an issue (Company Numbers are meant to be 8 characters long)
    if requestcount >=600: # Check if rate limit is exceeded (600 requests per five minute period)
        print('\r')
        print('Program is going to sleep for five minutes')
        sleep(320)
        requestcount = 0
    else:
        try:
            response = downloaddirectors(coyno)
            print(response.json())
            dict_results = response.json()
            print(type(dict_results))
            dict_results['coyno'] = str(coyno)
            dir_list.append(dict_results)

            success = 1

            # Write the results of the API search to the log file
            logcsv_dir.writerow([datetime.today().strftime('%Y%m%d %H:%M'), str(coyno), success, response.status_code])
            print('__________________________________________________________________________')
            print('                                                                          ')
            print('                                                                          ')
            print(requestcount)
            print('                                                                          ')
            print('                                                                          ')
            print('__________________________________________________________________________')
            requestcount +=1
        except:
            print('\r')
            print('Could not find record of Company Number: ' + str(coyno))
            success = 0
            logcsv_dir.writerow([datetime.today().strftime('%Y%m%d %H:%M'), str(coyno), success])

#print(dir_list)

# Export the results to a json file
with open(outjson_dir, 'w') as f: 
    json.dump(dir_list, f)


sleep(60)

###### Look up appointments of company directors ######
# officer_role=="director"

with open(outjson_dir, 'r') as f: 
    directors = json.load(f)

print(len(directors))

requestcount = 0 # Create a counter for tracking how many requests are made to the API
app_list = [] # Create a list for storing the results of the API requests

# Search through list of directors for information about their other appointments
for el in directors:
    coyno = el['coyno']
    for p in el['items']:
        link = p['links']['officer']['appointments'] # Link containing person id
        #print(link)
        #print(len(link)) # All links are 50 characters long
        pid = link[10:37]
        print(pid) # Use this to search the API for appointments

        if requestcount >=600: # Check if rate limit is exceeded (600 requests per five minute period)
            print('\r')
            print('Program is going to sleep for five minutes')
            sleep(320)
            requestcount = 0
        else:
            try:
                response = downloadappointments(pid)
                print(response.json())
                dict_results = response.json()
                print(type(dict_results))
                app_list.append(dict_results)
            
                success = 1
                logcsv_app.writerow([datetime.today().strftime('%Y%m%d %H:%M'), str(coyno), str(pid), success, response.status_code])

                print('__________________________________________________________________________')
                print('                                                                          ')
                print('                                                                          ')
                print(requestcount)
                print('                                                                          ')
                print('                                                                          ')
                print('__________________________________________________________________________')
                requestcount +=1
            except:
                print('\r')
                print('Could not find record of Individual: ' + str(pid))
                success = 0
                logcsv_app.writerow([datetime.today().strftime('%Y%m%d %H:%M'), str(coyno), str(pid), success, '404'])

# Export the results to a json file
with open(outjson_app, 'w') as f: 
    json.dump(app_list, f)