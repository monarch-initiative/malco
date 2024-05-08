from pathlib import Path

from malco.run.run_tool import run_tool
from ontogpt.cli import run_multilingual_analysis
import os


def run(testdata_dir: Path, raw_results_dir: Path) -> None:
    """
    Run the tool to obtain the raw results.

    Args:
        testdata_dir: Path to the test data directory.
        raw_results_dir: Path to the raw results directory.
    """
    mydir = os.getcwd()
    # TODO figure out how to run one language at a time, not like the next line
    # lang_list = os.listdir(mydir + "prompts")
    """
    run_multilingual_analysis(
        input_data_dir=mydir + "prompts/en/PMID_23993194_Family_2_Case_2-prompt",
        output_directory=mydir + "outputdir/",
        output=mydir + "outputdir/" + "grounded_en",  # TODO generalize lang
        output_format="yaml",
        model="gpt-4-turbo",
        ext=".txt",
    )
    """
    os.system(
        f"ontogpt run-multilingual-analysis --output={mydir}/outputdir/grounded_en/results.yaml --output-format=yaml {mydir}/prompts/et/ {mydir}outputdir/"
    )
    # run_tool(phenopacket_dir=testdata_dir.joinpath("phenopackets"), output_dir=raw_results_dir)
