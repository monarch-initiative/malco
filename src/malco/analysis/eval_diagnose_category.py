import pandas as pd
import numpy as np

from oaklib.datamodels.vocabulary import IS_A, PART_OF
from oaklib.interfaces import MappingProviderInterface
from oaklib.interfaces import OboGraphInterface
from oaklib.interfaces.obograph_interface import GraphTraversalMethod

from oaklib import get_adapter


def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo") 

def find_category(term, disease_categories, mondo):
    if not isinstance(mondo, MappingProviderInterface):
        raise ValueError("Adapter is not an MappingProviderInterface")
    # What is best algorithm to avoid traversing the mondo graph a billion times?    
    # Find ancestors
    ancenstor_list = mondo.ancestors(term, predicates=[IS_A, PART_OF]) #, reflexive=True) # method=GraphTraversalMethod.ENTAILMENT
    breakpoint()
    for mondo_ancestor in ancenstor_list:
        if mondo_ancestor in disease_categories:
            return mondo_ancestor # This should be smt like MONDO:0045024 (cancer or benign tumor)

def find_cat_index(category):
    #TODO!!
    return category+3

# Find 42 diseases categories
mondo = mondo_adapter()
#TODO check that the follosing is only dsecendantes down one "link" NO!
disease_categories = mondo.relationships(objects = ["MONDO:0700096"], predicates=[IS_A])
# make df contingency table with header=diseases_category, correct, incorrect and initialize all to 0.
header = ["diseases_category", "correct", "incorrect"]
dc_list = [i[0] for i in list(disease_categories)]
contingency_table = pd.DataFrame(0, index=np.arange(len(dc_list)), columns=header)
 
# example path of full results
filename = "testout_multmodel_b4run/raw_results/multimodel/gpt-4/full_df_results.tsv"

# label   term    score   rank    correct_term    is_correct      reciprocal_rank
# PMID_35962790_Family_B_Individual_3__II_6__en-prompt.txt        MONDO:0008675   1.0     1.0     OMIM:620545     False        0.0

df = pd.read_csv(
        filename, sep="\t" #, header=None, names=["description", "term", "label"]
    )

ppkts = df.groupby("label")[["term", "correct_term", "is_correct"]] 

for ppkt in ppkts:
    # find this phenopackets category <cat>, as an index from 1 to 42 (or 0 to 41)
    print(ppkt[1]["term"])
    breakpoint()
    category = find_category(ppkt[1]["term"], dc_list, mondo)
    cat_ind = find_cat_index(category)
    # is there a true? ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe 
    if not any(ppkt[1]["is_correct"]):
        # no  --> increase <cat> incorrect
        contingency_table.loc[cat_ind, "incorrect"] += 1
    else:
        # yes --> increase <cat> correct
        contingency_table.loc[cat_ind, "correct"] += 1


    