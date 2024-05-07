from dataclasses import dataclass
from pathlib import Path

from pheval.runners.runner import PhEvalRunner

from pheval_template.post_process.post_process import post_process
from pheval_template.run.run import run


@dataclass
class TemplatePhEvalRunner(PhEvalRunner):
    input_dir: Path
    testdata_dir: Path
    tmp_dir: Path
    output_dir: Path
    config_file: Path
    version: str

    def prepare(self):
        """
        Pre-process any data and inputs necessary to run the tool.
        """
        print("preparing")

    def run(self):
        """
        Run the tool to produce the raw output.
        """
        print("running with fake predictor")
        run(self.testdata_dir, self.raw_results_dir)

    def post_process(self):
        """
        Post-process the raw output into PhEval standardised TSV output.
        """
        print("post processing results to PhEval standardised TSV output.")
        post_process(raw_results_dir=self.raw_results_dir, output_dir=self.output_dir)
