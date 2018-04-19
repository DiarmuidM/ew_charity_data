// File: ew_dataanalysis_20180419.do
// Creator: Diarmuid McDonnell
// Created: 19/04/2018

******* England & Wales charity data - removal *******

/* 
	
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


/* Empty figures folder */
/*
	
	**shell rmdir $path1 /s /q
	
	pwd
	
	local workdir "C:\Users\mcdonndz-local\Desktop\github\a-tale-of-four-cities\figures\"
	cd `workdir'
	
	local datafiles: dir "`workdir'" files "*.gph"
	
	foreach datafile of local datafiles {
		rm `datafile'
	}
	
	local datafiles: dir "`workdir'" files "*.png"
	
	foreach datafile of local datafiles {
		rm `datafile'
	}

*/

/* 1. Open the clean dataset */

capture log close
**log using $path9\rqone_`tdate'.log, text replace

use $path3\ncvo_charitydata_analysis_20171211.dta, clear
capture datasignature report
count
desc, f
notes

/*
	Dependent variables:
		- regy, remy
		- charitystatus, removed_reason
		- icnpo_ncvo_category
		- charityage

	Independent variables:
		- area
		- period
*/

	/* Create dependent variables */
	
	// Removed
	
	capture drop dremoved
	gen dremoved = charitystatus
	recode dremoved 1=0 2=1
	tab dremoved charitystatus
	label variable dremoved "Organisation no longer registered as a charity"
	
	// Multinomial measure of removed reason
	
	capture drop removed
	gen removed = .
	replace removed = 0 if charitystatus==1
	replace removed = 1 if removed_reason==3 | removed_reason==11
	replace removed = 2 if removed_reason==20
	replace removed = 3 if removed_reason!=3 & removed_reason!=11 & removed_reason!=20 & removed_reason!=.
	tab removed
	tab removed_reason removed
	tab removed charitystatus
	label define rem_label 0 "Active" 1 "Failed" 2 "Vol Removal" 3 "Other Removal"
	label values removed rem_label
	label variable removed "Indicates whether a charity has been de-registered and for what reason"
	
	
	/* Create independent variables */
	
	// Company legal form
	
	capture drop company
	list coyno if coyno!="" in 1/1000
	**destring coyno, replace
	gen company = (coyno!="")
	tab company
	/*
		coyno needs a lot more work: i.e. check for duplicates, non-numeric characters, same as regno etc.
	*/
	
	codebook icnpo_ncvo_category company period aob_classified charityage charitysize, compact
	tab icnpo_ncvo_category, nolab
	encode icnpo_ncvo_category, gen(icnpo)
	encode aob_classified, gen(areaop)
	recode areaop 3 4=3
	tab areaop
	


		
**********************************************************************************************************************************
	
	
**********************************************************************************************************************************	
	
		
	/* 3. Regression analysis */
	
	/*
		Regression models for our two survival-related dependent variables: charityage (of removed charities) and removed multinomial variable.
		Independent variables: icnpo_ncvo_category period aob_classified charitysize company charityage (for removed).
	*/
	
	// Multinomial logistic regression of whether a charity is removed for whatever reason
			
	codebook charityage
	sum charityage, detail
		count if charityage < 0
		drop if charityage < 0 // 50 observations deleted.
	/*
		Period needs to be adjusted, too arbitrary at the moment; need other functional forms also.
	*/
		
	mdesc icnpo_ncvo_category company period aob_classified charityage charitysize
	/*
		A quarter of the sample has missing data for charityage (24%).
	*/
		
	// Create a variable that identifies cases with no missing values for independent variables
			
	capture drop nomiss_model
	gen nomiss_model = 1
	replace nomiss_model = 0 if missing(icnpo_ncvo_category) | missing(company) | missing(aob_classified) ///
		| missing(charityage) | missing(charitysize)
	tab nomiss_model // 232,744 observations with no missing data for all of the independent variables.
	keep if nomiss_model==1
			
	// Create a variable that captures the baseline odds in a logit model - must be used in conjunction with noconstant option
			
	capture drop baseline
	gen baseline = 1
	/*
		I can see `baseline' only being useful if there are few explanatory variables with not many categories.
	*/
			
	
	/* Descriptive statistics */
	
	/* 2. Descriptive statistics */
	
	/* Sample description */
	/*
		Overall statistics for our independent variables.
	*/
		
	tab1 aob_classified icnpo_ncvo_category period charitysize company
	sum charityage foundyear remy, detail
	
	local fdate = "19apr2018"

	graph bar , over(removed) over(aob_classified) stack asyvar percent
	graph bar , over(removed) over(period) stack asyvar percent
	graph bar , over(removed) over(company) stack asyvar percent
	graph bar , over(removed) over(icnpo_ncvo_category) stack asyvar percent
	
	tab remy removed if remy>=2007
	local numobs:di %6.0fc r(N)
		
	graph bar if remy>=2007, over(removed) over(remy) stack asyvar percent ///
		bar(1, color(maroon )) bar(2, color(dknavy)) bar(3, color(erose)) ///
		ylabel(, nogrid labsize(small)) ///
		ytitle("% of charities", size(medsmall)) ///
		title("Charity Removal Reasons - UK")  ///
		subtitle("by removal year")  ///
		note("Source: Charity Commission Register of Charities (31/12/2016);  n=`numobs'. Produced: $S_DATE.", size(vsmall) span) ///
		scheme(s1color)

	graph export $path6\removedreason_`fdate'.png, replace width(4096)
		
	// Whole sample
			
	sum charityage
	tab1 icnpo_ncvo_category area period aob_classified charitysize
			
	// By removed or not
			
	bysort removed: sum charityage
	bysort removed: tab1 icnpo_ncvo_category company period aob_classified charitysize
	/*
		25% of charities in the sample are closed. Average age is 22 and 17.
		
		[Write more about these descriptives.]
	*/
		
			
	/* Bivariate associations between dependent and each independent variable */
		
	foreach var of varlist icnpo_ncvo_category company period aob_classified charitysize {
		tab `var' removed, col nofreq all
	}	
	/*
		Moderate association with charitysize, weak-to-moderate with icnpo, nothing with the others.
	*/
	** [INSERT BARCHARTS - SEE VERNON'S SYNTAX]
		
	table removed, c(mean charityage sd charityage p50 charityage)
	anova charityage removed
	ereturn list
	di "Association statistic = " sqrt( e(r2))
	/*
		Eta = .1434039***
	*/
		
	/* Potential interaction effects: size and investigated; size and age
		
		bysort size: tab investigated report, col all
		pwcorr charityage latestgrossincome
		anova charityage size
			ereturn list
			di sqrt( e(r2))
		/*
			There are not enough cases to perform interaction effects.
		*/
		*/
		
		// Functional form of age and size with the outcome
		
		
	
	/* Model building */
	
	/*
		Test a number of different estimators: linear, logit, glm.
	*/
	
	// Decide on reference categories
	
	tab1 icnpo_ncvo_category company aob_classified charitysize
	/*
		Under 10k (charitysize==2), Local (aob_classified==1), Post-1992 (period==5), and Social Services (icnpo==17).
	*/
	
	// Model 1 - null model
		
	mlogit removed
	est store null
		
	// Model 2 - main effects
			
	regress removed ib17.icnpo i.company ib1.areaop ib2.charitysize charityage, robust
	est store linr
	fitstat
			
	tab removed
	
	mlogit removed ib17.icnpo i.company ib1.areaop ib2.charitysize charityage, vce(robust) nolog
	est store logr
	fitstat
	ereturn list

	
	*est save $path3\uk_removed_mlogit_20180419, replace
	*est use $path3\uk_removed_mlogit_20180419.ster

		/*
		// Save results in a matrix and then as variables
		/*
			There is an issue with the zero for the first variable in the model.
		*/
		*preserve
		
			matrix effect=e(b)
			*matrix variance=e(V)
			*matrix outcome=e(out)
			*scalar r2=e(r2_p)	
			
			clear 
			
			svmat effect, names(beta)
			*svmat variance, names(varian)
			*svmat outcome, names(out)
			
			list beta1
			l beta*
			
			drop beta1-beta34 // Drop first 35 variables as they are the values for the base outcome i.e. "Active".
			drop if missing(beta35-beta140) // Drop observations with missing data for the coefficient variables.
			l
			
			expand 3 // Create two extra rows for the other outcomes: vol removal and other removal.
			/*
				The first 35 variables correspond to the coeffients for the first outcome; the next 35 to the second outcome, and the final
				35 to the thrid outcome.
			*/
			
			forvalues i = 2(1)3 {
				forvalues num = 36(1)70 {
					local nextnum = `num' + 35*(`i'-1)
					replace beta`num' = beta`nextnum' if _n==`i'
				}
			}
			
			gen dataset = "UK"
			gen outcome = "Failed" if _n==1
			replace outcome = "Voluntary Removal" if _n==2
			replace outcome = "Other Removal" if _n==3
			tab outcome
			l			
			
			// rename variables and drop unnecessary ones
			
			drop beta71-beta140
			/*
			local varlist = "" 
			
			foreach var in beta36-beta70 {
				rename `var' 
			
			rename beta36 Cultureandrecreation
			*/
			
			// Graph results
			
			twoway (line 
			
		*/	
			
	
			
		
		/* See regression diagnostics from Leverhulme and Notif Events projects */
