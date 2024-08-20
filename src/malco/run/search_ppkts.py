import os
import shutil

    
def search_ppkts(input_dir, raw_results_dir, lang_or_model, *args):
    """
    Check what ppkts have already been computed in current output dir, for current run parameters.
    ontogpt will run every .txt that is in inputdir, we need a tmp inputdir 
    excluding already run cases.
    """
    if args[0]: # necessary extra handle, multiple models only do English
        original_inputdir = f"{input_dir}/prompts/en/"
    else:
        original_inputdir = f"{input_dir}/prompts/{lang_or_model}/"
    diff_dir = f"{raw_results_dir}/{lang_or_model}/differentials_by_file/"
    
    # files is a ls of diff_dir
    files = []
    # Create a list of what is in {raw_results_dir}/{lang}/differentials_by_file/
    for (dirpath, dirnames, filenames) in os.walk(diff_dir):
        files.extend(filenames) # list of filenames
        break
    
    # If no files are found, no previous run exists
    if files==[]:
        return original_inputdir
    else:
        # tmp inputdir contains prompts yet to be computed for a given model (pars set)
        selected_indir = f"{input_dir}/prompts/tmp/{lang_or_model}"
        os.makedirs(selected_indir)

    # prompts: ls original_inputdir
    promptfiles = []
    for (dirpath, dirnames, filenames) in os.walk(original_inputdir):
        promptfiles.extend(filenames) 
        break

    # foreach promptfile in original_inputdir
    for promptfile in promptfiles:
        # The file names are identical to the prompt file names, with an extra ".result"
        aux = promptfile + ".result"
        # If something failed and an empty file exists, run it again
        # Copy all prompt files in the new tmp inputdir, except the ones of line above
        if aux in files:
            emptyfile = (os.path.getsize(diff_dir + aux)==0)
            if not emptyfile:
                continue
            else:
                shutil.copyfile(original_inputdir + promptfile, selected_indir + "/" + promptfile)
        else:
            shutil.copyfile(original_inputdir + promptfile, selected_indir + "/" + promptfile)
    return selected_indir