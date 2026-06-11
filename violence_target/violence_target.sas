options nocenter validvarname=any;

*---Read in space-delimited ascii file;

data new_data;

infile 'violence_target.dat' lrecl=115 missover DSD DLM=' ' print;
input
  C0000100
  C0000200
  C0005300
  C0005400
  C0005700
  C0730700
  C0942400
  Y0375300
  Y0375900
  Y0376500
  Y0669000
  Y0669600
  Y0670200
  Y0966400
  Y0967000
  Y0967600
  Y1176200
  Y1415900
  Y1416800
  Y1667300
  Y1668200
  Y1940600
  Y1941500
  Y2256600
  Y2257500
  Y2267000
  Y2608200
  Y2609100
  Y2958300
  Y2959200
  Y3325701
  Y3670801
  Y4275601
  Y4596801
;
array nvarlist _numeric_;

*---Recode missing values to SAS custom system missing. See SAS
      documentation for use of MISSING option in procedures, e.g. PROC FREQ;

do over nvarlist;
  if nvarlist = -1 then nvarlist = .R;  /* Refused */
  if nvarlist = -2 then nvarlist = .D;  /* Dont know */
  if nvarlist = -3 then nvarlist = .I;  /* Invalid missing */
  if nvarlist = -7 then nvarlist = .M;  /* Missing */
end;

  label C0000100 = "ID CODE OF CHILD";
  label C0000200 = "ID CODE OF MOTHER OF CHILD";
  label C0005300 = "RACE OF CHILD (FROM MOTHERS SCREENER 79)";
  label C0005400 = "SEX OF CHILD";
  label C0005700 = "DATE OF BIRTH OF CHILD - YEAR";
  label C0730700 = "HURT SOMEONE BAD ENOUGH TO NEED A DR";
  label C0942400 = "# TIMES HURT SOMEONE TO NEED A DOCTOR";
  label Y0375300 = "IN PAST YR GOT IN SCHOOL/WORK FIGHT   94 1994";
  label Y0375900 = "IN PAST YR ATTACKED TO SERIOUSLY HURT 94 1994";
  label Y0376500 = "IN PAST YR HURT SOMEONE TO NEED DOCTR 94 1994";
  label Y0669000 = "IN PAST YR GOT IN SCHOOL/WORK FIGHT   96 1996";
  label Y0669600 = "IN PAST YR ATTACKED TO SERIOUSLY HURT 96 1996";
  label Y0670200 = "IN PAST YR HURT SOMEONE TO NEED DOCTR 96 1996";
  label Y0966400 = "IN PAST YR GOT IN SCHOOL/WORK FIGHT 1998";
  label Y0967000 = "IN PAST YR ATTACK TO SERIOUSLY HURT 1998";
  label Y0967600 = "IN PAST YR HURT SOMEONE TO NEED DR 1998";
  label Y1176200 = "IN LAST YR GOT IN PHYSICAL FIGHT AT SCHOOL OR WORK 2000";
  label Y1415900 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2002";
  label Y1416800 = "IN LAST YR GOT IN PHYSICAL FIGHT AT SCHOOL OR WORK 2002";
  label Y1667300 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2004";
  label Y1668200 = "IN LAST YR GOT IN PHYSICAL FIGHT AT SCHOOL OR WORK 2004";
  label Y1940600 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2006";
  label Y1941500 = "IN LAST YR GOT IN PHYSICAL FIGHT AT SCHOOL OR WORK 2006";
  label Y2256600 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2008";
  label Y2257500 = "IN LAST YR GOT IN PHYSICAL FIGHT AT SCHOOL OR WORK 2008";
  label Y2267000 = "VERSION_R29 CHILD/YOUNG ADULT XRND";
  label Y2608200 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2010";
  label Y2609100 = "IN LAST YR GOT IN PHYSICAL FIGHT AT SCHOOL OR WORK 2010";
  label Y2958300 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2012";
  label Y2959200 = "IN LAST YR GOT IN PHYSICAL FIGHT AT SCHOOL OR WORK 2012";
  label Y3325701 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2014";
  label Y3670801 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2016";
  label Y4275601 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2018";
  label Y4596801 = "TIMES IN LAST YR R HURT SOMEONE PHYSICALLY (CAT) 2020";

/*---------------------------------------------------------------------*
 *  Crosswalk for Reference number & Question name                     *
 *---------------------------------------------------------------------*
 * Uncomment and edit this RENAME statement to rename variables
 * for ease of use.  You may need to use  name literal strings
 * e.g.  'variable-name'n   to create valid SAS variable names, or 
 * alter variables similarly named across years.
 * This command does not guarantee uniqueness

 * See SAS documentation for use of name literals and use of the
 * VALIDVARNAME=ANY option.     
 *---------------------------------------------------------------------*/
  /* *start* */

* RENAME
  C0000100 = 'CPUBID_XRND'n
  C0000200 = 'MPUBID_XRND'n
  C0005300 = 'CRACE_XRND'n
  C0005400 = 'CSEX_XRND'n
  C0005700 = 'CYRB_XRND'n
  C0730700 = 'CS884221_1988'n
  C0942400 = 'CS906613_1990'n
  Y0375300 = 'YASR-61B_1994'n
  Y0375900 = 'YASR-61I_1994'n
  Y0376500 = 'YASR-61O_1994'n
  Y0669000 = 'YASR-61B_1996'n
  Y0669600 = 'YASR-61I_1996'n
  Y0670200 = 'YASR-61O_1996'n
  Y0966400 = 'YASR-61B_1998'n
  Y0967000 = 'YASR-61I_1998'n
  Y0967600 = 'YASR-61O_1998'n
  Y1176200 = 'YASR-61B_2000'n
  Y1415900 = 'YASR-60C_2002'n
  Y1416800 = 'YASR-61B_2002'n
  Y1667300 = 'YASR-60C_2004'n
  Y1668200 = 'YASR-61B_2004'n
  Y1940600 = 'YASR-60C_2006'n
  Y1941500 = 'YASR-61B_2006'n
  Y2256600 = 'YASR-60C_2008'n
  Y2257500 = 'YASR-61B_2008'n
  Y2267000 = 'VERSION_R29_XRND'n
  Y2608200 = 'YASR-60C_2010'n
  Y2609100 = 'YASR-61B_2010'n
  Y2958300 = 'YASR-60C_2012'n
  Y2959200 = 'YASR-61B_2012'n
  Y3325701 = 'YASR-60B-J~000002_2014'n
  Y3670801 = 'YASR-60B-J~000002_2016'n
  Y4275601 = 'YASR-60B-J~000002_2018'n
  Y4596801 = 'YASR-60B-J~000002_2020'n
;
  /* *finish* */
run;

proc means data=new_data n mean min max;
run;

/*---------------------------------------------------------------------*
 *  FORMATTED TABULATIONS                                              *
 *---------------------------------------------------------------------*
 * You can uncomment and edit the PROC FORMAT and PROC FREQ statements 
 * provided below to obtain formatted tabulations. The tabulations 
 * should reflect codebook values.
 * 
 * Please edit the formats below reflect any renaming of the variables
 * you may have done in the first data step. 
 *---------------------------------------------------------------------*/

/*
proc format;
value vx0f
  1-9999999='1 TO 9999999: See Min & Max values below for range as of this release'
;
value vx1f
  1-12686='1 TO 12686: NLSY79 Public ID'
;
value vx2f
  1='HISPANIC'
  2='BLACK'
  3='NON-BLACK, NON-HISPANIC'
;
value vx3f
  1='MALE'
  2='FEMALE'
;
value vx4f
  1970-1978='1970 TO 1978: < before 1979'
  1979='1979'
  1980='1980'
  1981='1981'
  1982='1982'
  1983='1983'
  1984='1984'
  1985='1985'
  1986='1986'
  1987='1987'
  1988='1988'
  1989='1989'
  1990='1990'
  1991='1991'
  1992='1992'
  1993='1993'
  1994='1994'
  1995='1995'
  1996='1996'
  1997='1997'
  1998='1998'
  1999='1999'
  2000='2000'
  2001='2001'
  2002='2002'
  2003='2003'
  2004='2004'
  2005='2005'
  2006='2006'
  2007='2007'
  2008='2008'
  2009='2009'
  2010='2010'
  2011='2011'
  2012='2012'
  2013='2013'
  2014='2014'
  2015='2015'
  2016='2016'
  2017='2017'
  2018='2018'
  2019='2019'
  2020='2020'
  2021='2021'
;
value vx5f
  0='NEVER'
  1='ONCE'
  2='TWICE'
  3='MORE THAN TWICE'
;
value vx6f
  0='NEVER'
  1='ONCE'
  2='TWICE'
  3='MORE THAN TWICE'
;
value vx7f
  1='1: YES'
  0='0: NO'
;
value vx8f
  1='1: YES'
  0='0: NO'
;
value vx9f
  1='1: YES'
  0='0: NO'
;
value vx10f
  1='1: YES'
  0='0: NO'
;
value vx11f
  1='1: YES'
  0='0: NO'
;
value vx12f
  1='1: YES'
  0='0: NO'
;
value vx13f
  1='1: YES'
  0='0: NO'
;
value vx14f
  1='1: YES'
  0='0: NO'
;
value vx15f
  1='1: YES'
  0='0: NO'
;
value vx16f
  1='Yes'
  0='No'
;
value vx17f
  1='Never'
  2='Once'
  3='Twice'
  4='More than twice'
;
value vx18f
  1='Yes'
  0='No'
;
value vx19f
  1='Never'
  2='Once'
  3='Twice'
  4='More than twice'
;
value vx20f
  1='Yes'
  0='No'
;
value vx21f
  1='Never'
  2='Once'
  3='Twice'
  4='More than twice'
;
value vx22f
  1='Yes'
  0='No'
;
value vx23f
  1='Never'
  2='Once'
  3='Twice'
  4='More than twice'
;
value vx24f
  1='Yes'
  0='No'
;
value vx25f
  532='532'
;
value vx26f
  1='Never'
  2='Once'
  3='Twice'
  4='More than twice'
;
value vx27f
  1='Yes'
  0='No'
;
value vx28f
  1='Never'
  2='Once'
  3='Twice'
  4='More than twice'
;
value vx29f
  1='Yes'
  0='No'
;
value vx30f
  1='Never'
  2='Once'
  3='Twice'
  4='More than twice'
;
value vx31f
  1='Never'
  2='Once'
  3='Twice'
  4='More than twice'
;
value vx32f
  1='NEVER'
  2='ONCE'
  3='TWICE'
  4='MORE THAN TWICE'
;
value vx33f
  1='NEVER'
  2='ONCE'
  3='TWICE'
  4='MORE THAN TWICE'
;
*/

/* 
 *--- Tabulations using reference number variables;
proc freq data=new_data;
tables _ALL_ /MISSING;
  format C0000100 vx0f.;
  format C0000200 vx1f.;
  format C0005300 vx2f.;
  format C0005400 vx3f.;
  format C0005700 vx4f.;
  format C0730700 vx5f.;
  format C0942400 vx6f.;
  format Y0375300 vx7f.;
  format Y0375900 vx8f.;
  format Y0376500 vx9f.;
  format Y0669000 vx10f.;
  format Y0669600 vx11f.;
  format Y0670200 vx12f.;
  format Y0966400 vx13f.;
  format Y0967000 vx14f.;
  format Y0967600 vx15f.;
  format Y1176200 vx16f.;
  format Y1415900 vx17f.;
  format Y1416800 vx18f.;
  format Y1667300 vx19f.;
  format Y1668200 vx20f.;
  format Y1940600 vx21f.;
  format Y1941500 vx22f.;
  format Y2256600 vx23f.;
  format Y2257500 vx24f.;
  format Y2267000 vx25f.;
  format Y2608200 vx26f.;
  format Y2609100 vx27f.;
  format Y2958300 vx28f.;
  format Y2959200 vx29f.;
  format Y3325701 vx30f.;
  format Y3670801 vx31f.;
  format Y4275601 vx32f.;
  format Y4596801 vx33f.;
run;
*/

/*
*--- Tabulations using default named variables;
proc freq data=new_data;
tables _ALL_ /MISSING;
  format 'CPUBID_XRND'n vx0f.;
  format 'MPUBID_XRND'n vx1f.;
  format 'CRACE_XRND'n vx2f.;
  format 'CSEX_XRND'n vx3f.;
  format 'CYRB_XRND'n vx4f.;
  format 'CS884221_1988'n vx5f.;
  format 'CS906613_1990'n vx6f.;
  format 'YASR-61B_1994'n vx7f.;
  format 'YASR-61I_1994'n vx8f.;
  format 'YASR-61O_1994'n vx9f.;
  format 'YASR-61B_1996'n vx10f.;
  format 'YASR-61I_1996'n vx11f.;
  format 'YASR-61O_1996'n vx12f.;
  format 'YASR-61B_1998'n vx13f.;
  format 'YASR-61I_1998'n vx14f.;
  format 'YASR-61O_1998'n vx15f.;
  format 'YASR-61B_2000'n vx16f.;
  format 'YASR-60C_2002'n vx17f.;
  format 'YASR-61B_2002'n vx18f.;
  format 'YASR-60C_2004'n vx19f.;
  format 'YASR-61B_2004'n vx20f.;
  format 'YASR-60C_2006'n vx21f.;
  format 'YASR-61B_2006'n vx22f.;
  format 'YASR-60C_2008'n vx23f.;
  format 'YASR-61B_2008'n vx24f.;
  format 'VERSION_R29_XRND'n vx25f.;
  format 'YASR-60C_2010'n vx26f.;
  format 'YASR-61B_2010'n vx27f.;
  format 'YASR-60C_2012'n vx28f.;
  format 'YASR-61B_2012'n vx29f.;
  format 'YASR-60B-J~000002_2014'n vx30f.;
  format 'YASR-60B-J~000002_2016'n vx31f.;
  format 'YASR-60B-J~000002_2018'n vx32f.;
  format 'YASR-60B-J~000002_2020'n vx33f.;
run;
*/