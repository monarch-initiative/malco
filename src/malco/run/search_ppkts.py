import os

def search_ppkts(input_dir, raw_results_dir, lang_or_model):
    original_inputdir = f"{input_dir}/prompts/{lang_or_model}/"
    diff_dir = f"{raw_results_dir}/{lang_or_model}/differentials_by_file/"
    
    # files = os.ls(diff_dir)
    files = []
    for (dirpath, dirnames, filenames) in os.walk(diff_dir):
        files.extend(filenames)
        break
    
    # if files not exist
    if files==[]:
        return original_inputdir
    else:
        selected_indir = original_inputdir + "tmp/"
        os.makedir(selected_indir)

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
            os.copy(promptfile, selected_indir)
    return selected_indir