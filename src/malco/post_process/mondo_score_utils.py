from functools import lru_cache
from typing import List

from oaklib import get_adapter
from oaklib.datamodels.vocabulary import IS_A
from oaklib.interfaces import OboGraphInterface, MappingProviderInterface

FULL_SCORE = 1.0
PARTIAL_SCORE = 0.5


@lru_cache(maxsize=4096)
def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo")


@lru_cache(maxsize=1024)
def omim_mappings(term: str) -> List[str]:
    """
    Get the OMIM mappings for a term.

    Example:

    >>> omim_mappings("MONDO:0007566")
    ['OMIM:132800']

    Args:
        term (str): The term.

    Returns:
        str: The OMIM mappings.
    """
    adapter = mondo_adapter()
    if not isinstance(adapter, MappingProviderInterface):
        raise ValueError("Adapter is not an MappingProviderInterface")
    omims = []
    for m in adapter.sssom_mappings([term], "OMIM"):
        if m.predicate_id == "skos:exactMatch":
            omims.append(m.object_id)
    return omims


def score_grounded_result(prediction: str, ground_truth: str) -> float:
    """
    Score the grounded result.

    Exact match:

    >>> score_grounded_result("OMIM:132800", "OMIM:132800")
    1.0

    The predicted Mondo is equivalent to the ground truth OMIM
    (via skos:exactMatches in Mondo):

    >>> score_grounded_result("MONDO:0007566", "OMIM:132800")
    1.0

    The predicted Mondo is a disease entity that groups multiple
    OMIMs, one of which is the ground truth:

    >>> score_grounded_result("MONDO:0008029", "OMIM:158810")
    0.5

    Args:
        prediction (str): The prediction.
        ground_truth (str): The ground truth.

    Returns:
        float: The score.
    """
    if prediction == ground_truth:
        # predication is the correct OMIM
        return FULL_SCORE
    if ground_truth in omim_mappings(prediction):
        # prediction is a MONDO that directly maps to a correct OMIM
        return FULL_SCORE
    mondo = mondo_adapter()

    descendants_list = mondo.descendants([prediction], predicates=[IS_A], reflexive=True)
    for mondo_descendant in descendants_list:
        if ground_truth in omim_mappings(mondo_descendant):
            # prediction is a MONDO that maps to a correct OMIM via a descendant
            return PARTIAL_SCORE
    return 0.0


