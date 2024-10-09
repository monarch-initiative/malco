"""This script looks for correlations between the ability of an LLM to 
diagnose the correct disease and certain parameters.

(1) The first idea is using time, namely dates of discovery, as a way to capture how much of a 
disease is present in the web. This is a proxy for how much an LLM knows about such a diseases.
We use HPOA, we do not parse out disease genes discovered after 2008 though (first thing in HPOA)

(2) Then we could look at some IC(prompt) as a second proxy. To start, avg(IC) as computed with

`runoak -g hpoa_file -G hpoa -i hpo_file  information-content -p i --use-associations .all`

Finally, if the two things correlate, can we use them to train a logit or SVM to predict whether
the LLM will be successfull or not?
"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import sys
import os
import pandas as pd
import numpy as np
import datetime as dt
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import json
import re
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# (1) HPOA for dates
# HPOA import and setup
hpoa_file_path = Path.home() / "data" / "phenotype.hpoa"
hpoa_df = pd.read_csv(
        hpoa_file_path, sep="\t" , header=4
    )

labels_to_drop = ["disease_name", "qualifier", "hpo_id", "reference", "evidence",
                   "onset", "frequency", "sex", "modifier", "aspect"]
hpoa_df = hpoa_df.drop(columns=labels_to_drop)

hpoa_df['date'] = hpoa_df["biocuration"].str.extract(r'\[(.*?)\]')
hpoa_df = hpoa_df.drop(columns='biocuration')
hpoa_df = hpoa_df[hpoa_df['database_id'].str.startswith("OMIM")]

hpoa_unique = hpoa_df.groupby("database_id").date.min()
# Now length 8251, and e.g. hpoa_unique.loc["OMIM:620662"] -> '2024-04-15'

# import df of results
model = str(sys.argv[1])
try:
   make_time_plot = str(sys.argv[2])=="plot"
except IndexError:
   make_time_plot = False
   print("\nYou can pass \"plot\" as a second CLI argument and this will generate nice plots!")

ranking_results_filename = f"out_openAI_models/multimodel/{model}/full_df_results.tsv"
rank_results_df = pd.read_csv(
        ranking_results_filename, sep="\t" 
    )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# As some exploratory data analysis, let us divide the set into two and look for
# some properties. Meanwhile, create dictonary necessary for linear regression.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Go through results data and make set of found vs not found diseases.
found_diseases = []
not_found_diseases = []
rank_date_dict = {} 
ppkts = rank_results_df.groupby("label")[["term", "correct_term", "is_correct", "rank"]] 
for ppkt in ppkts:
   # ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe 
   disease = ppkt[1].iloc[0]['correct_term']

   if any(ppkt[1]["is_correct"]):
      found_diseases.append(disease)
      index_of_match = ppkt[1]["is_correct"].to_list().index(True)
      try:
         rank = ppkt[1].iloc[index_of_match]["rank"] # inverse rank does not work well
         rank_date_dict[ppkt[0]] = [rank.item(), 
                                    hpoa_unique.loc[ppkt[1].iloc[0]["correct_term"]]]
      except (ValueError, KeyError) as e:
         print(f"Error {e} for {ppkt[0]}, disease {ppkt[1].iloc[0]['correct_term']}.")

   else: 
      not_found_diseases.append(disease)
      try:
         rank_date_dict[ppkt[0]] = [None,
                                    hpoa_unique.loc[ppkt[1].iloc[0]["correct_term"]]]
      except (ValueError, KeyError) as e:
         pass
         #TODO collect the below somewhere
         #print(f"Error {e} for {ppkt[0]}, disease {ppkt[1].iloc[0]['correct_term']}.")
         
# gpt-4o output, reasonable enough to throw out 62 cases ~1%. 3 OMIMs to check and 3 nan
# len(rank_date_dict) --> 6625
# len(ppkts) --> 6687

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Do linear regression of box plot of ppkts' rank vs time
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
dates = []
ranks = []

for key, data in rank_date_dict.items():
   dates.append(dt.datetime.strptime(data[1], '%Y-%m-%d').date())
   ranks.append(data[0])
   
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Correlation? Not evident from the following:
years_only = []
for i in range(len(dates)): 
   years_only.append(dates[i].year)

if make_time_plot:
   sns.boxplot(x=years_only, y=ranks)
   plt.xlabel("Year of HPOA annotation")
   plt.ylabel("Rank")
   plt.title("LLM performance uncorrelated with date of discovery")
   plt.show()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Statistical test, simplest idea: chi2 of contingency table with:
# y<=2009 and y>2009 clmns and found vs not-found counts, one count per ppkt
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cont_table = [[0, 0], [0, 0]] # contains counts
# ___| < 2010 | > 2010 |
#  f |        |        | (found)
# nf |        |        | (not found)
for i, d in enumerate(years_only):
   if d < 2010:
      if ranks[i] == None:
         cont_table[0][1] += 1
      else:
         cont_table[0][0] += 1
   else:
      if ranks[i] == None:
         cont_table[1][1] += 1
      else:
         cont_table[1][0] += 1

# ___| y<2010 | y>=2010|
#  f |  1295  |  1204  | (found)
# nf |  1064  |  3062  | (not found)

# H0: no correlation between clmn 1 and 2
from scipy.stats import chi2_contingency
res = chi2_contingency(cont_table) #res.statistic = chi2?
# Chi2ContingencyResult(statistic=np.float64(458.8912809317326), pvalue=np.float64(8.37853926348694e-102), dof=1, expected_freq=array([[ 889.83260377, 1609.16739623],
#       [1469.16739623, 2656.83260377]]))

contingency_table = pd.DataFrame(cont_table, index=['found', 'not_found'], 
                                 columns=['before2010', 'after2010'])
row_totals = [ cont_table[0][0] + cont_table[0][1],
               cont_table[1][0] + cont_table[1][1] ]
column_totals = [ cont_table[0][0] + cont_table[1][0],
                  cont_table[0][1] + cont_table[1][1] ]
N = row_totals[0] + row_totals[1]





# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# IC: For each phenpacket, list observed HPOs and compute average IC. Is it correlated with 
# success? I.e., start with f/nf, 1/0 on y-axis vs avg(IC) on x-axis

# Import file as dict
ic_file = "data/ic_hpoa.txt"
with open(ic_file) as f:
    ic_dict = dict(i.rstrip().split(None, 1) for i in f)


original_ppkt_dir = Path.home() / "data" / "phenopacket-store"
ppkt_ic = {}
missing_in_ic_dict = []
ppkts_with_zero_hpos = []

ppkts_with_missing_hpos = []
sanity_check = 0
# Iterate over ppkts, which are json. 
for subdir, dirs, files in os.walk(original_ppkt_dir):
   # For each ppkt
   for filename in files:
      if filename.endswith('.json'):
         sanity_check += 1
         file_path = os.path.join(subdir, filename)
         with open(file_path, mode="r", encoding="utf-8") as read_file:
            ppkt = json.load(read_file)
         ppkt_id = re.sub('[^\\w]', '_', ppkt['id'])
         # replaceAll("[^\\w]","_")
         ic = 0 
         num_hpos = 0
         # For each HPO
         for i in ppkt['phenotypicFeatures']:
            try:
               if i["excluded"]: # skip excluded
                  continue
            except KeyError:
               pass
            hpo = i["type"]["id"]
            try:
               ic += float(ic_dict[hpo])
               num_hpos += 1
            except KeyError as e:
               missing_in_ic_dict.append(e.args[0])
               ppkts_with_missing_hpos.append(ppkt_id)

               #print(f"No entry for {e}.")
            
         # For now we are fine with average IC
         try:
            ppkt_ic[ppkt_id] = ic/num_hpos
         except ZeroDivisionError as e: 
            # TODO to exit L161 loop w/ num_hpos=0 one may have L166 and then L171!
            ppkts_with_zero_hpos.append(ppkt_id)
            #print(f"No HPOs for {ppkt["id"]}.")
  
missing_in_ic_dict_unique = set(missing_in_ic_dict)
ppkts_with_missing_hpos = set(ppkts_with_missing_hpos)
print(f"\nNumber of (unique) HPOs without IC-value is {len(missing_in_ic_dict_unique)}.") # 65
print(f"Number of ppkts with zero observed HPOs is {len(ppkts_with_zero_hpos)}.") # 141
print(f"Number of ppkts where some HPOs are missing at least 1 IC value is {len(ppkts_with_missing_hpos)}.\n") # 172

ppkt_ic_df = pd.DataFrame.from_dict(ppkt_ic, orient='index', columns=['avg(IC)'])
ppkt_ic_df['Diagnosed'] = 0

still_missing = []
debug_counter = 0
for ppkt in ppkts:
   # debug_counter += 1
   # if debug_counter % 500 == 0:
   #    breakpoint()
   if any(ppkt[1]["is_correct"]):
      ppkt_label = ppkt[0].replace('_en-prompt.txt','')
      if ppkt_label in ppkts_with_zero_hpos:
         continue
      try:
         ppkt_ic_df.loc[ppkt_label,'Diagnosed'] = 1 
         # somehow this code generates new entries in df. From a code perspective it's bad and
         # should be changed TODO
      except :
         if ppkt_label in ppkts_with_zero_hpos:
            continue
         else:
            still_missing.append(ppkt_label)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# See https://github.com/monarch-initiative/phenopacket-store/issues/157
label_manual_removal = ["PMID_27764983_Family_1_individual__J", 
                        "PMID_35991565_Family_I__3"]
ppkt_ic_df = ppkt_ic_df.drop(label_manual_removal)
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ppkt_ic_df['Diagnosed'].value_counts()
# Diagnosed
# 0.0    4182
# 1.0    2347
# IMBALANCED! Maybe SMOTE or similar? Respectively 
# 0.0    64 %
# 1.0    36 %


#ppkt_ic_df.plot(x='avg(IC)', y='Diagnosed', style=['ob','rx'])
# Dumbly copy paste from
# https://towardsdatascience.com/building-a-logistic-regression-in-python-step-by-step-becd4d56c9c8 [1/10/24]

# cols=['euribor3m', 'job_blue-collar', 'job_housemaid', 'marital_unknown', 'education_illiterate', 
#       'month_apr', 'month_aug', 'month_dec', 'month_jul', 'month_jun', 'month_mar', 
#       'month_may', 'month_nov', 'month_oct', "poutcome_failure", "poutcome_success"] 
# X=os_data_X[cols]
# y=os_data_y['y']logit_model=sm.Logit(y,X)
# result=logit_model.fit()
# print(result.summary2())

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report

X_train, X_test, y_train, y_test = train_test_split(ppkt_ic_df[['avg(IC)']], ppkt_ic_df['Diagnosed'], test_size=0.3, random_state=0)
logreg = LogisticRegression()
logreg.fit(X_train, y_train)
y_pred = logreg.predict(X_test)
print('Accuracy of logistic regression classifier on test set: {:.2f}'.format(logreg.score(X_test, y_test)))
confusion_matrix = confusion_matrix(y_test, y_pred)
print(confusion_matrix)
class_report = classification_report(y_test, y_pred)
print(class_report)
# Not much better than always saying 0, as of now.

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Analysis of found vs not-found
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
found_set = set(found_diseases)
notfound_set = set(not_found_diseases)
all_set = found_set | notfound_set
# len(all_set) --> 476

# compute the overlap of found vs not-found disesases
overlap = []

for i in found_set:
   if i in notfound_set:
      overlap.append(i)

print(f"Number of found diseases by {model} is {len(found_set)}.")
print(f"Number of not found diseases by {model} is {len(notfound_set)}.")
print(f"Found diseases also present in not-found set, by {model} is {len(overlap)}.\n")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Look at the 263-129 (gpt-4o) found diseases not present in not-found set ("always found") 
# and the opposite namely "never found" diseases. Average date of two sets is?

always_found = found_set - notfound_set # 134
never_found = notfound_set - found_set # 213
# meaning 347/476, 27% sometimes found sometimes not, 28% always found, 45% never found.

# Compute average date of always vs never found diseases
results_dict = {} # turns out being 281 long 
found_dict = {}
notfound_dict = {}

results_df = pd.DataFrame(columns=["disease", "found", "date"])
# TODO get rid of next line
hpoa_df.drop_duplicates(subset='database_id', inplace=True)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
for af in always_found:
   try:
      results_dict[af] = [True, hpoa_df.loc[hpoa_df['database_id'] == af, 'date'].item() ]
      found_dict[af] = hpoa_df.loc[hpoa_df['database_id'] == af, 'date'].item()
      results_df
   except ValueError:
      print(f"No HPOA for {af}.")
for nf in never_found:
   try:
      results_dict[nf] = [False, hpoa_df.loc[hpoa_df['database_id'] == nf, 'date'].item() ]
      notfound_dict[nf] = hpoa_df.loc[hpoa_df['database_id'] == af, 'date'].item()
   except ValueError:
      print(f"No HPOA for {nf}.")

res_to_clean = pd.DataFrame.from_dict(results_dict).transpose()
res_to_clean.columns=["found","date"]
res_to_clean['date'] = pd.to_datetime(res_to_clean.date).values.astype(np.int64)
final_avg = pd.DataFrame(pd.to_datetime(res_to_clean.groupby('found').mean()['date']))
print(final_avg)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 2 dimensional logistic regression or SVM with gausskernel?