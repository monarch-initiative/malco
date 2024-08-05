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
    # Declare a tuple of languages and models
    #TODO move next 4 lines to input file
    languages = ("en", "es", "nl", "it", "de")
    models = ("gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o") # Decide on list of models: Claude-Sonnet (Anthropic key), 
    just_run = 1          # only run the run part of the code
    just_postprocess = 0  # only run the postprocess part of the code
    


    def prepare(self):
        """
        Pre-process any data and inputs necessary to run the tool.
        """
        print("Preparing...\n")
        pass

    def run(self):
        """
        Run the tool to produce the raw output.
        """
        print("running with predictor")
        run(testdata_dir=self.testdata_dir,
            raw_results_dir=self.raw_results_dir,
            input_dir=self.input_dir,
            langs=self.languages,
            models=self.models)


    def post_process(self,
                     print_plot=True,
                     prompts_subdir_name="prompts",
                     correct_answer_file="correct_results.tsv"
                     ):
        """
        Post-process the raw output into PhEval standardised TSV output.
        """
        print("post processing results to PhEval standardised TSV output.")

        post_process(raw_results_dir=self.raw_results_dir,
                     output_dir=self.output_dir,
                     langs=self.languages,
                     models=self.models)
        
        
        comparing = "language"
        mrr_file, plot_dir, num_ppkt, topn_file = compute_mrr(comparing,
            output_dir=self.output_dir / "multilingual" ,
            prompt_dir=os.path.join(self.input_dir, prompts_subdir_name),
            correct_answer_file=correct_answer_file,
            raw_results_dir=self.raw_results_dir / "multilingual")
        
        if print_plot:
            make_plots(mrr_file, plot_dir, self.languages, num_ppkt, self.models, topn_file, comparing)
        
        
        comparing = "model"
        mrr_file, plot_dir, num_ppkt, topn_file = compute_mrr( comparing,
            output_dir=self.output_dir / "multimodel" ,
            prompt_dir=os.path.join(self.input_dir, prompts_subdir_name),
            correct_answer_file=correct_answer_file,
            raw_results_dir=self.raw_results_dir / "multimodel" )
        
        if print_plot:
            make_plots(mrr_file, plot_dir, self.languages, num_ppkt, self.models, topn_file, comparing)
