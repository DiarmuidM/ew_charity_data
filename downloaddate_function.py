from time import sleep
from datetime import datetime

# Define a function that identifies the data the script was run; derived from datatime. Call on this function from other scripts.
def downloaddate():
	ddate = datetime.today().strftime('%Y%m%d')
	print(ddate)
	return ddate

#downloaddate()	