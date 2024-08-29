from pathlib import Path

from malco.post_process.post_process_results_format import create_standardised_results
import os


def post_process(raw_results_dir: Path, output_dir: Path, langs: tuple) -> None:
    """
    Post-process the raw results output to standardised PhEval TSV format.

    Args:
        raw_results_dir (Path): Path to the raw results directory.
        output_dir (Path): Path to the output directory.
    """

    for lang in langs:
        raw_results_lang = raw_results_dir / lang
        output_lang = output_dir / lang
        raw_results_lang.mkdir(exist_ok=True)
        output_lang.mkdir(exist_ok=True)

        create_standardised_results(raw_results_dir=raw_results_lang,
                                    output_dir=output_lang, output_file_name="results.tsv")


def post_process_exomiser_result_format(
    config, # : ExomiserConfigurations,
    raw_results_dir: Path,
    output_dir: Path,
    variant_analysis: bool,
    gene_analysis: bool,
    disease_analysis: bool,
):
    """Standardise Exomiser json format to separated gene and variant results."""
    print("...standardising results format...")
    create_standardised_results(
        results_dir=raw_results_dir,
        output_dir=output_dir,
        score_name=config.post_process.score_name,
        sort_order=config.post_process.sort_order,
        variant_analysis=variant_analysis,
        gene_analysis=gene_analysis,
        disease_analysis=disease_analysis,
    )
    print("done")
