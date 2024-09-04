import os 
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import pickle as pkl
import shutil

from oaklib.interfaces import OboGraphInterface
from oaklib.datamodels.vocabulary import IS_A
from oaklib.interfaces import MappingProviderInterface
from oaklib import get_adapter

from malco.post_process.df_save_util import safe_save_tsv
from malco.post_process.mondo_score_utils import score_grounded_result
from cachetools import LRUCache
from typing import List 
from cachetools.keys import hashkey
from shelved_cache import PersistentCache

FULL_SCORE = 1.0
PARTIAL_SCORE = 0.5

def cache_info(self):
    return f"CacheInfo: hits={self.hits}, misses={self.misses}, maxsize={self.wrapped.maxsize}, currsize={self.wrapped.currsize}"

def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo") 

def compute_mrr_and_ranks(
    comparing: str, 
    output_dir: Path, 
    out_subdir: str,
    prompt_dir: str, 
    correct_answer_file: str,
    ) -> Path:

    # Read in results TSVs from self.output_dir that match glob results*tsv 
    out_caches = output_dir / "caches"
    out_caches.mkdir(exist_ok=True)
    output_dir = output_dir / out_subdir
    results_data = []
    results_files = []
    num_ppkt = 0
    pc2_cache_file = str(out_caches / "score_grounded_result_cache")
    pc2 = PersistentCache(LRUCache, pc2_cache_file, maxsize=524288)        
    pc1_cache_file = str(out_caches / "omim_mappings_cache")
    pc1 = PersistentCache(LRUCache, pc1_cache_file, maxsize=524288)
    # Treat hits and misses as run-specific arguments, write them cache_log
    pc1.hits = pc1.misses = 0
    pc2.hits = pc2.misses = 0
    PersistentCache.cache_info = cache_info
    

    for subdir, dirs, files in os.walk(output_dir):
        for filename in files:
            if filename.startswith("result") and filename.endswith(".tsv"):
                file_path = os.path.join(subdir, filename)
                df = pd.read_csv(file_path, sep="\t")
                num_ppkt = df["label"].nunique() 
                #TODO this just picks the number of ppkts of the last dirs...
                # num_ppkt should be a list with one entry per model/language...
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
    header = [comparing, "n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8", "n9", "n10", "n10p", "nf"]
    rank_df = pd.DataFrame(0, index=np.arange(len(results_files)), columns=header)

    cache_file = out_caches / "cache_log.txt"

    with cache_file.open('a', newline = '') as cf:
        now_is = datetime.now().strftime("%Y%m%d-%H%M%S")
        cf.write("Timestamp: " + now_is +"\n\n")
        mondo = mondo_adapter()
        i = 0
        # Each df is a model or a language
        for df in results_data:
            # For each label in the results file, find if the correct term is ranked
            df["rank"] = df.groupby("label")["score"].rank(ascending=False, method="first")
            label_4_non_eng = df["label"].str.replace("_[a-z][a-z]-prompt", "_en-prompt", regex=True)

            # df['correct_term'] is an OMIM
            # df['term'] is Mondo or OMIM ID, or even disease label
            df["correct_term"] = label_4_non_eng.map(label_to_correct_term)
 
            # Make sure caching is used in the following by unwrapping explicitly
            results = []
            for idx, row in df.iterrows():
                # call OAK and get OMIM IDs for df['term'] and see if df['correct_term'] is one of them
                # in the case of phenotypic series, if Mondo corresponds to grouping term, accept it
                k = hashkey(row['term'], row['correct_term'])
                try:
                    val = pc2[k]
                    pc2.hits += 1
                except KeyError:
                    # cache miss
                    val = score_grounded_result(row['term'], row['correct_term'], mondo, pc1)
                    pc2[k] = val
                    pc2.misses += 1
                is_correct = val > 0
                results.append(is_correct)

            df['is_correct'] = results
            df["reciprocal_rank"] = df.apply(
                lambda row: 1 / row["rank"] if row["is_correct"] else 0, axis=1
            )

            # Save full data frame
            full_df_path = output_dir / results_files[i].split("/")[0]
            full_df_filename = "full_df_results.tsv"
            safe_save_tsv(full_df_path, full_df_filename, df)
            
            # Calculate MRR for this file
            mrr = df.groupby("label")["reciprocal_rank"].max().mean()
            mrr_scores.append(mrr)
            
            # Calculate top<n> of each rank
            rank_df.loc[i, comparing] = results_files[i].split("/")[0]
            
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
            cf.write(str(pc2.cache_info()))
            cf.write('\nomim_mappings cache info:\n')
            cf.write(str(pc1.cache_info()))
            cf.write('\n\n')
            i = i + 1

    pc1.close()
    pc2.close()
    

    data_dir = output_dir / "rank_data"
    data_dir.mkdir(exist_ok=True)
    topn_file_name = "topn_result.tsv"
    topn_file = data_dir / topn_file_name
    safe_save_tsv(data_dir, topn_file_name, rank_df)

    print("MRR scores are:\n")
    print(mrr_scores)
    mrr_file = data_dir / "mrr_result.tsv"

    # write out results for plotting 
    with mrr_file.open('w', newline = '') as dat:
        writer = csv.writer(dat, quoting = csv.QUOTE_NONNUMERIC, delimiter = '\t', lineterminator='\n')
        writer.writerow(results_files)
        writer.writerow(mrr_scores)

    df = pd.read_csv(topn_file, delimiter='\t')
    df["top1"] = df['n1']
    df["top3"] = df["n1"] + df["n2"] + df["n3"]
    df["top5"] = df["top3"] + df["n4"] + df["n5"]
    df["top10"] = df["top5"] + df["n6"] + df["n7"] + df["n8"] + df["n9"] + df["n10"]
    df["not_found"] = df["nf"]
    
    df_aggr = pd.DataFrame()
    df_aggr = pd.melt(df, id_vars=comparing, value_vars=["top1", "top3", "top5", "top10", "not_found"], var_name="Rank_in", value_name="counts")
    df_aggr["percentage"] = df_aggr["counts"]/num_ppkt

    # If "topn_aggr.tsv" already exists, prepend "old_"
    # It's the user's responsibility to know only up to 2 versions can exist, then data is lost
    topn_aggr_file_name = "topn_aggr.tsv"
    topn_aggr_file = data_dir / topn_aggr_file_name
    safe_save_tsv(data_dir, topn_aggr_file_name, df_aggr)
        
    return mrr_file, data_dir, num_ppkt, topn_aggr_file
                    