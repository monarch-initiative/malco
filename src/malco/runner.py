import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests
from pheval.runners.runner import PhEvalRunner

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

    def prepare(self,
                phenopacket_zip_url="https://github.com/monarch-initiative/phenopacket-store/releases/download/0.1.8/all_phenopackets.zip",
                phenopacket_dir="phenopacket-store"):
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

        os.system(f"java -jar {self.input_dir}/phenopacket2prompt.jar download")
        os.system(
            f"java -jar {self.input_dir}/phenopacket2prompt.jar batch -d {phenopacket_store_path}")

    def run(self):
        """
        Run the tool to produce the raw output.
        """
        print("running with fake predictor")
        # run(self.testdata_dir, self.raw_results_dir)

    def post_process(self):
        """
        Post-process the raw output into PhEval standardised TSV output.
        """
        print("post processing results to PhEval standardised TSV output.")
        # post_process(raw_results_dir=self.raw_results_dir, output_dir=self.output_dir)

    def _download_phenopackets(self, phenopacket_zip_url, phenopacket_dir):
        # Ensure the directory for storing the phenopackets exists
        phenopacket_store_path = os.path.join(self.input_dir, phenopacket_dir)
        os.makedirs(phenopacket_store_path, exist_ok=True)

        # Download the phenopacket release zip file
        response = requests.get(phenopacket_zip_url)
        zip_path = os.path.join(self.input_dir, 'all_phenopackets.zip')
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        print("Download completed.")

        # Unzip the phenopacket release zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(phenopacket_store_path)
        print("Unzip completed.")
