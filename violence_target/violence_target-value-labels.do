

label define vlC0005300 1 "HISPANIC" 2 "BLACK" 3 "NON-BLACK, NON-HISPANIC" 
label values C0005300 vlC0005300

label define vlC0005400 1 "MALE" 2 "FEMALE" 
label values C0005400 vlC0005400

label define vlC0005700 1970 "1970 TO 1978: < before 1979" 1979 "1979" 1980 "1980" 1981 "1981" 1982 "1982" 1983 "1983" 1984 "1984" 1985 "1985" 1986 "1986" 1987 "1987" 1988 "1988" 1989 "1989" 1990 "1990" 1991 "1991" 1992 "1992" 1993 "1993" 1994 "1994" 1995 "1995" 1996 "1996" 1997 "1997" 1998 "1998" 1999 "1999" 2000 "2000" 2001 "2001" 2002 "2002" 2003 "2003" 2004 "2004" 2005 "2005" 2006 "2006" 2007 "2007" 2008 "2008" 2009 "2009" 2010 "2010" 2011 "2011" 2012 "2012" 2013 "2013" 2014 "2014" 2015 "2015" 2016 "2016" 2017 "2017" 2018 "2018" 2019 "2019" 2020 "2020" 2021 "2021" 
label values C0005700 vlC0005700

label define vlC0730700 0 "NEVER" 1 "ONCE" 2 "TWICE" 3 "MORE THAN TWICE" 
label values C0730700 vlC0730700

label define vlC0942400 0 "NEVER" 1 "ONCE" 2 "TWICE" 3 "MORE THAN TWICE" 
label values C0942400 vlC0942400

label define vlY0375300 1 "1: YES" 0 "0: NO" 
label values Y0375300 vlY0375300

label define vlY0375900 1 "1: YES" 0 "0: NO" 
label values Y0375900 vlY0375900

label define vlY0376500 1 "1: YES" 0 "0: NO" 
label values Y0376500 vlY0376500

label define vlY0669000 1 "1: YES" 0 "0: NO" 
label values Y0669000 vlY0669000

label define vlY0669600 1 "1: YES" 0 "0: NO" 
label values Y0669600 vlY0669600

label define vlY0670200 1 "1: YES" 0 "0: NO" 
label values Y0670200 vlY0670200

label define vlY0966400 1 "1: YES" 0 "0: NO" 
label values Y0966400 vlY0966400

label define vlY0967000 1 "1: YES" 0 "0: NO" 
label values Y0967000 vlY0967000

label define vlY0967600 1 "1: YES" 0 "0: NO" 
label values Y0967600 vlY0967600

label define vlY1176200 1 "Yes" 0 "No" 
label values Y1176200 vlY1176200

label define vlY1415900 1 "Never" 2 "Once" 3 "Twice" 4 "More than twice" 
label values Y1415900 vlY1415900

label define vlY1416800 1 "Yes" 0 "No" 
label values Y1416800 vlY1416800

label define vlY1667300 1 "Never" 2 "Once" 3 "Twice" 4 "More than twice" 
label values Y1667300 vlY1667300

label define vlY1668200 1 "Yes" 0 "No" 
label values Y1668200 vlY1668200

label define vlY1940600 1 "Never" 2 "Once" 3 "Twice" 4 "More than twice" 
label values Y1940600 vlY1940600

label define vlY1941500 1 "Yes" 0 "No" 
label values Y1941500 vlY1941500

label define vlY2256600 1 "Never" 2 "Once" 3 "Twice" 4 "More than twice" 
label values Y2256600 vlY2256600

label define vlY2257500 1 "Yes" 0 "No" 
label values Y2257500 vlY2257500

label define vlY2267000 532 "532" 
label values Y2267000 vlY2267000

label define vlY2608200 1 "Never" 2 "Once" 3 "Twice" 4 "More than twice" 
label values Y2608200 vlY2608200

label define vlY2609100 1 "Yes" 0 "No" 
label values Y2609100 vlY2609100

label define vlY2958300 1 "Never" 2 "Once" 3 "Twice" 4 "More than twice" 
label values Y2958300 vlY2958300

label define vlY2959200 1 "Yes" 0 "No" 
label values Y2959200 vlY2959200

label define vlY3325701 1 "Never" 2 "Once" 3 "Twice" 4 "More than twice" 
label values Y3325701 vlY3325701

label define vlY3670801 1 "Never" 2 "Once" 3 "Twice" 4 "More than twice" 
label values Y3670801 vlY3670801

label define vlY4275601 1 "NEVER" 2 "ONCE" 3 "TWICE" 4 "MORE THAN TWICE" 
label values Y4275601 vlY4275601

label define vlY4596801 1 "NEVER" 2 "ONCE" 3 "TWICE" 4 "MORE THAN TWICE" 
label values Y4596801 vlY4596801

/* Crosswalk for Reference number & Question name
 * Uncomment and edit this RENAME statement to rename variables for ease of use.
 * This command does not guarantee uniqueness
 */
  /* *start* */
/*
  rename C0000100 CPUBID_XRND
  rename C0000200 MPUBID_XRND
  rename C0005300 CRACE_XRND
  rename C0005400 CSEX_XRND
  rename C0005700 CYRB_XRND
  rename C0730700 CS884221_1988
  rename C0942400 CS906613_1990
  rename Y0375300 YASR_61B_1994   // YASR-61B
  rename Y0375900 YASR_61I_1994   // YASR-61I
  rename Y0376500 YASR_61O_1994   // YASR-61O
  rename Y0669000 YASR_61B_1996   // YASR-61B
  rename Y0669600 YASR_61I_1996   // YASR-61I
  rename Y0670200 YASR_61O_1996   // YASR-61O
  rename Y0966400 YASR_61B_1998   // YASR-61B
  rename Y0967000 YASR_61I_1998   // YASR-61I
  rename Y0967600 YASR_61O_1998   // YASR-61O
  rename Y1176200 YASR_61B_2000   // YASR-61B
  rename Y1415900 YASR_60C_2002   // YASR-60C
  rename Y1416800 YASR_61B_2002   // YASR-61B
  rename Y1667300 YASR_60C_2004   // YASR-60C
  rename Y1668200 YASR_61B_2004   // YASR-61B
  rename Y1940600 YASR_60C_2006   // YASR-60C
  rename Y1941500 YASR_61B_2006   // YASR-61B
  rename Y2256600 YASR_60C_2008   // YASR-60C
  rename Y2257500 YASR_61B_2008   // YASR-61B
  rename Y2267000 VERSION_R29_XRND
  rename Y2608200 YASR_60C_2010   // YASR-60C
  rename Y2609100 YASR_61B_2010   // YASR-61B
  rename Y2958300 YASR_60C_2012   // YASR-60C
  rename Y2959200 YASR_61B_2012   // YASR-61B
  rename Y3325701 YASR_60B_J_000002_2014   // YASR-60B-J~000002
  rename Y3670801 YASR_60B_J_000002_2016   // YASR-60B-J~000002
  rename Y4275601 YASR_60B_J_000002_2018   // YASR-60B-J~000002
  rename Y4596801 YASR_60B_J_000002_2020   // YASR-60B-J~000002
*/
  /* *end* */

/* To convert variable names to lower case use the TOLOWER command
 *      (type findit tolower and follow the links to install).
 * TOLOWER VARLIST will change listed variables to lower case;
 *  TOLOWER without a specified variable list will convert all variables in the dataset to lower case
 */
/* tolower */
