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
