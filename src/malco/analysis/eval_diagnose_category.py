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

def mondo_mapping(term, adapter): 
    print(term)
    mondos = []
    for m in adapter.sssom_mappings([term], source="OMIM"):
        if m.predicate_id == "skos:exactMatch":
            mondos.append(m.subject_id)
    return mondos

def find_category(omim_term, disease_categories, mondo):
    if not isinstance(mondo, MappingProviderInterface):
        raise ValueError("Adapter is not an MappingProviderInterface")
    # What is best algorithm to avoid traversing the mondo graph a billion times?    
    # Find ancestors
    mondo_term = mondo_mapping(omim_term, mondo)
    ancestor_list = mondo.ancestors(mondo_term, predicates=[IS_A, PART_OF]) #, reflexive=True) # method=GraphTraversalMethod.ENTAILMENT
    
    for mondo_ancestor in ancestor_list:
        if mondo_ancestor in disease_categories:
            return mondo_ancestor # This should be smt like MONDO:0045024 (cancer or benign tumor)


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


# example path of full results
filename = "testout_multmodel_b4run/raw_results/multimodel/gpt-4/full_df_results.tsv"

# label   term    score   rank    correct_term    is_correct      reciprocal_rank
# PMID_35962790_Family_B_Individual_3__II_6__en-prompt.txt        MONDO:0008675   1.0     1.0     OMIM:620545     False        0.0

df = pd.read_csv(
        filename, sep="\t" #, header=None, names=["description", "term", "label"]
    )

ppkts = df.groupby("label")[["term", "correct_term", "is_correct"]] 

for ppkt in ppkts:
    # find this phenopackets category <cat> from OMIM
    category_index = find_category(ppkt[1].iloc[0]["correct_term"], dc_list, mondo)
    #cat_ind = find_cat_index(category)
    # is there a true? ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe 
    if not any(ppkt[1]["is_correct"]):
        # no  --> increase <cat> incorrect
        contingency_table.loc[category_index, "incorrect"] += 1
    else:
        # yes --> increase <cat> correct
        contingency_table.loc[category_index, "correct"] += 1

print(contingency_table)
    