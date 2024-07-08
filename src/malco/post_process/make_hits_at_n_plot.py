import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import sys

def make_combined_hits_at_n_plot(file1, file2):
    # Read the data from both files
    df1 = pd.read_csv(file1, delimiter='\t')
    df2 = pd.read_csv(file2, delimiter='\t')

    # Calculate total cases for each dataset
    total_cases1 = df1.iloc[:, 1:].sum(axis=1).values[0]
    total_cases2 = df2.iloc[:, 1:].sum(axis=1).values[0]

    # Calculate percentages for hits at 1, 3, and 10 for both datasets
    def calculate_percentages(df, total_cases):
        return {
            'Top-1': df['n1'].values[0] / total_cases * 100,
            'Top-3': (df['n1'] + df['n2'] + df['n3']).values[0] / total_cases * 100,
            'Top-10': (df['n1'] + df['n2'] + df['n3'] + df['n4'] + df['n5'] +
                       df['n6'] + df['n7'] + df['n8'] + df['n9'] + df['n10']).values[0] / total_cases * 100
        }

    percentages1 = calculate_percentages(df1, total_cases1)
    percentages2 = calculate_percentages(df2, total_cases2)

    # Prepare data for plotting
    plot_data = {
        'Hits': ['Top-1', 'Top-3', 'Top-10'] * 2,
        'Percentage': [percentages1['Top-1'], percentages1['Top-3'], percentages1['Top-10'],
                       percentages2['Top-1'], percentages2['Top-3'], percentages2['Top-10']],
        'Dataset': ['Text-mined'] * 3 + ['Phenopacket'] * 3
    }
    plot_df = pd.DataFrame(plot_data)

    # Plot the grouped barplot
    plt.figure(figsize=(12, 6))
    sns.barplot(x='Hits', y='Percentage', hue='Dataset', data=plot_df)
    plt.xlabel("")
    plt.ylabel("Percent of cases")
    plt.title("Top-k accuracy of GPT")
    plt.ylim(0, 100)  # Adjust this as needed
    plt.legend(title="")
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python plot_hits_at_n.py <text_mined_file> <phenopacket_file>")
        sys.exit(1)

    # python make_hits_at_n_plot.py  ../../../outputdir_text_mined_2024_07_02/plots/topn_result.tsv ../../../outputdir_all_2024_07_04/plots/topn_result.tsv

    text_mined_file = sys.argv[1]
    phenopacket_file = sys.argv[2]

    make_combined_hits_at_n_plot(text_mined_file, phenopacket_file)
