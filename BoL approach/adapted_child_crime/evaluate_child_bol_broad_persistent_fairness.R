options(stringsAsFactors = FALSE)

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_path <- if (length(file_arg)) sub("^--file=", "", file_arg[[1]]) else "bolt_nlsy79_starter_v0-2/evaluate_child_bol_broad_persistent_fairness.R"
repo <- normalizePath(dirname(script_path))
project_repo <- normalizePath(file.path(repo, ".."))

out_dir <- file.path(repo, "data", "processed_child_crime_broad_persistent")
data_path <- file.path(
  project_repo,
  "output/share_with_team/nlsy79_child_youngadult_combined_bundle/nlsy79_child_youngadult_selected_crime_features.csv"
)
pred_path <- file.path(out_dir, "child_crime_broad_persistent_llm_predictions_120.csv")
threshold_path <- file.path(out_dir, "child_crime_broad_persistent_llm_threshold_eval_120.csv")
out_metrics <- file.path(out_dir, "child_crime_broad_persistent_fairness_metrics_120.csv")
out_gaps <- file.path(out_dir, "child_crime_broad_persistent_fairness_gaps_120.csv")

race_labels <- c(`1` = "Hispanic", `2` = "Black", `3` = "Non-Black/non-Hispanic")
sex_labels <- c(`1` = "Male", `2` = "Female")

auc_rank <- function(y, p) {
  if (length(unique(y)) < 2) return(NA_real_)
  n_pos <- sum(y == 1)
  n_neg <- sum(y == 0)
  ranks <- rank(p, ties.method = "average")
  (sum(ranks[y == 1]) - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
}

metrics <- function(df, threshold) {
  y <- as.integer(df$y_true)
  p <- as.numeric(df$probability)
  pred <- as.integer(p >= threshold)
  tp <- sum(pred == 1 & y == 1)
  tn <- sum(pred == 0 & y == 0)
  fp <- sum(pred == 1 & y == 0)
  fn <- sum(pred == 0 & y == 1)
  data.frame(
    n = length(y),
    base_rate = mean(y == 1),
    predicted_positive_rate = mean(pred == 1),
    accuracy = mean(pred == y),
    auc = auc_rank(y, p),
    tpr = ifelse(tp + fn > 0, tp / (tp + fn), NA),
    fpr = ifelse(fp + tn > 0, fp / (fp + tn), NA),
    fnr = ifelse(fn + tp > 0, fn / (fn + tp), NA),
    ppv = ifelse(tp + fp > 0, tp / (tp + fp), NA),
    npv = ifelse(tn + fn > 0, tn / (tn + fn), NA),
    tp = tp, tn = tn, fp = fp, fn = fn
  )
}

make_metric_rows <- function(preds, threshold, group_col, group_label) {
  rows <- lapply(sort(unique(preds[[group_col]])), function(g) {
    sub <- preds[preds[[group_col]] == g & !is.na(preds[[group_col]]), ]
    cbind(
      data.frame(model = "BoL LLM broad persistent", threshold = threshold, attribute = group_label, subgroup = as.character(g)),
      metrics(sub, threshold)
    )
  })
  do.call(rbind, rows)
}

make_gaps <- function(metric_rows) {
  metric_names <- c("base_rate", "predicted_positive_rate", "accuracy", "auc", "tpr", "fpr", "fnr", "ppv", "npv")
  out <- do.call(rbind, lapply(split(metric_rows, metric_rows$attribute), function(d) {
    data.frame(
      model = d$model[1],
      threshold = d$threshold[1],
      attribute = d$attribute[1],
      metric = metric_names,
      min_value = sapply(metric_names, function(m) min(d[[m]], na.rm = TRUE)),
      max_value = sapply(metric_names, function(m) max(d[[m]], na.rm = TRUE)),
      gap = sapply(metric_names, function(m) max(d[[m]], na.rm = TRUE) - min(d[[m]], na.rm = TRUE))
    )
  }))
  rownames(out) <- NULL
  out
}

thresholds <- read.csv(threshold_path)
threshold <- thresholds$threshold[order(-thresholds$accuracy, -thresholds$sensitivity_tpr)][1]

preds <- read.csv(pred_path)
child <- read.csv(data_path, check.names = FALSE)[, c("C0000100", "C0005300", "C0005400")]
child$race <- race_labels[as.character(child$C0005300)]
child$sex <- sex_labels[as.character(child$C0005400)]
preds <- merge(preds, child[, c("C0000100", "race", "sex")], by = "C0000100")

metric_rows <- rbind(
  make_metric_rows(preds, threshold, "sex", "Sex"),
  make_metric_rows(preds, threshold, "race", "Race")
)
gap_rows <- make_gaps(metric_rows)

write.csv(metric_rows, out_metrics, row.names = FALSE)
write.csv(gap_rows, out_gaps, row.names = FALSE)

cat("Threshold:", threshold, "\n")
cat("Metrics written to", out_metrics, "\n")
cat("Gaps written to", out_gaps, "\n\n")
print(metric_rows[, c("model", "attribute", "subgroup", "n", "base_rate", "predicted_positive_rate", "accuracy", "auc", "tpr", "fpr", "fnr", "ppv")])
cat("\nGaps:\n")
print(gap_rows[gap_rows$metric %in% c("predicted_positive_rate", "accuracy", "auc", "tpr", "fpr", "fnr", "ppv"), ])
