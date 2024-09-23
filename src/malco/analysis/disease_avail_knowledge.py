# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This script looks for correlations between the ability of an LLM to 
# diagnose the correct disease and certain parameters.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The main points are using time, namely dates of discovery, as a way to capture how much of a 
# disease is present in the web. This is a proxy for how much an LLM knows about such a diseases.
# We use HPOA, we need to parse out disease genes discovered after 2008 or 9 (First thing in HPOA)
# 
# Then we could look at some IC(prompt) as a second proxy.
#
# Finally, if the two things correlate, can we use them to train a logit or SVM to predict whether
# the LLM will be successfull or not?
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import sys
import pandas as pd
import numpy as np
import datetime as dt
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# (1) HPOA for dates
# HPOA import and setup
hpoa_file_path = Path.home() / "data" / "phenotype.hpoa"
hpoa_df = pd.read_csv(
        hpoa_file_path, sep="\t" , header=4
    )

labels_to_drop = ["disease_name", "qualifier", "hpo_id", "reference", "evidence", "onset", "frequency", "sex", "modifier", "aspect"]
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
         inverse_rank = 1/ppkt[1].iloc[index_of_match]["rank"] # np.float64
         rank_date_dict[ppkt[0]] = [inverse_rank.item(), 
                                    hpoa_unique.loc[ppkt[1].iloc[0]["correct_term"]]]
      except (ValueError, KeyError) as e:
         print(f"Error {e} for {ppkt[0]}, disease {ppkt[1].iloc[0]['correct_term']}.")

   else: 
      not_found_diseases.append(disease)
      try:
         rank_date_dict[ppkt[0]] = [0.0, 
                                    hpoa_unique.loc[ppkt[1].iloc[0]["correct_term"]]]
      except (ValueError, KeyError) as e:
         print(f"Error {e} for {ppkt[0]}, disease {ppkt[1].iloc[0]['correct_term']}.")
         
# gpt-4o output, reasonable enough to throw out 62 cases ~1%. 3 OMIMs to check and 3 nan
# len(rank_date_dict) --> 6625
# len(ppkts) --> 6687

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Do linear regression of box plot of ppkts' 1/r vs time
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Plot TODO
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=365))
dates = []
invranks = []
for key, data in rank_date_dict.items():
    #rank, date_str = zip(*data_list)  # Unpack
    # necessary to convert to date object?
    #dates = convert_str_to_dates(dates_str)  # Not handled in example
    #plt.plot(date_str, rank, label=key)
    dates.append(dt.datetime.strptime(data[1], '%Y-%m-%d').date())
    invranks.append(data[0])

plt.plot(dates, invranks, 'xr')
#plt.legend()
plt.gcf().autofmt_xdate()
plt.show()
breakpoint()
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Correlation coefficient TODO

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Statistical test TODO


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Analysis of found vs not-found
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

found_set = set(found_diseases)
notfound_set = set(not_found_diseases)

# compute the overlap of found vs not-found disesases
overlap = []

for i in found_set:
   if i in notfound_set:
      overlap.append(i)

print(f"Number of found diseases by {model} is {len(found_set)}.")
print(f"Number of not found diseases by {model} is {len(notfound_set)}.")
print(f"Found diseases also present in not-found set, by {model} is {len(overlap)}.\n")
# Need some more statistic


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# One Idea 
# Look at the 263-129 (gpt-4o) found diseases not present in not-found set ("always found") 
# and the opposite namely "never found" diseases. Average date of two sets is?

always_found = found_set - notfound_set # 134
never_found = notfound_set - found_set # 213

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
res_to_clean.date = pd.to_datetime(res_to_clean.date).values.astype(np.int64)
final_avg = pd.DataFrame(pd.to_datetime(res_to_clean.groupby('found').mean().date))
print(final_avg)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 2 dimensional logistic regression or SVM with gausskernel?