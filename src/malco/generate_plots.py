import seaborn as sns
import matplotlib.pyplot as plt


#TODO import data

print(results_files)
print(mrr_scores)

# Plotting the results
sns.barplot(x=results_files, y=mrr_scores)
#plt.xticks(rotation=90)  # Rotate labels for better readability
plt.xlabel("Results File")
plt.ylabel("Mean Reciprocal Rank (MRR)")
plt.title("MRR of Correct Answers Across Different Results Files")
plot_path = os.path.join(self.output_dir, "/plots/en_es_v1_78ppkt.png")
plt.savefig(plot_path)
plt.show()
