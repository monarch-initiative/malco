# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
rank_date_dict = {} # Maybe dict is not a super good idea
ppkts = rank_results_df.groupby("label")[["term", "correct_term", "is_correct", "rank"]] 
for ppkt in ppkts:
    # is there a true? ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe 
   disease = ppkt[1].iloc[0]['correct_term']

   if any(ppkt[1]["is_correct"]):
      found_diseases.append(disease)
      index_of_match = ppkt[1]["is_correct"].to_list().index(True)
      try:
         #inverse_rank = 1/ppkt[1].iloc[index_of_match]["rank"] # np.float64
         rank = ppkt[1].iloc[index_of_match]["rank"] # np.float64
         rank_date_dict[ppkt[0]] = [rank.item(), 
                                    hpoa_unique.loc[ppkt[1].iloc[0]["correct_term"]]]
      except (ValueError, KeyError) as e:
         print(f"Error {e} for {ppkt[0]}, disease {ppkt[1].iloc[0]['correct_term']}.")

   else: 
      not_found_diseases.append(disease)
      continue # only use diseases that have been found
      try:
         rank_date_dict[ppkt[0]] = [None, # only use diseases that have been found
                                    hpoa_unique.loc[ppkt[1].iloc[0]["correct_term"]]]
      except (ValueError, KeyError) as e:
         print(f"Error {e} for {ppkt[0]}, disease {ppkt[1].iloc[0]['correct_term']}.")
         
# gpt-4o output, reasonable enough to throw out 62 cases ~1%. 3 OMIMs to check and 3 nan
# len(rank_date_dict) --> 6625
# len(ppkts) --> 6687

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Do linear regression of box plot of ppkts' rank vs time
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=365))
dates = []
ranks = []
for key, data in rank_date_dict.items():
    #rank, date_str = zip(*data_list)  # Unpack
    # necessary to convert to date object?
    #dates = convert_str_to_dates(dates_str)  # Not handled in example
    #plt.plot(date_str, rank, label=key)
    dates.append(dt.datetime.strptime(data[1], '%Y-%m-%d').date())
    ranks.append(data[0])

#plt.legend()
#plt.plot(dates, ranks, 'xr')
#plt.gcf().autofmt_xdate()
#plt.show()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Correlation? Not evident from the following:
years_only = []
for i in range(len(dates)): 
   years_only.append(dates[i].year)

sns.boxplot(x=years_only,y=ranks)
plt.xlabel("Year of HPOA annotation")
plt.ylabel("Rank")
plt.title("LLM performance uncorrelated with date of discovery")
#plt.show()

#years_range = np.array([i for i in range(2009,2025)]) # bins
#year_indices = np.digitize(years_only,years_range)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Statistical test, simplest idea: chi2 of contingency table with:
# y<=2009 and y>2009 clmns and found vs not-found counts, one count per ppkt
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


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

# Iterate over ppkts, which are json. 
for subdir, dirs, files in os.walk(original_ppkt_dir):
   # For each ppkt
   for filename in files:
      if filename.endswith('.json'):
         file_path = os.path.join(subdir, filename)
         with open(file_path, mode="r", encoding="utf-8") as read_file:
            ppkt = json.load(read_file)
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
               #print(f"No entry for {e}.")
            
         # For now we are fine with average IC
         try:
            ppkt_ic[ppkt["id"]] = ic/num_hpos
         except ZeroDivisionError as e:
            ppkts_with_zero_hpos.append(ppkt["id"])
            #print(f"No HPOs for {ppkt["id"]}.")

missing_in_ic_dict_unique = set(missing_in_ic_dict)
print(f"\nNumber of HPOs without IC-value is {len(missing_in_ic_dict_unique)}.") # 191
print(f"Number of ppkts with zero observed HPOs is {len(ppkts_with_zero_hpos)}.\n") # 141
breakpoint()
ppkt_ic_df = pd.DataFrame.from_dict(ppkt_ic, orient='index', columns=['avg(IC)'])
ppkt_ic_df['Diagnosed'] = 0

still_missing = []

for ppkt in ppkts:
   if any(ppkt[1]["is_correct"]):
      ppkt_label = ppkt[0][0:-14]
      try:
         ppkt_ic_df.loc[ppkt_label,'Diagnosed'] = 1 
         # somehow this code generates new entries in df. From a code perspective it's bad and
         # should be changed, but before, why? Is there some error? TODO
      except :
         if ppkt_label in ppkts_with_zero_hpos:
            continue
         else:
            still_missing.append(ppkt_label)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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