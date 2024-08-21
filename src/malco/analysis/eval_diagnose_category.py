import pandas as pd
import numpy as np
import sys
from cachetools import cached, LRUCache
from cachetools.keys import hashkey
from shelved_cache import PersistentCache

from oaklib.datamodels.vocabulary import IS_A, PART_OF
from oaklib.interfaces import MappingProviderInterface
from oaklib.interfaces import OboGraphInterface
from oaklib.interfaces.obograph_interface import GraphTraversalMethod

from oaklib import get_adapter
pc_cache_file = "trial_diagnose_cache"
pc = PersistentCache(LRUCache, pc_cache_file, maxsize=4096)        
    

def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo") 

def mondo_mapping(term, adapter): 
    #print(term)
    mondos = []
    for m in adapter.sssom_mappings([term], source="OMIM"):
        if m.predicate_id == "skos:exactMatch":
            mondos.append(m.subject_id)
    return mondos

#@cached(cache=LRUCache(maxsize=4096), key=lambda omim_term, disease_categories, mondo: hashkey(omim_term), info=True)
@cached(pc, key=lambda omim_term, disease_categories, mondo: hashkey(omim_term))
def find_category(omim_term, disease_categories, mondo):
    if not isinstance(mondo, MappingProviderInterface):
        raise ValueError("Adapter is not an MappingProviderInterface")
    # What is best algorithm to avoid traversing the mondo graph a billion times?    
    # Find ancestors
    mondo_term = mondo_mapping(omim_term, mondo)
    if not mondo_term:
        print(omim_term)
        return None
        #breakpoint()
    ancestor_list = mondo.ancestors(mondo_term, predicates=[IS_A, PART_OF]) #, reflexive=True) # method=GraphTraversalMethod.ENTAILMENT
    
    for mondo_ancestor in ancestor_list:
        if mondo_ancestor in disease_categories:
            return mondo_ancestor # This should be smt like MONDO:0045024 (cancer or benign tumor)
    
    print("Special issue following:  ")
    print(omim_term)

#=====================================================
# script starts here
# Find 42 diseases categories
mondo = mondo_adapter()
disease_categories = mondo.relationships(objects = ["MONDO:0700096"], predicates=[IS_A])
# make df contingency table with header=diseases_category, correct, incorrect and initialize all to 0.
header = ["label","correct", "incorrect"]
#header = ["diseases_category", "correct", "incorrect"]
dc_list = [i[0] for i in list(disease_categories)]
#contingency_table = pd.DataFrame(0, index=np.arange(len(dc_list)), columns=header)
contingency_table = pd.DataFrame(0, index=dc_list, columns=header)
#dc_labels = []
for j in dc_list:
    contingency_table.loc[j,"label"] = mondo.label(j)

model=str(sys.argv[1])
# example path of full results
#filename = f"out_openAI_models/multimodel/gpt-4o/full_df_results.tsv"
filename = f"out_openAI_models/multimodel/{model}/full_df_results.tsv"
# label   term    score   rank    correct_term    is_correct      reciprocal_rank
# PMID_35962790_Family_B_Individual_3__II_6__en-prompt.txt        MONDO:0008675   1.0     1.0     OMIM:620545     False        0.0

df = pd.read_csv(
        filename, sep="\t" #, header=None, names=["description", "term", "label"]
    )

ppkts = df.groupby("label")[["term", "correct_term", "is_correct"]] 
count_fails=0



for ppkt in ppkts:
    # find this phenopackets category <cat> from OMIM
    # cache find_category
    category_index = find_category(ppkt[1].iloc[0]["correct_term"], dc_list, mondo)
    if not category_index:
        count_fails += 1
        continue
    #cat_ind = find_cat_index(category)
    # is there a true? ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe 
    if not any(ppkt[1]["is_correct"]):
        # no  --> increase <cat> incorrect
        contingency_table.loc[category_index, "incorrect"] += 1
    else:
        # yes --> increase <cat> correct
        contingency_table.loc[category_index, "correct"] += 1

print(count_fails) # print to file!
print(contingency_table)

cont_table_file = f"disease_groups/{model}.tsv"
# Will overwrite
contingency_table.to_csv(cont_table_file, sep='\t')