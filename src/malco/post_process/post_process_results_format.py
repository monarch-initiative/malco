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
        raw_result_data = yaml.safe_load(raw_result)
    return raw_result_data


def create_standardised_results(raw_results_dir: Path, output_dir: Path,
                                output_file_name: str = "results.tsv") -> None:
    """
    (via enock.Niyonkuru@jax.org)
    Load a YAML file, create a DataFrame with columns 'label', 'term', and 'score', and
    save it to a TSV file.

    Parameters:
    yaml_file_path (str): The path to the YAML file.
    output_file_path (str): The path where the TSV file will be saved.

    Returns:
    pd.DataFrame: The DataFrame created from the YAML data.
    """
    for raw_result_path in all_files(raw_results_dir):

        raw_result = read_raw_result_yaml(raw_result_path)

        extracted_object = raw_result.get("extracted_object")
        data = []
        if extracted_object:
            label = extracted_object.get('label')
            terms = extracted_object.get('terms')
            if terms:
                num_terms = len(terms)
                score = [1 / (i + 1) for i in range(num_terms)]
                for term, scr in zip(terms, score):
                    data.append({'label': label, 'term': term, 'score': scr})

        # Create DataFrame
        df = pd.DataFrame(data)

        # Save DataFrame to TSV
        df.to_csv(os.path.join(output_dir, output_file_name), sep='\t', index=False)

        return df

