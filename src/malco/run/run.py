from pathlib import Path
from malco.run.run_tool import run_tool
import os
# from ontogpt.cli import run_multilingual_analysis


def run(testdata_dir: Path,
        raw_results_dir: Path,
        output_dir: Path,
        langs: tuple) -> None:
    """
    Run the tool to obtain the raw results.

    Args:
        testdata_dir: Path to the test data directory.
        raw_results_dir: Path to the raw results directory.
        output_dir: Path to the output directory.
        langs: Tuple of languages.
    """
    mydir = os.getcwd()

    for lang in langs:
        os.system(
            f"ontogpt -v run-multilingual-analysis --output={output_dir}/raw_results/{lang}/results.yaml {mydir}/prompts/{lang}/ {output_dir}/raw_results/{lang}/differentials_by_file/"
        )
