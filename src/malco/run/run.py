from pathlib import Path

from malco.run.run_tool import run_tool
import os

# from ontogpt.cli import run_multilingual_analysis


def run(testdata_dir: Path, raw_results_dir: Path) -> None:
    """
    Run the tool to obtain the raw results.

    Args:
        testdata_dir: Path to the test data directory.
        raw_results_dir: Path to the raw results directory.
    """
    mydir = os.getcwd()
    langs = ["en", "es"]
    # For testing
    # langs = ["et", "ep"]
    for lang in langs:
        os.system(
            f"ontogpt -v run-multilingual-analysis --output={mydir}/outputdir/raw_results/{lang}/results.yaml {mydir}/prompts/{lang}/ {mydir}/outputdir/"
        )
    # run_tool(phenopacket_dir=testdata_dir.joinpath("phenopackets"), output_dir=raw_results_dir)
