from dataclasses import dataclass
from pathlib import Path

import requests
from pheval.runners.runner import PhEvalRunner

from malco.post_process.compute_mrr import compute_mrr
from malco.post_process.post_process import post_process
from malco.run.run import run
from malco.prepare.setup_phenopackets import setup_phenopackets
import os

@dataclass
class MalcoRunner(PhEvalRunner):
    input_dir: Path
    testdata_dir: Path
    tmp_dir: Path
    output_dir: Path
    config_file: Path
    version: str
    # Declare a tuple (immutable!) of languages 
    languages = ("en", "es")

    def prepare(self):
        """
        Pre-process any data and inputs necessary to run the tool.
        """
        print("Preparing...\n")
        # Ensure we have phenopacket-store downloaded
        phenopacket_store_path = setup_phenopackets(self)
        
        os.system(f"java -jar {self.input_dir}/phenopacket2prompt.jar download")
        os.system(
             f"java -jar {self.input_dir}/phenopacket2prompt.jar batch -d {phenopacket_store_path}")
        

    def run(self):
        """
        Run the tool to produce the raw output.
        """
        print("running with predictor")
        run(testdata_dir=self.testdata_dir, raw_results_dir=self.raw_results_dir,
             output_dir=self.output_dir, langs=self.languages)

    def post_process(self):
        """
        Post-process the raw output into PhEval standardised TSV output.
        """
        print("post processing results to PhEval standardised TSV output.")
        post_process(raw_results_dir=self.raw_results_dir, output_dir=self.output_dir, 
                     langs=self.languages)

        compute_mrr(output_dir=self.output_dir, prompt_dir="prompts", correct_answer_file="correct_results.tsv")
