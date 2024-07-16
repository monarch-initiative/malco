from pathlib import Path
import multiprocessing
import subprocess


def call_ontogpt(lang, raw_results_dir, input_dir):
    command = (
        f"ontogpt -v run-multilingual-analysis "
        f"{input_dir}/prompts/{lang}/ "  # input_data_dir argument
        f"{raw_results_dir}/{lang}/differentials_by_file/ "  # output_directory argument
        f"--output={raw_results_dir}/{lang}/results.yaml"  # --output option
    )
    print(f"Running command: {command}")
    process = subprocess.Popen(command, shell=True)
    process.communicate()
    print(f"Finished command for {lang}")


def run(testdata_dir: Path,
        raw_results_dir: Path,
        input_dir: Path,
        langs: tuple,
        max_workers: int = None) -> None:
    """
    Run the tool to obtain the raw results.

    Args:
        testdata_dir: Path to the test data directory.
        raw_results_dir: Path to the raw results directory.
        output_dir: Path to the output directory.
        langs: Tuple of languages.
        max_workers: Maximum number of worker processes to use.
    """

    for lang in langs:
        call_ontogpt(lang, raw_results_dir, input_dir)
