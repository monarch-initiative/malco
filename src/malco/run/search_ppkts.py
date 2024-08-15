import os
import shutil

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