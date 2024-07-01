import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import sys


def make_hits_at_n_plot_from_data_file(plot_data_file):
    # Read the data
    df = pd.read_csv(plot_data_file, delimiter='\t')

    # Calculate the total number of cases
    total_cases = df.iloc[:, 1:].sum(axis=1).values[0]

    # Calculate percentages for hits at 1, 3, 5, and 10
    df['hits_at_1'] = df['n1'] / total_cases * 100
    df['hits_at_3'] = (df['n1'] + df['n2'] + df['n3']) / total_cases * 100
    df['hits_at_5'] = (df['n1'] + df['n2'] + df['n3'] + df['n4'] + df[
        'n5']) / total_cases * 100
    df['hits_at_10'] = (df['n1'] + df['n2'] + df['n3'] + df['n4'] + df['n5'] + df[
        'n6'] + df['n7'] + df['n8'] + df['n9'] + df['n10']) / total_cases * 100

    # Prepare data for plotting
    plot_data = {
        'Hits': ['Top-1', 'Top-3', 'Top-10'],
        'Percentage': [df['hits_at_1'].values[0], df['hits_at_3'].values[0],
                       df['hits_at_10'].values[0]]
    }
    plot_df = pd.DataFrame(plot_data)

    # Plot the barplot
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Hits', y='Percentage', data=plot_df)
    plt.xlabel("")
    plt.ylabel("Percent of cases")
    plt.title("Top-k accuracy of GPT")
    plt.ylim(0, 45)
    plt.show()


if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("Usage: python plot_hits_at_n.py <plot_data_file>")
    #     sys.exit(1)

    # Path to the data file from the first argument
    # plot_data_file = sys.argv[1]
    plot_data_file = "../../../outputdir_all_2024_07_02/plots/topn_result.tsv"

    # Call the function
    make_hits_at_n_plot_from_data_file(plot_data_file)
