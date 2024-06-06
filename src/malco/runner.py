from dataclasses import dataclass
from pathlib import Path

from pheval.runners.runner import PhEvalRunner

from malco.post_process.compute_mrr import compute_mrr
from malco.post_process.post_process import post_process
from malco.run.run import run
from malco.prepare.setup_phenopackets import setup_phenopackets
from malco.post_process.generate_plots import make_plots
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
    languages = ("en", "es", "nl", "it", "de")

    def prepare(self):
        """
        Pre-process any data and inputs necessary to run the tool.
        """
        print("Preparing...\n")
        # Before this prepare step:
        # We start with cohort with 1 phenopacket per disease, run
        # phenopacket2prompt.jar to get prompts
        # We then commit this to the repo, and the phenopackets and prompts here
        # are the source of truth
        pass

    def run(self):
        """
        Run the tool to produce the raw output.
        """
        print("running with predictor")

        run(testdata_dir=self.testdata_dir,
            raw_results_dir=self.raw_results_dir,
            input_dir=self.input_dir,
            langs=self.languages)

    def post_process(self, print_plot=True):
        """
        Post-process the raw output into PhEval standardised TSV output.
        """
        print("post processing results to PhEval standardised TSV output.")

        post_process(raw_results_dir=self.raw_results_dir, output_dir=self.output_dir,
                     langs=self.languages)

        plot_data_file, plot_dir, num_ppkt = (
            compute_mrr(output_dir=self.output_dir,
                        prompt_dir="prompts",
                        correct_answer_file="correct_results.tsv")
        )
        if print_plot:
            make_plots(plot_data_file, plot_dir, self.languages, num_ppkt)
