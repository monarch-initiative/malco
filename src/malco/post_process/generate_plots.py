import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os
import csv

# Make a nice plot, use it as function or as script

def make_plots(plot_data_file, plot_dir, languages, num_ppkt, topn_file):
    with plot_data_file.open('r', newline = '') as f:
        lines = csv.reader(f, quoting = csv.QUOTE_NONNUMERIC, delimiter = '\t', lineterminator='\n')
        results_files = next(lines)
        mrr_scores = next(lines)
        #lines = f.read().splitlines()
            
    print(results_files)
    print(mrr_scores)

    # Plotting the mrr results
    sns.barplot(x = results_files, y = mrr_scores)
    plt.xlabel("Results File")
    plt.ylabel("Mean Reciprocal Rank (MRR)")
    plt.title("MRR of Correct Answers Across Different Results Files")
    plot_path = plot_dir /  (str(len(languages)) + "_langs_" + str(num_ppkt) + "ppkt.png")
    plt.savefig(plot_path)

    # Plotting bar-plots with top<n> ranks
    df = pd.read_csv(topn_file, delimiter='\t')
    df["top1"] = df['n1']
    df["top3"] = df["n1"] + df["n2"] + df["n3"]
    df["top5"] = df["top3"] + df["n4"] + df["n5"]
    df["top10"] = df["top5"] + df["n6"] + df["n7"] + df["n8"] + df["n9"] + df["n10"]
    df["not_found"] = df["nf"]
    
    df_aggr = pd.DataFrame()
    df_aggr = pd.melt(df, id_vars="lang", value_vars=["top1", "top3", "top5", "top10", "not_found"], var_name="Rank_in", value_name="counts")
    bar_data_file = plot_dir / "topn_aggr.tsv"
    df_aggr.to_csv(bar_data_file, sep='\t', index=False)

    sns.barplot(x="Rank_in", y="counts", data = df_aggr, hue = "lang")

    plt.xlabel("Number of Ranks")
    plt.ylabel("Number of Correct Diagnoses")
    plt.title("Rank Comparison for Different Languages")
    plot_path = plot_dir /  ("barplot_" + str(len(languages)) + "_langs_" + str(num_ppkt) + "ppkt.png")
    plt.savefig(plot_path)
    plt.show()

    
