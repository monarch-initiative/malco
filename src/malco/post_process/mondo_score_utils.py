from oaklib.datamodels.vocabulary import IS_A
from oaklib.interfaces import MappingProviderInterface
from typing import List 
from cachetools import cached, LRUCache
from cachetools.keys import hashkey



FULL_SCORE = 1.0
PARTIAL_SCORE = 0.5

@cached(cache=LRUCache(maxsize=16384), info=True, key=lambda term, adapter: hashkey(term))
def omim_mappings(term: str, adapter) -> List[str]: 
    """
    Get the OMIM mappings for a term.

    Example:

    >>> omim_mappings("MONDO:0007566", adapter)
    ['OMIM:132800']

    Args:
        term (str): The term.

    Returns:
        str: The OMIM mappings.
    """   
    omims = []
    for m in adapter.sssom_mappings([term], source="OMIM"):
        if m.predicate_id == "skos:exactMatch":
            omims.append(m.object_id)
    return omims


@cached(cache=LRUCache(maxsize=4096), info=True, key=lambda prediction, ground_truth, mondo: hashkey(prediction, ground_truth))
def score_grounded_result(prediction: str, ground_truth: str, mondo) -> float:
    """
    Score the grounded result.

    Exact match:
    >>> score_grounded_result("OMIM:132800", "OMIM:132800", mondo)
    1.0

    The predicted Mondo is equivalent to the ground truth OMIM
    (via skos:exactMatches in Mondo):
    >>> score_grounded_result("MONDO:0007566", "OMIM:132800", mondo)
    1.0

    The predicted Mondo is a disease entity that groups multiple
    OMIMs, one of which is the ground truth:
    >>> score_grounded_result("MONDO:0008029", "OMIM:158810", mondo)
    0.5

    Args:
        prediction (str): The prediction.
        ground_truth (str): The ground truth.
        mondo: the mondo adapter.

    Returns:
        float: The score.
    """
    if not isinstance(mondo, MappingProviderInterface):
        raise ValueError("Adapter is not an MappingProviderInterface")
    
    if prediction == ground_truth:
        # predication is the correct OMIM
        return FULL_SCORE

    #if ground_truth in omim_mappings(prediction, mondo):
    if ground_truth in omim_mappings(prediction, mondo):
        # prediction is a MONDO that directly maps to a correct OMIM
        return FULL_SCORE

    descendants_list = mondo.descendants([prediction], predicates=[IS_A], reflexive=True)
    for mondo_descendant in descendants_list:
        if ground_truth in omim_mappings(mondo_descendant, mondo):
            # prediction is a MONDO that maps to a correct OMIM via a descendant
            return PARTIAL_SCORE
    return 0.0


