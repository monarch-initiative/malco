import seaborn as sns
import matplotlib.pyplot as plt
import csv


def make_plots(mrr_data_file, hits_data_file, plot_dir, languages, num_ppkt):
    # Read MRR data
    with mrr_data_file.open('r', newline='') as f:
        lines = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC, delimiter='\t',
                           lineterminator='\n')
        results_files = next(lines)
        mrr_scores = next(lines)

    # Read hits_at_n data
    with hits_data_file.open('r', newline='') as f:
        lines = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC, delimiter='\t',
                           lineterminator='\n')
        header = next(lines)
        hits_data = list(lines)

    hits_files = [row[0] for row in hits_data]
    hits_at_1 = [row[1] for row in hits_data]
    hits_at_5 = [row[2] for row in hits_data]
    hits_at_10 = [row[3] for row in hits_data]

    print(results_files)
    print(mrr_scores)
    print(hits_files)
    print(hits_at_1)
    print(hits_at_5)
    print(hits_at_10)

    # Plotting the MRR results
    plt.figure(figsize=(10, 6))
    sns.barplot(x=results_files, y=mrr_scores)
    plt.xlabel("Results File")
    plt.ylabel("Mean Reciprocal Rank (MRR)")
    plt.title("MRR of Correct Answers Across Different Results Files")
    plot_path_mrr = plot_dir / (
                str(len(languages)) + "_langs_" + str(num_ppkt) + "ppkt_MRR.png")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(plot_path_mrr)
    plt.show()

    # Plotting the hits_at_n results
    plt.figure(figsize=(10, 6))
    data = {
        'Results File': hits_files,
        'Hits@1': hits_at_1,
        'Hits@5': hits_at_5,
        'Hits@10': hits_at_10
    }
    df = pd.DataFrame(data)
    df_melted = df.melt(id_vars='Results File', var_name='Hits@N',
                        value_name='Percentage')

    sns.barplot(x='Hits@N', y='Percentage', hue='Results File', data=df_melted)
    plt.xlabel("Hits@N")
    plt.ylabel("Percentage")
    plt.title("Hits@N of Correct Answers Across Different Results Files")
    plot_path_hits = plot_dir / (
                str(len(languages)) + "_langs_" + str(num_ppkt) + "ppkt_HitsAtN.png")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(plot_path_hits)
    plt.show()
