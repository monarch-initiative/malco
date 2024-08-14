import os 
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import pickle as pkl

from oaklib.interfaces import OboGraphInterface
from oaklib.datamodels.vocabulary import IS_A
from oaklib.interfaces import MappingProviderInterface
from oaklib import get_adapter

from cachetools import cached, LRUCache
from typing import List 
from cachetools.keys import hashkey
from shelved_cache import PersistentCache

FULL_SCORE = 1.0
PARTIAL_SCORE = 0.5

#pc1 = {}
#pc2 = {}

#efilename1 = str(output_dir / "omim_mappings_cache")
#filenam2 = str(output_dir / "score_grounded_result_cache")
#filename1 = str("omim_mappings_cache")
# filename2 = str("score_grounded_result_cache")
#    global pc1
#    global pc2
    #pc1 = PersistentCache(LRUCache(maxsize=16384), filename1)
    #pc2 = PersistentCache(LRUCache(maxsize=4096), filename2)
#pc1 = PersistentCache(LRUCache, filename1, maxsize=16384)
# pc2 = PersistentCache(LRUCache, filename2, maxsize=4096)

#@cached(pc1, info=True, key=lambda term, adapter: hashkey(term))
def omim_mappings(term: str, adapter) -> List[str]: 
    """
    Get the OMIM mappings for a term.

    Example:

    >>> from oaklib import get_adapter
    >>> omim_mappings("MONDO:0007566", get_adapter("sqlite:obo:mondo"))
    ['OMIM:132800']

    Args:
        term (str): The term.
        adapter: The mondo adapter.

    Returns:
        str: The OMIM mappings.
    """   
    omims = []
    for m in adapter.sssom_mappings([term], source="OMIM"):
        if m.predicate_id == "skos:exactMatch":
            omims.append(m.object_id)
    return omims


# @cached(pc2, info=True, key=lambda prediction, ground_truth, mondo: hashkey(prediction, ground_truth))
def score_grounded_result(prediction: str, ground_truth: str, mondo, cache=None) -> float:
    """
    Score the grounded result.

    Exact match:
    >>> from oaklib import get_adapter
    >>> score_grounded_result("OMIM:132800", "OMIM:132800", get_adapter("sqlite:obo:mondo"))
    1.0

    The predicted Mondo is equivalent to the ground truth OMIM
    (via skos:exactMatches in Mondo):
    
    >>> score_grounded_result("MONDO:0007566", "OMIM:132800", get_adapter("sqlite:obo:mondo"))
    1.0

    The predicted Mondo is a disease entity that groups multiple
    OMIMs, one of which is the ground truth:
    
    >>> score_grounded_result("MONDO:0008029", "OMIM:158810", get_adapter("sqlite:obo:mondo"))
    0.5

    Args:
        prediction (str): The prediction.
        ground_truth (str): The ground truth.
        mondo: The mondo adapter.

    Returns:
        float: The score.
    """
    if not isinstance(mondo, MappingProviderInterface):
        raise ValueError("Adapter is not an MappingProviderInterface")
    
    if prediction == ground_truth:
        # predication is the correct OMIM
        return FULL_SCORE

    
    ground_truths = get_ground_truth_from_cache_or_compute(prediction, mondo, cache)
    if ground_truth in ground_truths:
        # prediction is a MONDO that directly maps to a correct OMIM
        return FULL_SCORE

    descendants_list = mondo.descendants([prediction], predicates=[IS_A], reflexive=True)
    for mondo_descendant in descendants_list:
        ground_truths = get_ground_truth_from_cache_or_compute(mondo_descendant, mondo, cache)
        if ground_truth in ground_truths:
            # prediction is a MONDO that maps to a correct OMIM via a descendant
            return PARTIAL_SCORE
    return 0.0

def get_ground_truth_from_cache_or_compute(
    term, 
    adapter, 
    cache,
):
    if cache is None:
        return omim_mappings(term, adapter)
        
    k = hashkey(term)
    try:
        ground_truths = cache[k]
    except KeyError:
        # cache miss
        ground_truths = omim_mappings(term, adapter)
        cache[k] = ground_truths
    return ground_truths


def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo") 

def compute_mrr_and_ranks(
    comparing, 
    output_dir, 
    prompt_dir, 
    correct_answer_file,
    raw_results_dir,
) -> Path:
    # Read in results TSVs from self.output_dir that match glob results*tsv 
    results_data = []
    results_files = []
    num_ppkt = 0
    pc2_cache_file = str(output_dir / "score_grounded_result_cache")
    pc2 = PersistentCache(LRUCache, pc2_cache_file, maxsize=4096)        
    pc1_cache_file = str(output_dir / "omim_mappings_cache")
    pc1 = PersistentCache(LRUCache, pc1_cache_file, maxsize=16384)


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
    header = [comparing, "n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8", "n9", "n10", "n10p", "nf"]
    rank_df = pd.DataFrame(0, index=np.arange(len(results_files)), columns=header)

    cache_file = output_dir / "cache_log.txt"

    with cache_file.open('a', newline = '') as cf:
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
                #breakpoint()

                # lambda prediction, ground_truth, mondo: hashkey(prediction, ground_truth)
                k = hashkey(row['term'], row['correct_term'])
                try:
                    val = pc2[k]
                except KeyError:
                    # cache miss
                    val = score_grounded_result(row['term'], row['correct_term'], mondo, pc1)
                    pc2[k] = val
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
            breakpoint()
            cf.write(results_files[i])
            cf.write('\nscore_grounded_result cache info:\n')
            #cf.write(str(score_grounded_result.cache_info()))
            cf.write('\nomim_mappings cache info:\n')
            #cf.write(str(omim_mappings.cache_info()))
            cf.write('\n\n')
            i = i + 1

    pc1.close()
    pc2.close()
    
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
