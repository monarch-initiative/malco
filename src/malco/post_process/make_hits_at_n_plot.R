library(ggplot2)
library(readr)
library(dplyr)
library(tidyr)

make_combined_hits_at_n_plot <- function(file1, file2, output_file) {
  # Read the data from both files
  df1 <- read_tsv(file1)
  df2 <- read_tsv(file2)

  # Calculate total cases for each dataset
  total_cases1 <- sum(df1[, 2:ncol(df1)])
  total_cases2 <- sum(df2[, 2:ncol(df2)])

  # Calculate percentages for hits at 1, 3, and 10 for both datasets
  calculate_percentages <- function(df, total_cases) {
    list(
      Top_1 = df$n1[1] / total_cases * 100,
      Top_3 = (df$n1 + df$n2 + df$n3)[1] / total_cases * 100,
      Top_10 = (df$n1 + df$n2 + df$n3 + df$n4 + df$n5 + df$n6 + df$n7 + df$n8 + df$n9 + df$n10)[1] / total_cases * 100
    )
  }

  percentages1 <- calculate_percentages(df1, total_cases1)
  percentages2 <- calculate_percentages(df2, total_cases2)

  # Prepare data for plotting
  plot_data <- tibble(
    Hits = factor(rep(c("Top 1", "Top 3", "Top 10"), 2), levels = c("Top 1", "Top 3", "Top 10")),
    Percentage = c(percentages1$Top_1, percentages1$Top_3, percentages1$Top_10,
                   percentages2$Top_1, percentages2$Top_3, percentages2$Top_10),
    Dataset = rep(c("Text-mined", "Phenopacket"), each = 3)
  )

  # Create the plot
  p <- ggplot(plot_data, aes(x = Hits, y = Percentage, fill = Dataset)) +
    geom_bar(stat = "identity", position = position_dodge()) +
    labs(x = "", y = "Percent of cases", title = "") +
    ylim(0, 60) +  # Adjust this as needed
    theme_minimal() +
    theme(
      legend.position = c(0.6, 0.9),  # Position the legend inside the plot, adjusted to the left
      legend.title = element_blank(),
      legend.text = element_text(size = 14),  # Increase legend text size
      axis.text = element_text(size = 18),  # Increased font size
      axis.title = element_text(size = 20),  # Increased font size
      axis.title.y = element_text(margin = margin(t = 0, r = 20, b = 0, l = 0))  # Add margin to y-axis label
    ) +
    guides(fill = guide_legend(override.aes = list(size = 5)))  # Increase the size of legend keys

  # Save the plot to the specified file
  ggsave(output_file, plot = p, width = 12, height = 6, device = "png")
}

# Main execution
args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 3) {
  stop("Usage: Rscript plot_hits_at_n.R <text_mined_file> <phenopacket_file> <output_file>")
}

text_mined_file <- args[1]
phenopacket_file <- args[2]
output_file <- args[3]

make_combined_hits_at_n_plot(text_mined_file, phenopacket_file, output_file)
