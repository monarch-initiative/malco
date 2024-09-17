import os
import pandas as pd
from collections import Counter
import argparse
import matplotlib.pyplot as plt


def compute_summary_statistics(input_dir, output_file, output_plot):
    # Initialize the counter for each rank
    rank_counter = Counter()

    # Iterate through all files in the directory ending with .tsv
    for filename in os.listdir(input_dir):
        if filename.endswith('.tsv'):
            filepath = os.path.join(input_dir, filename)
            # Read the TSV file
            df = pd.read_csv(filepath, sep='\t')

            # Find the first occurrence of the correct diagnosis
            correct_rank = df[df['is_correct'] == True].index.min() + 1 if not df[
                df['is_correct'] == True].empty else None

            # Increment the appropriate counter based on the rank or nf if not found
            if correct_rank is not None and 1 <= correct_rank <= 10:
                rank_counter[f'n{correct_rank}'] += 1
            else:
                rank_counter['nf'] += 1

    # Get the total number of records processed
    total_files = sum(rank_counter.values())

    # Prepare the row to be written to the output file
    output_row = [
        'en',  # Assuming language is 'en' as per the example
        rank_counter.get('n1', 0),
        rank_counter.get('n2', 0),
        rank_counter.get('n3', 0),
        rank_counter.get('n4', 0),
        rank_counter.get('n5', 0),
        rank_counter.get('n6', 0),
        rank_counter.get('n7', 0),
        rank_counter.get('n8', 0),
        rank_counter.get('n9', 0),
        rank_counter.get('n10', 0),
        rank_counter.get('n10', 0) / total_files if total_files else 0,
        # n10p: proportion of n10 hits
        rank_counter.get('nf', 0)
    ]

    # Write the results to the output file
    with open(output_file, 'w') as f:
        f.write('lang\tn1\tn2\tn3\tn4\tn5\tn6\tn7\tn8\tn9\tn10\tn10p\tnf\n')
        f.write('\t'.join(map(str, output_row)) + '\n')

    print(f"Summary statistics written to {output_file}")

    # Generate the plot
    hits = ['Top-1', 'Top-3', 'Top-10']
    percentages = [
        rank_counter.get('n1', 0) / total_files * 100 if total_files else 0,
        sum(rank_counter.get(f'n{i}', 0) for i in
            range(1, 4)) / total_files * 100 if total_files else 0,
        sum(rank_counter.get(f'n{i}', 0) for i in
            range(1, 11)) / total_files * 100 if total_files else 0,
    ]

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.bar(hits, percentages, color=['blue', 'green', 'orange'])
    plt.xlabel('Hits')
    plt.ylabel('Percent of cases')
    plt.title('Top-k accuracy of correct diagnoses')
    plt.ylim(0, 100)  # Adjust this as needed
    plt.savefig(output_plot)
    plt.close()

    print(f"Plot saved to {output_plot}")


def main():
    # Command-line interface for the script
    parser = argparse.ArgumentParser(
        description="Compute summary statistics for disease ranking results.")
    parser.add_argument(
        '-i', '--input_dir',
        type=str,
        required=True,
        help="Directory containing TSV files. Example: 'outputdir_all_2024_07_04/pheval_disease_results/'"
    )
    parser.add_argument(
        '-o', '--output_file',
        type=str,
        required=True,
        help="Path to output TSV file. Example: 'outputdir_all_2024_07_04/plots/topn_result_exomiser.tsv'"
    )
    parser.add_argument(
        '-p', '--output_plot',
        type=str,
        required=True,
        help="Path to save the output plot. Example: 'outputdir_all_2024_07_04/plots/topn_result_exomiser_plot.png'"
    )
    args = parser.parse_args()

    # Call the function with command line arguments
    compute_summary_statistics(args.input_dir, args.output_file, args.output_plot)


if __name__ == "__main__":
    #  python make_hits_at_n_plot_exomiser.py -i ../../../outputdir_all_2024_07_04/pheval_disease_results/ -o ../../../outputdir_all_2024_07_04/plots/topn_result_exomiser.tsv -p ../../../outputdir_all_2024_07_04/plots/topn_result_exomiser_plot.png
    main()
