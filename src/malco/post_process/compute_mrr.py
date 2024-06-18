import os 
import csv
from pathlib import Path
import pandas as pd
import pickle as pkl
from malco.post_process.mondo_score_utils import score_grounded_result
from malco.post_process.mondo_score_utils import omim_mappings
from typing import List
from oaklib.interfaces import OboGraphInterface, MappingProviderInterface


from oaklib import get_adapter

from viztracer import VizTracer


def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo") # , cache_lookups=True

def compute_mrr(output_dir, prompt_dir, correct_answer_file) -> Path:
    # Read in results TSVs from self.output_dir that match glob results*tsv 
    results_data = []
    results_files = []
    num_ppkt = 0

    for subdir, dirs, files in os.walk(output_dir):
        for filename in files:
            if filename.startswith("result") and filename.endswith(".tsv"):
                file_path = os.path.join(subdir, filename)
                df = pd.read_csv(file_path, sep="\t")
                num_ppkt = df["label"].nunique()
                results_data.append(df)
                # Append both the subdirectory relative to output_dir and the filename
                results_files.append(os.path.relpath(file_path, output_dir))
    # Read in correct answers from prompt_dir
    answers_path = os.path.join(os.getcwd(), prompt_dir, correct_answer_file)
    answers = pd.read_csv(
        answers_path, sep="\t", header=None, names=["description", "term", "label"]
    )

    # Mapping each label to its correct term
    label_to_correct_term = answers.set_index("label")["term"].to_dict()
    # Calculate the Mean Reciprocal Rank (MRR) for each file
    mrr_scores = []

    tracer = VizTracer(tracer_entries=8000000)
    tracer.start()

    mondo = mondo_adapter()

    for df in results_data:
        # For each label in the results file, find if the correct term is ranked
        df["rank"] = df.groupby("label")["score"].rank(ascending=False, method="first")
        label_4_non_eng = df["label"].str.replace("_[a-z][a-z]-prompt", "_en-prompt", regex=True)
        df["correct_term"] = label_4_non_eng.map(label_to_correct_term)

        # df['term'] is Mondo or OMIM ID, or even disease label
        # df['correct_term'] is an OMIM
        # call OAK and get OMIM IDs for df['term'] and see if df['correct_term'] is one of them
        # in the case of phenotypic series, if Mondo corresponds to grouping term, accept it
                        
        #df['is_correct'] = df.apply(
        #       lambda row: score_grounded_result(row['term'], row['correct_term'], mondo) > 0,
         #   axis=1)

        # Calculate reciprocal rank
        # Make sure caching is used in the following by unwrapping explicitly
        results = []
        for idx, row in df.iterrows():
            val = score_grounded_result(row['term'], row['correct_term'], mondo)
            is_correct = val > 0
            results.append(is_correct)

        df['is_correct'] = results

        df["reciprocal_rank"] = df.apply(
            lambda row: 1 / row["rank"] if row["is_correct"] else 0, axis=1
        )
        # Calculate MRR for this file
        mrr = df.groupby("label")["reciprocal_rank"].max().mean()
        mrr_scores.append(mrr)
        print('=' * 100)
        print('score_grounded_result cache info:\n')
        print(score_grounded_result.cache_info())
        print('=' * 100)
        print('omim_mappings cache info:\n')
        print(omim_mappings.cache_info())

    tracer.stop()
    tracer.save("mondoscore_viz_prof.json")

    print("MRR scores are:\n")
    print(mrr_scores)
    plot_dir = output_dir / "plots"
    plot_dir.mkdir(exist_ok=True)
    plot_data_file = plot_dir / "plotting_data.tsv"

    # write out results for plotting 
    with plot_data_file.open('w', newline = '') as dat:
        writer = csv.writer(dat, quoting = csv.QUOTE_NONNUMERIC, delimiter = '\t', lineterminator='\n')
        writer.writerow(results_files)
        writer.writerow(mrr_scores)
    return plot_data_file, plot_dir, num_ppkt
