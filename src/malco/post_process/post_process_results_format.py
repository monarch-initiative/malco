import json
import os
import tqdm
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
                                output_file_name: str) -> pd.DataFrame:
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
                        rank_list = [ i+1 for i in range(num_terms)]
                        for term, scr, rank in zip(terms, score, rank_list):
                            data.append({'label': label, 'term': term, 'score': scr, 'rank': rank})

    # Create DataFrame
    df = pd.DataFrame(data)

    # Save DataFrame to TSV
    output_path = output_dir / output_file_name
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


#!/usr/bin/python
import json
from pathlib import Path

import click
from pheval.post_processing.post_processing import (
    PhEvalDiseaseResult,
    PhEvalGeneResult,
    PhEvalVariantResult,
    generate_pheval_result,
)
from pheval.utils.file_utils import files_with_suffix


def read_exomiser_json_result(exomiser_result_path: Path) -> dict:
    """Load Exomiser json result."""
    with open(exomiser_result_path) as exomiser_json_result:
        exomiser_result = json.load(exomiser_json_result)
    exomiser_json_result.close()
    return exomiser_result


def trim_exomiser_result_filename(exomiser_result_path: Path) -> Path:
    """Trim suffix appended to Exomiser JSON result path."""
    return Path(str(exomiser_result_path.name).replace("-exomiser", ""))


class PhEvalGeneResultFromExomiserJsonCreator:
    def __init__(self, exomiser_json_result: [dict], score_name: str):
        self.exomiser_json_result = exomiser_json_result
        self.score_name = score_name

    @staticmethod
    def _find_gene_symbol(result_entry: dict) -> str:
        """Return gene symbol from Exomiser result entry."""
        return result_entry["geneSymbol"]

    @staticmethod
    def _find_gene_identifier(result_entry: dict) -> str:
        """Return ensembl gene identifier from Exomiser result entry."""
        return result_entry["geneIdentifier"]["geneId"]

    def _find_relevant_score(self, result_entry: dict):
        """Return score from Exomiser result entry."""
        return round(result_entry[self.score_name], 4)

    def extract_pheval_gene_requirements(self) -> [PhEvalGeneResult]:
        """Extract data required to produce PhEval gene output."""
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            if self.score_name in result_entry:
                simplified_exomiser_result.append(
                    PhEvalGeneResult(
                        gene_symbol=self._find_gene_symbol(result_entry),
                        gene_identifier=self._find_gene_identifier(result_entry),
                        score=self._find_relevant_score(result_entry),
                    )
                )

        return simplified_exomiser_result


class PhEvalVariantResultFromExomiserJsonCreator:

    def __init__(self, exomiser_json_result: [dict], score_name: str):
        self.exomiser_json_result = exomiser_json_result
        self.score_name = score_name

    @staticmethod
    def _find_chromosome(result_entry: dict) -> str:
        """Return chromosome from Exomiser result entry."""
        return result_entry["contigName"]

    @staticmethod
    def _find_start_pos(result_entry: dict) -> int:
        """Return start position from Exomiser result entry."""
        return result_entry["start"]

    @staticmethod
    def _find_end_pos(result_entry: dict) -> int:
        """Return end position from Exomiser result entry."""
        return result_entry["end"]

    @staticmethod
    def _find_ref(result_entry: dict) -> str:
        """Return reference allele from Exomiser result entry."""
        return result_entry["ref"]

    @staticmethod
    def _find_alt(result_entry: dict) -> str:
        """Return alternate allele from Exomiser result entry."""
        if "alt" in result_entry and result_entry["alt"] is not None:
            return result_entry["alt"].strip(">").strip("<")
        else:
            return ""

    def _find_relevant_score(self, result_entry) -> float:
        """Return score from Exomiser result entry."""
        return round(result_entry[self.score_name], 4)

    def _filter_for_acmg_assignments(
        self, variant: PhEvalVariantResult, score: float, variant_acmg_assignments: dict
    ) -> bool:
        """Filter variants if they meet the PATHOGENIC or LIKELY_PATHOGENIC ACMG classification."""
        for assignment in variant_acmg_assignments:
            if variant == PhEvalVariantResult(
                chromosome=self._find_chromosome(assignment["variantEvaluation"]),
                start=self._find_start_pos(assignment["variantEvaluation"]),
                end=self._find_end_pos(assignment["variantEvaluation"]),
                ref=self._find_ref(assignment["variantEvaluation"]),
                alt=self._find_alt(assignment["variantEvaluation"]),
                score=score,
            ) and (
                assignment["acmgClassification"] == "PATHOGENIC"
                or assignment["acmgClassification"] == "LIKELY_PATHOGENIC"
            ):
                return True

    def extract_pheval_variant_requirements(
        self, use_acmg_filter: bool = False
    ) -> [PhEvalVariantResult]:
        """Extract data required to produce PhEval variant output."""
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            for gene_hit in result_entry["geneScores"]:
                if self.score_name in result_entry:
                    if "contributingVariants" in gene_hit:
                        score = self._find_relevant_score(result_entry)
                        contributing_variants = gene_hit["contributingVariants"]
                        variant_acmg_assignments = gene_hit["acmgAssignments"]
                        for cv in contributing_variants:
                            variant = PhEvalVariantResult(
                                chromosome=self._find_chromosome(cv),
                                start=self._find_start_pos(cv),
                                end=self._find_end_pos(cv),
                                ref=self._find_ref(cv),
                                alt=self._find_alt(cv),
                                score=score,
                            )
                            if use_acmg_filter and self._filter_for_acmg_assignments(
                                variant, score, variant_acmg_assignments
                            ):
                                simplified_exomiser_result.append(variant)
                            if not use_acmg_filter:
                                simplified_exomiser_result.append(variant)
        return simplified_exomiser_result


class PhEvalDiseaseResultFromExomiserJsonCreator:
    def __init__(self, exomiser_json_result: [dict]):
        self.exomiser_json_result = exomiser_json_result

    @staticmethod
    def _find_disease_name(result_entry: dict) -> str:
        """Return disease term from Exomiser result entry."""
        return result_entry["diseaseTerm"]

    @staticmethod
    def _find_disease_identifier(result_entry: dict) -> int:
        """Return disease ID from Exomiser result entry."""
        return result_entry["diseaseId"]

    @staticmethod
    def _find_relevant_score(result_entry) -> float:
        """Return score from Exomiser result entry."""
        return round(result_entry["score"], 4)

    def extract_pheval_disease_requirements(self) -> [PhEvalDiseaseResult]:
        """Extract data required to produce PhEval disease output."""
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            try:
                for disease in result_entry["priorityResults"]["HIPHIVE_PRIORITY"][
                    "diseaseMatches"
                ]:
                    simplified_exomiser_result.append(
                        PhEvalDiseaseResult(
                            disease_name=self._find_disease_name(disease["model"]),
                            disease_identifier=self._find_disease_identifier(disease["model"]),
                            score=self._find_relevant_score(disease),
                        )
                    )
            except KeyError:
                pass
        return simplified_exomiser_result


def create_exomiser_standardised_results(
    results_dir: Path,
    output_dir: Path,
    score_name: str,
    sort_order: str,
    variant_analysis: bool,
    gene_analysis: bool,
    disease_analysis: bool,
    include_acmg: bool = False,
) -> None:
    """Write standardised gene/variant/disease results from default Exomiser json output."""
    for exomiser_json_result in tqdm.tqdm(files_with_suffix(results_dir, ".json"), desc="Processing Exomiser Results"):
        exomiser_result = read_exomiser_json_result(exomiser_json_result)
        if gene_analysis:
            pheval_gene_requirements = PhEvalGeneResultFromExomiserJsonCreator(
                exomiser_result, score_name
            ).extract_pheval_gene_requirements()
            generate_pheval_result(
                pheval_result=pheval_gene_requirements,
                sort_order_str=sort_order,
                output_dir=output_dir,
                tool_result_path=trim_exomiser_result_filename(exomiser_json_result),
            )
        if variant_analysis:
            pheval_variant_requirements = PhEvalVariantResultFromExomiserJsonCreator(
                exomiser_result, score_name
            ).extract_pheval_variant_requirements(include_acmg)
            generate_pheval_result(
                pheval_result=pheval_variant_requirements,
                sort_order_str=sort_order,
                output_dir=output_dir,
                tool_result_path=trim_exomiser_result_filename(exomiser_json_result),
            )
        if disease_analysis:
            pheval_disease_requirements = PhEvalDiseaseResultFromExomiserJsonCreator(
                exomiser_result
            ).extract_pheval_disease_requirements()
            generate_pheval_result(
                pheval_result=pheval_disease_requirements,
                sort_order_str=sort_order,
                output_dir=output_dir,
                tool_result_path=trim_exomiser_result_filename(exomiser_json_result),
            )


@click.command()
@click.option(
    "--output-dir",
    "-o",
    required=True,
    metavar="PATH",
    help="Output directory for standardised results.",
    type=Path,
)
@click.option(
    "--results-dir",
    "-R",
    required=True,
    metavar="DIRECTORY",
    help="Full path to Exomiser results directory to be standardised.",
    type=Path,
)
@click.option(
    "--score-name",
    "-s",
    required=True,
    help="Score name to extract from results.",
    type=click.Choice(["combinedScore", "priorityScore", "variantScore", "pValue"]),
    default="combinedScore",
    show_default=True,
)
@click.option(
    "--sort-order",
    "-so",
    required=True,
    help="Ordering of results for ranking.",
    type=click.Choice(["ascending", "descending"]),
    default="descending",
    show_default=True,
)
@click.option(
    "--gene-analysis/--no-gene-analysis",
    type=bool,
    default=False,
    help="Specify whether to create PhEval gene results.",
)
@click.option(
    "--variant-analysis/--no-variant-analysis",
    type=bool,
    default=False,
    help="Specify whether to create PhEval variant results.",
)
@click.option(
    "--disease-analysis/--no-disease-analysis",
    type=bool,
    default=False,
    help="Specify whether to create PhEval disease results.",
)
@click.option(
    "--include-acmg",
    is_flag=True,
    type=bool,
    default=False,
    help="Specify whether to include ACMG filter for PATHOGENIC or LIKELY_PATHOGENIC classifications.",
)
def post_process_exomiser_results(
    output_dir: Path,
    results_dir: Path,
    score_name: str,
    sort_order: str,
    gene_analysis: bool,
    variant_analysis: bool,
    disease_analysis: bool,
    include_acmg: bool,
):
    """Post-process Exomiser json results into PhEval gene and variant outputs."""
    (
        output_dir.joinpath("pheval_gene_results").mkdir(parents=True, exist_ok=True)
        if gene_analysis
        else None
    )
    (
        output_dir.joinpath("pheval_variant_results").mkdir(parents=True, exist_ok=True)
        if variant_analysis
        else None
    )
    (
        output_dir.joinpath("pheval_disease_results").mkdir(parents=True, exist_ok=True)
        if disease_analysis
        else None
    )
    create_standardised_results(
        results_dir,
        output_dir,
        score_name,
        sort_order,
        variant_analysis,
        gene_analysis,
        disease_analysis,
        include_acmg,
    )
