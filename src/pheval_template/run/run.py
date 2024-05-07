from pathlib import Path

from pheval_template.run.run_tool import run_tool


def run(testdata_dir: Path, raw_results_dir: Path) -> None:
    """
    Run the tool to obtain the raw results.

    Args:
        testdata_dir: Path to the test data directory.
        raw_results_dir: Path to the raw results directory.
    """
    run_tool(phenopacket_dir=testdata_dir.joinpath("phenopackets"), output_dir=raw_results_dir)
