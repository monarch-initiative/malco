# setup_run_pars
import csv

def import_inputdata(self):
    """Example inputfile is located in input_dir and named run_parameters.csv
    It should contain something like:
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    "en"
    "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"
    1, 0
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Meaning run english prompts with those 4 aforementioned models, and only execute the run function, not postprocess.

    Or something like:
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    "en", "es", "nl", "it", "de"
    "gpt-4"
    0, 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    Meaning run multilingual prompts with those 5 aforementioned languages, and only execute the function postprocess, not run.
    """
    with open(self.input_dir / "run_parameters.csv", 'r') as pars:
        lines = csv.reader(pars, quoting = csv.QUOTE_NONNUMERIC, delimiter = ',', lineterminator='\n')
        in_langs = next(lines)
        in_models = next(lines)
        in_what_to_run = next(lines)


    self.languages = tuple(in_langs)
    #self.languages = ("en", "es", "nl", "it", "de")
    #self.models = ("gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o") # Decide on list of models: Claude-Sonnet (Anthropic key), 
    self.models =  tuple(in_models)
    self.do_run_step = in_what_to_run[0]          # only run the run part of the code
    self.do_postprocess_step = in_what_to_run[1]  # only run the postprocess part of the code
