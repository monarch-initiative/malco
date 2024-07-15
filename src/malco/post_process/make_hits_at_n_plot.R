library(ggplot2)
library(readr)
library(dplyr)
library(tidyr)
library(ggsci)
library(gridExtra)  # Load the gridExtra package

make_combined_hits_at_n_plot <- function(file1, mrr_data, output_file) {
  # Read the data from the file
  df1 <- read_tsv(file1, col_types = cols(.default = col_double(), lang = col_character()))

  # Read the MRR data
  mrr_value <- as.numeric(read_lines(mrr_data)[2])

  # Calculate total cases for the dataset
  total_cases1 <- sum(df1[, 2:ncol(df1)])

  # Calculate percentages for hits at 1, 3, and 10
  calculate_percentages <- function(df, total_cases) {
    list(
      Top_1 = df$n1[1] / total_cases * 100,
      Top_3 = (df$n1 + df$n2 + df$n3)[1] / total_cases * 100,
      Top_10 = (df$n1 + df$n2 + df$n3 + df$n4 + df$n5 + df$n6 + df$n7 + df$n8 + df$n9 + df$n10)[1] / total_cases * 100
    )
  }

  percentages1 <- calculate_percentages(df1, total_cases1)

  # Prepare data for plotting
  plot_data <- tibble(
    Hits = factor(c("Top 1", "Top 3", "Top 10"), levels = c("Top 1", "Top 3", "Top 10")),
    Percentage = c(percentages1$Top_1, percentages1$Top_3, percentages1$Top_10),
    Dataset = rep("Phenopacket", 3)
  )

  mrr_plot_data <- tibble(
    Metric = "MRR",
    Value = mrr_value
  )

  # Create the percentage plot
  p1 <- ggplot(plot_data, aes(x = Hits, y = Percentage, fill = Dataset)) +
    geom_bar(stat = "identity", position = position_dodge()) +
    scale_fill_jama() +  # Apply JAMA color theme
    labs(x = "", y = "Percent of cases", title = "") +
    ylim(0, 40) +  # Adjust this as needed
    theme_minimal() +
    theme(
      legend.position = "none",  # Remove the legend
      axis.text = element_text(size = 18),  # Increased font size
      axis.title = element_text(size = 20),  # Increased font size
      axis.title.y = element_text(margin = margin(t = 0, r = 20, b = 0, l = 0))  # Add margin to y-axis label
    )

  # Create the MRR plot
  p2 <- ggplot(mrr_plot_data, aes(x = Metric, y = Value, fill = Metric)) +
    geom_bar(stat = "identity") +
    scale_fill_jama() +  # Apply JAMA color theme
    labs(x = "", y = "MRR Value", title = "") +
    ylim(0, 1) +  # MRR values are typically between 0 and 1
    theme_minimal() +
    theme(
      legend.position = "none",  # Remove the legend
      axis.text = element_text(size = 18),  # Increased font size
      axis.title = element_text(size = 20),  # Increased font size
      axis.title.y = element_text(margin = margin(t = 0, r = 20, b = 0, l = 0))  # Add margin to y-axis label
    )

  # Combine the two plots
  combined_plot <- grid.arrange(p1, p2, ncol = 2)

  # Save the combined plot to the specified file
  ggsave(output_file, plot = combined_plot, width = 12, height = 6, device = "png")
}

# Main execution
args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 3) {
  stop("Usage: Rscript plot_hits_at_n.R <phenopacket_file> <mrr_file> <output_file>")
}

phenopacket_file <- args[1]
mrr_file <- args[2]
output_file <- args[3]

make_combined_hits_at_n_plot(phenopacket_file, mrr_file, output_file)
