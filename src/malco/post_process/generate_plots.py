import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os
import csv

# Make a nice plot, use it as function or as script

def make_plots(mrr_file, plot_dir, languages, num_ppkt, models, topn_file, comparing):
    if comparing=="model":
        name_string = str(len(models))
    else:
        name_string = str(len(languages))

    with mrr_file.open('r', newline = '') as f:
        lines = csv.reader(f, quoting = csv.QUOTE_NONNUMERIC, delimiter = '\t', lineterminator='\n')
        results_files = next(lines)
        mrr_scores = next(lines)
            
    print(results_files)
    print(mrr_scores)

    # Plotting the mrr results
    sns.barplot(x = results_files, y = mrr_scores)
    plt.xlabel("Results File")
    plt.ylabel("Mean Reciprocal Rank (MRR)")
    plt.title("MRR of Correct Answers Across Different Results Files")
    plot_path = plot_dir /  (name_string + "_" + comparing + "_" + str(num_ppkt) + "ppkt.png")
    plt.savefig(plot_path)
    plt.close()

    # Plotting bar-plots with top<n> ranks
    df = pd.read_csv(topn_file, delimiter='\t')
    df["top1"] = df['n1']
    df["top3"] = df["n1"] + df["n2"] + df["n3"]
    df["top5"] = df["top3"] + df["n4"] + df["n5"]
    df["top10"] = df["top5"] + df["n6"] + df["n7"] + df["n8"] + df["n9"] + df["n10"]
    df["not_found"] = df["nf"]
    
    df_aggr = pd.DataFrame()
    df_aggr = pd.melt(df, id_vars=comparing, value_vars=["top1", "top3", "top5", "top10", "not_found"], var_name="Rank_in", value_name="counts")
    df_aggr["percentage"] = df_aggr["counts"]/num_ppkt
    bar_data_file = plot_dir / "topn_aggr.tsv"
    df_aggr.to_csv(bar_data_file, sep='\t', index=False)

    sns.barplot(x="Rank_in", y="percentage", data = df_aggr, hue = comparing)

    plt.xlabel("Number of Ranks in")
    plt.ylabel("Percentage of Cases")
    plt.title("Rank Comparison for Differential Diagnosis")
    plt.legend(title=comparing)
    plot_path = plot_dir /  ("barplot_" + name_string + "_" + comparing + "_" + str(num_ppkt) + "ppkt.png")
    plt.savefig(plot_path)
    plt.close()
    
