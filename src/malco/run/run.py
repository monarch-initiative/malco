from pathlib import Path
import multiprocessing
import subprocess
import shutil
import os
from malco.run.search_ppkts import search_ppkts

def call_ontogpt(lang, raw_results_dir, input_dir, model, modality):
    
    if modality=="several_languages":
        selected_indir  = search_ppkts(input_dir, raw_results_dir, lang)
        yaml_file = f"{raw_results_dir}/{lang}/results.yaml"
        if Path(yaml_file).isFile():
            old_yaml_file = yaml_file
            yaml_file = f"{raw_results_dir}/{lang}/new_results.yaml"
        command = (
            f"ontogpt -v run-multilingual-analysis "
            f"--output={yaml_file} "  # save raw OntoGPT output
            f"{selected_indir} "
            #f"{input_dir}/prompts/{lang}/ "
            f"{raw_results_dir}/{lang}/differentials_by_file/ "
            f"--model={model}"
        )
    elif modality=="several_models":
        selected_indir  = search_ppkts(input_dir, raw_results_dir, model, True)
        yaml_file = f"{raw_results_dir}/{model}/results.yaml"   
        if Path(yaml_file).isFile():
            old_yaml_file = yaml_file
            yaml_file = f"{raw_results_dir}/{model}/new_results.yaml"     
        command = (
            f"ontogpt -v run-multilingual-analysis "
            f"--output={yaml_file} "  # save raw OntoGPT output
            f"{selected_indir} "
            #f"{input_dir}/prompts/{lang}/ "
            f"{raw_results_dir}/{model}/differentials_by_file/ "
            f"--model={model}"
        )
    else:
        command(f"echo Something is not working...")
    print(f"Running command: {command}")
    process = subprocess.Popen(command, shell=True)
    process.communicate()
    # Note: if file.txt.result is empty, what ends up in the yaml is still OK thanks to L39 in post_process_results_format.py
    print(f"Finished command for language {lang} and model {model}")
    try:
        with open(yaml_file, 'r') as file2concat:
            with open(old_yaml_file, 'a') as original_file:
                shutil.copyfileobj(file2concat, original_file)
        os.remove(yaml_file)
    except NameError:
        pass


#TODO decide whether to get rid of parallelization
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

    '''
    modality = "several_languages"
    with multiprocessing.Pool(processes=max_workers) as pool:
        pool.starmap(call_ontogpt, [(lang, raw_results_dir / "multilingual", input_dir, "gpt-4-turbo", modality) for lang in langs])
    '''
    
    # English only many models
    modality = "several_models"
    with multiprocessing.Pool(processes=max_workers) as pool:
        pool.starmap(call_ontogpt, [("en", raw_results_dir / "multimodel", input_dir, model, modality) for model in models])
            