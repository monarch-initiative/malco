import json
import os
from pathlib import Path
from typing import List

import pandas as pd
import yaml
from pheval.post_processing.post_processing import PhEvalGeneResult, generate_pheval_result
from pheval.utils.file_utils import all_files
from pheval.utils.phenopacket_utils import GeneIdentifierUpdater, create_hgnc_dict


def read_raw_result_yaml(raw_result_path: Path) -> List[dict]:
    """
    Read the raw result file.

    Args:
        raw_result_path(Path): Path to the raw result file.

    Returns:
        dict: Contents of the raw result file.
    """
    with open(raw_result_path, 'r') as raw_result:
        return list(yaml.safe_load_all(raw_result))  # Load and convert to list


def create_standardised_results(raw_results_dir: Path, output_dir: Path,
                                output_file_name: str = "results.tsv") -> pd.DataFrame:
    data = []
    for raw_result_path in raw_results_dir.iterdir():
        if raw_result_path.is_file():
            all_results = read_raw_result_yaml(raw_result_path)

            for this_result in all_results:
                extracted_object = this_result.get("extracted_object")
                if extracted_object:
                    label = extracted_object.get('label')
                    terms = extracted_object.get('terms')
                    if terms:
                        num_terms = len(terms)
                        score = [1 / (i + 1) for i in range(num_terms)]  # score is reciprocal rank
                        for term, scr in zip(terms, score):
                            data.append({'label': label, 'term': term, 'score': scr})

    # Create DataFrame
    df = pd.DataFrame(data)

    # Save DataFrame to TSV
    output_path = os.path.join(output_dir, output_file_name)
    df.to_csv(output_path, sep='\t', index=False)

    return df
