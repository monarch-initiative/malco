import os 
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import pickle as pkl
from malco.post_process.mondo_score_utils import score_grounded_result
from malco.post_process.mondo_score_utils import omim_mappings
from typing import List
from oaklib.interfaces import OboGraphInterface


from oaklib import get_adapter


def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo") 

def compute_mrr(output_dir, prompt_dir, correct_answer_file,
                raw_results_dir) -> Path:
    # Read in results TSVs from self.output_dir that match glob results*tsv 
    results_data = []
    results_files = []
    num_ppkt = 0

    for subdir, dirs, files in os.walk(output_dir): # maybe change this so it only looks into multilingual/multimodel? I.e. use that as outputdir...?
        for filename in files:
            if filename.startswith("result") and filename.endswith(".tsv"):
                file_path = os.path.join(subdir, filename)
                df = pd.read_csv(file_path, sep="\t")
                num_ppkt = df["label"].nunique()
                results_data.append(df)
                # Append both the subdirectory relative to output_dir and the filename
                results_files.append(os.path.relpath(file_path, output_dir))
    # Read in correct answers from prompt_dir
    answers_path = os.path.join(os.getcwd(), prompt_dir, correct_answer_file)
    answers = pd.read_csv(
        answers_path, sep="\t", header=None, names=["description", "term", "label"]
    )

    # Mapping each label to its correct term
    label_to_correct_term = answers.set_index("label")["term"].to_dict()
    # Calculate the Mean Reciprocal Rank (MRR) for each file
    mrr_scores = []
    header = ["lang", "n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8", "n9", "n10", "n10p", "nf"]
    rank_df = pd.DataFrame(0, index=np.arange(len(results_files)), columns=header)

    cache_file = output_dir / "cache_log.txt"

    with cache_file.open('w', newline = '') as cf:
        now_is = datetime.now().strftime("%Y%m%d-%H%M%S")
        cf.write("Timestamp: " + now_is +"\n\n")
        mondo = mondo_adapter()
        i = 0
        for df in results_data:
            # For each label in the results file, find if the correct term is ranked
            df["rank"] = df.groupby("label")["score"].rank(ascending=False, method="first")
            label_4_non_eng = df["label"].str.replace("_[a-z][a-z]-prompt", "_en-prompt", regex=True)
            df["correct_term"] = label_4_non_eng.map(label_to_correct_term)

            # df['term'] is Mondo or OMIM ID, or even disease label
            # df['correct_term'] is an OMIM
            # call OAK and get OMIM IDs for df['term'] and see if df['correct_term'] is one of them
            # in the case of phenotypic series, if Mondo corresponds to grouping term, accept it

            # Calculate reciprocal rank
            # Make sure caching is used in the following by unwrapping explicitly
            results = []
            for idx, row in df.iterrows():
                val = score_grounded_result(row['term'], row['correct_term'], mondo)
                is_correct = val > 0
                results.append(is_correct)

            df['is_correct'] = results

            df["reciprocal_rank"] = df.apply(
                lambda row: 1 / row["rank"] if row["is_correct"] else 0, axis=1
            )

            # Save full data frame
            full_df_file = raw_results_dir / results_files[i].split("/")[0] / "full_df_results.tsv"
            df.to_csv(full_df_file, sep='\t', index=False)

            # Calculate MRR for this file
            mrr = df.groupby("label")["reciprocal_rank"].max().mean()
            mrr_scores.append(mrr)
            
            # Calculate top<n> of each rank
            rank_df.loc[i,"lang"] = results_files[i].split("/")[0]
            
            ppkts = df.groupby("label")[["rank","is_correct"]] 
            index_matches = df.index[df['is_correct']]
          
            # for each group
            for ppkt in ppkts:
                # is there a true? ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe 
                if not any(ppkt[1]["is_correct"]):
                    # no  --> increase nf = "not found"
                    rank_df.loc[i,"nf"] += 1       
                else:
                   # yes --> what's it rank? It's <j>
                   jind = ppkt[1].index[ppkt[1]['is_correct']]
                   j = int(ppkt[1]['rank'].loc[jind].values[0])
                   if j<11:
                       # increase n<j>
                       rank_df.loc[i,"n"+str(j)] += 1
                   else:
                       # increase n10p
                       rank_df.loc[i,"n10p"] += 1
            
            
            # Write cache charatcteristics to file
            cf.write(results_files[i])
            cf.write('\nscore_grounded_result cache info:\n')
            cf.write(str(score_grounded_result.cache_info()))
            cf.write('\nomim_mappings cache info:\n')
            cf.write(str(omim_mappings.cache_info()))
            cf.write('\n\n')
            i = i + 1

    
    plot_dir = output_dir / "plots"
    plot_dir.mkdir(exist_ok=True)
    topn_file = plot_dir / "topn_result.tsv"
    rank_df.to_csv(topn_file, sep='\t', index=False)

    print("MRR scores are:\n")
    print(mrr_scores)
    mrr_file = plot_dir / "mrr_result.tsv"

    # write out results for plotting 
    with mrr_file.open('w', newline = '') as dat:
        writer = csv.writer(dat, quoting = csv.QUOTE_NONNUMERIC, delimiter = '\t', lineterminator='\n')
        writer.writerow(results_files)
        writer.writerow(mrr_scores)
        
    return mrr_file, plot_dir, num_ppkt, topn_file
