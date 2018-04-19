// File: ew_datamanagement_20180419.do
// Creator: Diarmuid McDonnell
// Created: 19/04/2018

******* England & Wales Register of Charities data cleaning *******

/* This DO file performs the following tasks:
	- imports raw data in csv format
	- cleans these datasets
	- links these datasets together to form a comprehensive Register of Charities and a financial panel dataset
	- saves these datasets in Stata and CSV formats
   
	The files associated with this project can be accessed via the Github repository: https://github.com/DiarmuidM/regno
*/


******* Preliminaries *******

// These are all handled by profile.do

/*
clear
capture clear matrix
set mem 400m // not necessary in recent versions of Stata
set more off, perm
set scrollbufsize 2048000
exit
*/

/* Define paths */

include "C:\Users\mcdonndz-local\Desktop\github\ew_charity_data\stata\do_files\ew_paths_20180419.doi"
di "$path1"
di "$path2"
di "$path3"
di "$path4"
di "$path5"
di "$path6"
di "$path7"
di "$path8"


/* 1. Open the raw data in csv format */

import delimited using $path3\extract_charity.csv, varnames(1) clear
count
desc, f
notes
codebook *, compact
**codebook *, problems

/*
		- remove problematic variables/cases e.g. duplicate records, missing values etc
		- sort data by unique identifier
		- explore invalid values for each variable
		- label variables/values/dataset
*/


	/* Missing or duplicate values */
	
	capture ssc install mdesc
	mdesc
	missings dropvars, force
	
	duplicates report // Lots of duplicates
	duplicates list // Look to be data entry errors: every variable is blank except regno, which is a string (e.g. "AS AMENDED ON 27/11/2011&#x0D;").
	duplicates drop
	
	duplicates report regno
	duplicates list regno // Looks like a combination of data entry errors (strings again) and duplicate numbers. Delete strings first.
	
		list regno if missing(real(regno))
		replace regno = "" if missing(real(regno)) // Set nonnumeric instances of regno as missing
		destring regno, replace
		
		duplicates report regno
		duplicates list regno
	
	
	/* Remove unnecessary variables */
	
	drop add1 add2 add3 add4 add5 phone fax
	codebook corr // Looks like the name of the principal contact; drop.
	drop corr
	
		
	/* 	Sort data */
	
	sort regno
	list regno in 1/1000

	
	/* Deal with issues identified by codebook, problems */
	
	// Trim leading and trailing blanks
	
	foreach var in name nicename gd aob address objects phone aob_classified corr address postcode fax web latest_strata almanac_strata objects date_registered date_removed icnpo_category icnpo_ncvo_category regy {
		replace `var' = strtrim(`var')
	}
	
	// Trim embedded blanks
	
	foreach var in name nicename gd aob aob_classified corr address postcode phone fax web latest_strata almanac_strata objects date_registered date_removed icnpo_category icnpo_ncvo_category regy {
		replace `var' = subinstr(`var', " ", "", .)
	}
			
	
	
	/* Invalid values for each variable */
	
	codebook regno
	inspect regno // This variable is a string; should really be numeric.
	list regno in 300000/l // I think it's due to presence of Scottish charity numbers.
	list regno in 1/1000
	notes: use regno for linking with other datasets containing charity numbers
	
		
		// Count string length and determine if scottish and english/welsh charity numbers are different:
		
		capture drop length_regno
		gen length_regno = strlen(regno)
		inspect length_regno
		sum length_regno
		tab length_regno
		
			list regno if length_regno==8 // I think these are Scottish charities
			list regno if length_regno==7
			list regno if length_regno==6 // 6 and 7 must be English & Welsh charities
			
			count if length_regno==6

			// Let's remove the "SC" at the beginning and replace with a numeric prefix unique to Scottish charities e.g. "5050"
			
			preserve
				replace regno = substr(regno, 3, .)
				duplicates report regno
			restore
			/*
				Just removing the "SC" creates duplicates of regno.
			*/
				

			replace regno = subinstr(regno, "SC", "5050", .) if length_regno==8
			list regno if length_regno==8
			duplicates report regno
			duplicates list regno
			
				// Create a variable identifying Scottish charities
			
				capture drop scot
				gen scot = 1 if length_regno==8
				
				// Drop Scottish charities from the dataset
				
				drop if scot==1

			drop length_regno
			
		
		// Create a unique id (numeric)
		
		capture drop uniqueid
		gen uniqueid = _n
		list uniqueid in 1/1000
		sort uniqueid
		
	destring regno, replace
	
		
	codebook name nicename
	list name nicename in 1/1000 // There are some dummy charities (e.g. TestCharity, DELETED) that need to be removed.
	preserve
		gsort name
		list name nicename in 1/1000
	restore
	/*
		There are some minor issues with name (55 missing values, invalid values e.g. TestCharity, DELETED).
		I'll just assume that all of the values for regno are valid and ignore name.
	*/
	drop nicename
	
	
	codebook orgtype
	tab orgtype // RM=removed, R=registered i.e. active
	encode orgtype, gen(charitystatus)
	tab charitystatus
	label define charitystatus_label 1 "Active" 2 "Removed"
	label values charitystatus charitystatus_label
	tab charitystatus
	drop orgtype
	
	
	codebook gd aob aob_classified
	tab1 aob_classified
	
	

	
	
	codebook welsh
	tab welsh // T=true, F=false?
	encode welsh, gen(charity_wales)
	tab charity_wales, nolabel
	label define charity_wales_label 1 "False" 2 "True"
	label values charity_wales charity_wales_label
	tab charity_wales
	drop welsh

	
	codebook coyno // Companies House number
	list coyno if coyno!=""
	
		capture drop length_coyno
		gen length_coyno = strlen(coyno)
		tab length_coyno // 0=missing and lots of varying lengths.
		
	destring coyno, replace // Non-numeric characters (e.g. "RC"). Leave as string for now.	

	
	/* Merge Bethnal Green information to create area variable */
	
	merge 1:1 regno using $path1\bethnalgreen_20180306.dta, keep(match master using)
	tab _merge
	list if _merge==2 // 1 observation with all missing values; drop
	drop if _merge==2
	rename _merge bethmerge
	
	notes: The code for Birmingham charities is E08000025 - geog_la variable.
	notes: The code for Burnley charities is E07000117 - geog_la variable.
	notes: The code for Bolton charities is E08000001 - geog_la variable.
	notes: The code for Bethnal Green charities is E09000030 - geog_la variable.
	codebook geog*, compact
	codebook geog*
	count if geog_la=="E08000025"
	count if geog_la=="E07000117"
	count if geog_la=="E08000001"
	count if geog_la=="E09000030"
	
		capture drop area
		gen area = 1 if geog_la=="E08000025"
		replace area = 2 if beth==1
		replace area = 3 if geog_la=="E08000001"
		replace area = 4 if geog_la=="E07000117"
		replace area = 5 if geog_la!="E08000025" & geog_la!="E07000117" & geog_la!="E08000001" & geog_la!="E09000030" & geog_la!=""
		label define area_label 1 "Birmingham" 2 "Bethnal Green" 3 "Bolton" 4 "Burnley" 5 "Rest of UK"
		label values area area_label
		tab area
		
		// Do a quick test to see if aob field contains 'bethnal green'
		
		list aob in 1/500 if aob!=""
		count if strpos(aob, "BETHNALGREEN")
		di r(N) " observations mentioning Bethnal Green
		tab beth if strpos(aob, "BETHNALGREEN")
			
		notes: 4,291 Birmingham charities.
		notes: 236 Burnley charities.
		notes: 790 Bolton charities.
		notes: 320 Bethnal Green charities.
	
	
	notes: geog_ccg geog_lep are not neccessary for analysis.
	notes: geog_oa is output area from census (~10,000 people in each area); also not neccessary for analysis.
	drop geog_ccg geog_lep geog_oa
	
			
			/* Create a dataset of postcodes and emails for our four areas */
			
			preserve
				codebook email postcode
				keep if area < 5
				keep regno name area postcode email web phone regy remy
				export excel using $path2\leverhulme_postcodeandemail_4b.xlsx, firstrow(var) replace
			restore	

	
	
	codebook latest_fye latest_activity
	tab latest_fye, sort miss // Need to extract the year.
	tab latest_activity, sort miss
	
		capture drop latest_repyr
		gen latest_repyr = substr(latest_fye, 7, .)
		tab latest_repyr
		destring latest_repyr, replace
	
		// Are latest_repyr and latest_activity different? If so, in what way?
		
		list latest_repyr latest_activity in 1/1000 // They look to be different for certain charities.
		capture drop diff_repyractivity
		gen diff_repyractivity = latest_activity - latest_repyr
		sum diff_repyractivity, detail
		histogram diff_repyractivity, norm freq
		/*
			Range of differences: sometimes latest_activity is later than fye, sometimes earlier.
			
			I'm going to go with latest_fye as the indicator of most recent year of charitable activity, at least
			until I see how latest_activity is constructed.
		*/
		
		
	
	codebook removed_reason
	tab removed_reason // Need the codebook!
	tab removed_reason charitystatus, miss
	notes: 24,630 removed charities without a reason for removal
	rename removed_reason oldvar
	
	encode oldvar, gen(removed_reason)
	tab removed_reason
	tab removed_reason, nolab
	label define removed_reason_label 1 "AMALGAMATED" 2 "CEASED TO BE CHARITABLE" 3 "CEASED TO EXIST" 4 "REMOVED BY APPLICATION" 5 "DUPLICATE REGISTRATION" ///
		6 "EXCEPTED CHARITY" 7 "REMOVED IN ERROR" 8 "EXEMPT CHARITY" 9 "FUNDS TRANSFERRED (GI)" 10 "FUNDS TRANSFERRED (INCOR)" 11 "DOES NOT OPERATE" ///
		12 "POLICY REMOVAL" 13 "REGISTERED IN ERROR" 14 "FUNDS TRANSFERRED (S.74)" 15 "FUNDS SPENT UP (S.75)" 16 "UNITING DIRECTION (S96) M" ///
		17 "TRANSFER OF FUNDS" 18 "FUNDS SPENT (BY TRUSTEES)" 19 "TRANSFERRED TO EXEMPT CHY" 20 "VOLUNTARY REMOVAL"
	label values removed_reason removed_reason_label
	tab removed_reason
	drop oldvar
	notes: Only use two categories of removed_reason: CEASED TO EXIST (3) and DOES NOT OPERATE (11).

	
	
	codebook latest_income latest_expend latest_assets latest_employees trustees
	inspect latest_income latest_expend latest_assets latest_employees trustees
	sum latest_income latest_expend latest_assets latest_employees trustees, detail // Lots of zeroes; I take it I can treat these as valid values.
	notes: 366 charities with negative values for latest_assets.
	
		count if latest_income==0 // 29,952
		count if latest_expend==0 // 40,168
		count if latest_employees==0 // 1,448
		count if latest_assets==0 // 121
		count if trustees==0 // 190,8888

		// Create alternative functional forms of these variables
		/*
		ladder latest_income 
		ladder latest_employees
		ladder latest_expend 
		ladder latest_assets
		ladder trustees
		*/
		/*
			Not producing any statistics for these variables? The issue appears to be with -sktest-.
			It can break down for large sample sizes and/or large deviations from Gaussianity.
			
			Oh well, the variables should be transformed to log functional form and we take it from there.
		*/
		
		foreach var in latest_income latest_expend latest_employees latest_assets trustees {
			gen ln_`var' = ln(`var' + 1) // Should it be .5?
			histogram ln_`var', normal freq
		}
		sum ln_latest_income ln_latest_expend ln_latest_employees ln_latest_assets ln_trustees, detail
		/*
			Need to do something with these zeroes: exclude them from analyses? I suppose they are fine for now.
		*/
		
		
	**twoway (scatter latest_income latest_expend, jitter(20) mcolor(%50)) (lfit latest_income latest_expend)

		
	codebook latest_strata latest_strata_code
	/*
		latest_strata is a categorical variable of org size. latest_strata_code is ambiguous but doesn't need transforming.
	*/	
	
	tab1 latest_strata
	encode latest_strata, gen(charitysize)
	tab charitysize
	tab charitysize, nolab
		recode charitysize 7=1 9=2 2=3 5=4 1=5 6=6 4=7 3=8 8=9
		tab charitysize
	label define charitysize_label 1 "No income" 2 "Under 10k" 3 "10k - 25k" 4 "25k - 100k" 5 "100k - 500k" 6 "500k - 1m" ///
		7 "1m - 10m" 8 "10m - 100m" 9 "Over 100m"
	label values charitysize charitysize_label
	tab charitysize
	drop latest_strata
	
	
	codebook almanac_strata
	encode almanac_strata, gen(charitysize_almanac)
	tab charitysize_almanac
	tab charitysize_almanac, nolab
		recode charitysize_almanac 7=1 9=2 2=3 5=4 1=5 6=6 4=7 3=8 8=9
		tab charitysize_almanac
	label define charitysize_almanac_label 1 "No income" 2 "Under 10k" 3 "10k - 25k" 4 "25k - 100k" 5 "100k - 500k" 6 "500k - 1m" ///
		7 "1m - 10m" 8 "10m - 100m" 9 "Over 100m"
	label values charitysize_almanac charitysize_almanac_label
	tab charitysize_almanac
	drop almanac_strata
	
		tab charitysize charitysize_almanac
		list latest_fye almanac_fye in 1/500
		/*
			Plenty of differences between the two, most likely due to different comparison years.
		*/
		

	
	codebook objects
	
	
	codebook icnpo* // Use this to track changes in types of charities over time.
	tab1 icnpo_code icnpo_category
	tab1 icnpo_ncvo_code icnpo_ncvo_category
	/*
		I'll use the NCVO version of ICNPO categorisation.
	*/
		
		
	codebook date_registered date_removed		
	codebook regy remy // Year values extracted from date_registered date_removed respectively.
	// check scottish registration years
	
		list regno if missing(regy)
		count if missing(regy) // Who are these charities? I think they might be Scottish charities.
		tab scot if missing(regy)
		/*
			21,528 of 21,665 missing values for regy are accounted for by Scottish charities.
			
			I need to link to Scottish Charity Register.
		*/
	
	
		// Create variable capturing period in which charities were registered:
		
		tab1 regy remy
		/*
			There appear to be some problematic values for regy e.g. 9 14. Need to get rid of these before I destring and recode.
			
			I need to calculate string length, set observations with strlen==3 to missing, and then destring.
		*/
		
			capture drop length_regy
			gen length_regy = strlen(regy)
			tab length_regy // 0=missing
			/*
				158 observations with invalid values for period i.e. 3-character string.
				
				This is due to the timestamp on some of the values for date_registered; see if I can extract it properly.
			*/

			
				list date_registered regy if length_regy==3 // No way to extract the year from these values e.g. 0000-00-0314:00:00.
				
			notes: 158 observations with invalid values for registered year i.e. 3-character string, due to missing components of "date" variables.
			
			replace regy = "" if length_regy==3
			tab regy, sort miss
			
		destring regy, replace
		destring remy, replace
		
		capture drop period
		gen period = regy
		tab period, sort miss
		count if period < 1945
		recode period min/1944=1 1945/1965=2 1966/1978=3 1979/1992=4 1993/max=5 *=.
		label define period_label 1 "Pre-1945" 2 "1945-1965" 3 "1966-1978" 4 "1979-1992" 5 "Post-1993"
		label values period period_label
		tab period, miss
		count if regy==.
		
		tab charitysize period, all row nofreq
		
		// Period when a charity was removed
		
		capture drop remperiod
		gen remperiod = remy
		tab remperiod, sort miss
		count if remperiod < 1945
		recode remperiod min/1944=1 1945/1965=2 1966/1978=3 1979/1992=4 1993/max=5 *=.
		label values remperiod period_label
		tab remperiod, miss
		count if remy==.
		
		// Create a charity age variable: charity age = latest_repyr - regy
		
		capture drop charityage
		gen charityage = latest_repyr - regy if ~missing(latest_repyr) & ~missing(regy)
		sum charityage, detail // Some extreme values; explore in more detail.
		histogram charityage, norm freq
		notes: charityage is derived from latest_repyr - regy
		
			count if charityage < 1 // 1,514 charities younger than 1.
			count if charityage <= 0 // Same as above. Who are all these -1 charities?
			list regno charitystatus latest_repyr regy if charityage <= 0
			/*
				Look to be a whole variety of charities here:
					- ~half are removed and relate to older years (1995/96)
					- some are Scottish charities from 2015/16
			*/
		
			capture drop ln_charityage
			gen ln_charityage = ln(charityage + 1) if charityage >= 0
			histogram ln_charityage, norm freq
			/*
				What do I do about charityage==0 (ln_charityage <=1)? Just exclude them from analyses I suppose.
			*/
	
	
	/* Produce some line graphs of registrations and removals over time */
	/*
	preserve
		capture drop freq
		gen freq = 1
		collapse (count) freq, by(regy)
		line freq regy
	restore
	
	preserve
		capture drop freq
		gen freq = 1
		collapse (count) freq, by(remy)
		line freq remy, ylabel(10 100 1000 10000) yscale(r(0 10000))
	restore
	*/
		
		
	/* 3. Label and order variables */
	/*
		The dataset is not currently documented in full. Do my best to label the variables and speak to John about the remainder.
	*/
	
	label variable regno "Charity number of organisation"
	label variable aob_classified "Geographical scale of activity i.e. local, national"
	label variable coyno "Companies House number"
	label variable geog_la "Area charity is based"
	label variable removed_reason "Reason for removal from Charity Register"
	label variable regy "Year charity was founded"
	label variable remy "Year charity was removed from Charity Register"
	label variable scot "Charity registered with OSCR in Scotland"
	label variable charity_wales "Charity is based in Wales"
	label variable charitystatus "Whether charity is active or removed from Charity Register"
	label variable uniqueid "Unique id of record"
	label variable latest_repyr "Most recent reporting year - derived from latest_fye"
	label variable charitysize "Categorical measure of charity income - derived from latest_income"
	label variable period "Era charity was founded in - derived from key policy and political changes"
	label variable charityage "Length of time - in years - since charity was founded"
	label variable ln_charityage "Length of time - in years - since charity was founded (log)"

	
	sav $path1\ncvo_charitydata_20171115_v2.dta, replace
