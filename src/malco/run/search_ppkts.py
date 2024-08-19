import os
import shutil

# Check what ppkts have already been computed in current output dir, for current run parameters
# ontogpt will run every txt that is in inputdir, we need a tmp inputdir
# This tmp inputdir contains only the prompts that have not yet been computed for a given, fixed model (pars set)
# If it exists and is not empty, create a list of what is in {raw_results_dir}/{lang}/differentials_by_file/
# The file names are identical to the prompt file names, with an extra ".result"
# Copy all prompt files in the new tmp inputdir, except the ones of line above
    
def search_ppkts(input_dir, raw_results_dir, lang_or_model, *args):
    if args[0]:
        original_inputdir = f"{input_dir}/prompts/en/"
    else:
        original_inputdir = f"{input_dir}/prompts/{lang_or_model}/"
    diff_dir = f"{raw_results_dir}/{lang_or_model}/differentials_by_file/"
    
    # files is a ls of diff_dir
    files = []
    for (dirpath, dirnames, filenames) in os.walk(diff_dir):
        files.extend(filenames) # list of filenames
        break
    
    # if files not exist
    if files==[]:
        return original_inputdir
    else:
        selected_indir = f"{input_dir}/prompts/tmp/{lang_or_model}"
        os.makedirs(selected_indir)

    # prompts = os.ls(original_inputdir)
    promptfiles = []
    for (dirpath, dirnames, filenames) in os.walk(original_inputdir):
        promptfiles.extend(filenames) 
        break

    # foreach promptfile in original_inputdir
    for promptfile in promptfiles:
        aux = promptfile + ".result"
        if aux in files:
            continue
        else:
            shutil.copyfile(original_inputdir + promptfile, selected_indir + "/" + promptfile)
    return selected_indir