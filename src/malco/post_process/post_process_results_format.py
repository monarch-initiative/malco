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


# these are from the template and not currently used outside of tests

def read_raw_result(raw_result_path: Path) -> List[dict]:
    """
    Read the raw result file.

    Args:
        raw_result_path(Path): Path to the raw result file.

    Returns:
        List[dict]: Contents of the raw result file.
    """
    with open(raw_result_path) as raw_result:
        raw_result_data = json.load(raw_result)
    raw_result.close()
    return raw_result_data


class ConvertToPhEvalResult:
    """Class to convert the raw result file to PhEvalGeneResult."""

    def __init__(self, raw_result: List[dict], gene_identifier_updator: GeneIdentifierUpdater):
        """
        Initialise the ConvertToPhEvalResult class.

        Args:
            raw_result (List[dict]): Contents of the raw result file.
            gene_identifier_updator (GeneIdentifierUpdater): GeneIdentifierUpdater object.

        """
        self.raw_result = raw_result
        self.gene_identifier_updator = gene_identifier_updator

    @staticmethod
    def _obtain_score(result_entry: dict) -> float:
        """
        Obtain the score from the result entry.

        Args:
            result_entry (dict): Contents of the result entry.

        Returns:
            float: The score.
        """
        return result_entry["score"]

    @staticmethod
    def _obtain_gene_symbol(result_entry: dict) -> str:
        """
        Obtain the gene symbol from the result entry.

        Args:
            result_entry (dict): Contents of the result entry.

        Returns:
            str: The gene symbol.
        """
        return result_entry["gene_symbol"]

    def obtain_gene_identifier(self, result_entry: dict) -> str:
        """
        Obtain the gene identifier from the result entry.

        Args:
            result_entry (dict): Contents of the result entry.

        Returns:
            str: The gene identifier.
        """
        return self.gene_identifier_updator.find_identifier(self._obtain_gene_symbol(result_entry))

    def extract_pheval_gene_requirements(self) -> List[PhEvalGeneResult]:
        """
        Extract the data required to produce PhEval gene output.

        Returns:
            List[PhEvalGeneResult]: List of PhEvalGeneResult objects.
        """
        pheval_result = []
        for result_entry in self.raw_result:
            pheval_result.append(
                PhEvalGeneResult(
                    gene_symbol=self._obtain_gene_symbol(result_entry),
                    gene_identifier=self.obtain_gene_identifier(result_entry),
                    score=self._obtain_score(result_entry),
                )
            )
        return pheval_result


def create_standardised_results(raw_results_dir: Path, output_dir: Path) -> None:
    """
    Create PhEval gene tsv output from raw results.

    Args:
        raw_results_dir (Path): Path to the raw results directory.
        output_dir (Path): Path to the output directory.
    """
    gene_identifier_updator = GeneIdentifierUpdater(
        gene_identifier="ensembl_id", hgnc_data=create_hgnc_dict()
    )
    for raw_result_path in all_files(raw_results_dir):
        raw_result = read_raw_result(raw_result_path)
        pheval_result = ConvertToPhEvalResult(
            raw_result, gene_identifier_updator
        ).extract_pheval_gene_requirements()
        generate_pheval_result(
            pheval_result=pheval_result,
            sort_order_str="DESCENDING",
            output_dir=output_dir,
            tool_result_path=raw_result_path,
        )
