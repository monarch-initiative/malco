from pathlib import Path
import multiprocessing
import subprocess


def call_ontogpt(lang, raw_results_dir, input_dir):
    command = (
        f"ontogpt -v run-multilingual-analysis "
        f"--output={raw_results_dir}/{lang}/results.yaml "  # save raw OntoGPT output
        f"{input_dir}/prompts/{lang}/ "
        f"{raw_results_dir}/{lang}/differentials_by_file/"
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

    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    with multiprocessing.Pool(processes=max_workers) as pool:
        pool.starmap(call_ontogpt, [(lang, raw_results_dir, input_dir) for lang in langs])
