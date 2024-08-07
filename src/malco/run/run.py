from pathlib import Path
import multiprocessing
import subprocess


def call_ontogpt(lang, raw_results_dir, input_dir, model, modality): 
    if modality=="several_languages":
        command = (
            f"ontogpt -v run-multilingual-analysis "
            f"--output={raw_results_dir}/{lang}/results.yaml "  # save raw OntoGPT output
            f"{input_dir}/prompts/{lang}/ "
            f"{raw_results_dir}/{lang}/differentials_by_file/ "
            f"--model={model}"
        )
    elif modality=="several_models":
        command = (
            f"ontogpt -v run-multilingual-analysis "
            f"--output={raw_results_dir}/{model}/results.yaml "  # save raw OntoGPT output
            f"{input_dir}/prompts/{lang}/ "
            f"{raw_results_dir}/{model}/differentials_by_file/ "
            f"--model={model}"
        )
    else:
        command(f"echo Something is not working...")
    print(f"Running command: {command}")
    process = subprocess.Popen(command, shell=True)
    process.communicate()
    print(f"Finished command for language {lang} and model {model}") 


def run(testdata_dir: Path,
        raw_results_dir: Path,
        input_dir: Path,
        langs: tuple,
        models: tuple,
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

    modality = "several_languages"
    with multiprocessing.Pool(processes=max_workers) as pool:
        pool.starmap(call_ontogpt, [(lang, raw_results_dir / "multilingual", input_dir, "gpt-4-turbo", modality) for lang in langs])

    # English only many models
    modality = "several_models"
    with multiprocessing.Pool(processes=max_workers) as pool:
        pool.starmap(call_ontogpt, [("en", raw_results_dir / "multimodel", input_dir, model, modality) for model in models])
