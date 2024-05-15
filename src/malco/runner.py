import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
from pheval.runners.runner import PhEvalRunner

from malco.post_process.mondo_score_utils import score_grounded_result
from malco.post_process.post_process import post_process
from malco.run.run import run

import os


@dataclass
class MalcoRunner(PhEvalRunner):
    input_dir: Path
    testdata_dir: Path
    tmp_dir: Path
    output_dir: Path
    config_file: Path
    version: str

    import requests
    import zipfile
    import os

    def prepare(
        self,
        phenopacket_zip_url="https://github.com/monarch-initiative/phenopacket-store/releases/download/0.1.8/all_phenopackets.zip",
        phenopacket_dir="phenopacket-store",
    ):
        """
        Pre-process any data and inputs necessary to run the tool.
        """
        print("Preparing...\n")
        # Ensure we have phenopacket-store downloaded
        phenopacket_store_path = os.path.join(self.input_dir, phenopacket_dir)
        if os.path.exists(phenopacket_store_path):
            print(f"{phenopacket_store_path} exists, skipping download.")
        else:
            print(f"{phenopacket_store_path} doesn't exist, downloading phenopackets...")
            self._download_phenopackets(phenopacket_zip_url, phenopacket_dir)

        # os.system(f"java -jar {self.input_dir}/phenopacket2prompt.jar download")
        # os.system(
        #     f"java -jar {self.input_dir}/phenopacket2prompt.jar batch -d {phenopacket_store_path}")

    def run(self):
        """
        Run the tool to produce the raw output.
        """
        print("running with predictor")
        # run(self.testdata_dir, self.raw_results_dir)

    def post_process(self, make_plot=True):
        """
        Post-process the raw output into PhEval standardised TSV output.
        """
        print("post processing results to PhEval standardised TSV output.")
        # post_process(raw_results_dir=self.raw_results_dir, output_dir=self.output_dir)

        if make_plot:
            self._make_plot()

    def _download_phenopackets(self, phenopacket_zip_url, phenopacket_dir):
        # Ensure the directory for storing the phenopackets exists
        phenopacket_store_path = os.path.join(self.input_dir, phenopacket_dir)
        os.makedirs(phenopacket_store_path, exist_ok=True)

        # Download the phenopacket release zip file
        response = requests.get(phenopacket_zip_url)
        zip_path = os.path.join(self.input_dir, "all_phenopackets.zip")
        with open(zip_path, "wb") as f:
            f.write(response.content)
        print("Download completed.")

        # Unzip the phenopacket release zip file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(phenopacket_store_path)
        print("Unzip completed.")

    def _make_plot(self, prompt_dir="prompts", correct_answer_file="correct_results.tsv"):
        # Read in results TSVs from self.output_dir that match glob results*tsv --> TODO Leo: make more robust, had other results*tsv files from previous testing
        results_data = []
        results_files = []
        for subdir, dirs, files in os.walk(self.output_dir):
            for filename in files:
                if filename.startswith("result") and filename.endswith(".tsv"):
                    file_path = os.path.join(subdir, filename)
                    df = pd.read_csv(file_path, sep="\t")
                    results_data.append(df)
                    # Append both the subdirectory relative to output_dir and the filename
                    results_files.append(os.path.relpath(file_path, self.output_dir))
        # Read in correct answers from prompt_dir
        answers_path = os.path.join(os.getcwd(), prompt_dir, correct_answer_file)
        answers = pd.read_csv(
            answers_path, sep="\t", header=None, names=["description", "term", "label"]
        )

        # Mapping each label to its correct term
        label_to_correct_term = answers.set_index("label")["term"].to_dict()

        # Calculate the Mean Reciprocal Rank (MRR) for each file
        mrr_scores = []
        for df in results_data:
            # For each label in the results file, find if the correct term is ranked
            print(df)
            df["rank"] = df.groupby("label")["score"].rank(ascending=False, method="first")
            label_4_non_eng = df["label"].str.replace("json_es-prompt", "json_en-prompt")
            df["correct_term"] = label_4_non_eng.map(label_to_correct_term)
            # df['term'] is sometimes a Mondo ID
            # df['correct_term'] is always an OMIM
            # TODO: call OAK and get OMIM IDs for df['term'] and see if df['correct_term'] is one of them
            # if so, df["is_correct"] = True
            df["is_correct"] = df["term"] == df["correct_term"]
            # match_score = score_grounded_result("MONDO:0008029", "OMIM:158810")
            df['is_correct'] = df.apply(
                lambda row: score_grounded_result(row['term'], row['correct_term']) > 0,
                axis=1)

            # Calculate reciprocal rank
            df["reciprocal_rank"] = df.apply(
                lambda row: 1 / row["rank"] if row["is_correct"] else 0, axis=1
            )
            # Calculate MRR for this file
            mrr = df.groupby("label")["reciprocal_rank"].max().mean()
            mrr_scores.append(mrr)

        # Plotting the results
        sns.barplot(x=results_files, y=mrr_scores)
        plt.xticks(rotation=90)  # Rotate labels for better readability
        plt.xlabel("Results File")
        plt.ylabel("Mean Reciprocal Rank (MRR)")
        plt.title("MRR of Correct Answers Across Different Results Files")
        plt.show()
