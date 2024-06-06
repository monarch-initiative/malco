import seaborn as sns
import matplotlib.pyplot as plt
import os
import csv

# Make a nice plot, use it as function or as script

def make_plots(plot_data_file, plot_dir, languages, num_ppkt):
    with plot_data_file.open('r', newline = '') as f:
        lines = csv.reader(f, quoting = csv.QUOTE_NONNUMERIC, delimiter = '\t', lineterminator='\n')
        results_files = next(lines)
        mrr_scores = next(lines)
        #lines = f.read().splitlines()
            
    print(results_files)
    print(mrr_scores)

    # Plotting the results
    sns.barplot(x = results_files, y = mrr_scores)
    plt.xlabel("Results File")
    plt.ylabel("Mean Reciprocal Rank (MRR)")
    plt.title("MRR of Correct Answers Across Different Results Files")
    plot_path = plot_dir /  (str(len(languages)) + "_langs_" + str(num_ppkt) + "ppkt.png")
    plt.savefig(plot_path)
    plt.show()
