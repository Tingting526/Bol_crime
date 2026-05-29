options(stringsAsFactors = FALSE)

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_path <- if (length(file_arg)) sub("^--file=", "", file_arg[[1]]) else "bolt_nlsy79_starter_v0-2/evaluate_child_bol_fairness.R"
repo <- normalizePath(dirname(script_path))
project_repo <- normalizePath(file.path(repo, ".."))
out_dir <- file.path(repo, "data", "processed_child_crime")

data_path <- file.path(
  project_repo,
  "output/share_with_team/nlsy79_child_youngadult_combined_bundle/nlsy79_child_youngadult_selected_crime_features.csv"
)
llm_path <- file.path(out_dir, "child_crime_llm_predictions.csv")
logit_path <- file.path(out_dir, "child_crime_logit_same_features_predictions.csv")
llm_threshold_path <- file.path(out_dir, "child_crime_llm_threshold_eval.csv")
logit_threshold_path <- file.path(out_dir, "child_crime_logit_threshold_eval.csv")

out_metrics <- file.path(out_dir, "child_crime_fairness_metrics_120.csv")
out_gaps <- file.path(out_dir, "child_crime_fairness_gaps_120.csv")

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
  p <- as.numeric(df$score)
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

best_threshold <- function(path) {
  d <- read.csv(path)
  d <- d[order(-d$accuracy, -d$sensitivity_tpr), ]
  d$threshold[1]
}

make_metric_rows <- function(preds, model, threshold, group_col, group_label) {
  split_vals <- sort(unique(preds[[group_col]]))
  rows <- lapply(split_vals, function(g) {
    sub <- preds[preds[[group_col]] == g & !is.na(preds[[group_col]]), ]
    if (nrow(sub) == 0) return(NULL)
    cbind(
      data.frame(model = model, threshold = threshold, attribute = group_label, subgroup = as.character(g)),
      metrics(sub, threshold)
    )
  })
  do.call(rbind, rows)
}

make_gaps <- function(metric_rows) {
  metric_names <- c("base_rate", "predicted_positive_rate", "accuracy", "auc", "tpr", "fpr", "fnr", "ppv", "npv")
  out <- do.call(rbind, lapply(split(metric_rows, list(metric_rows$model, metric_rows$attribute), drop = TRUE), function(d) {
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

child <- read.csv(data_path, check.names = FALSE)
demo <- child[, c("C0000100", "C0005300", "C0005400")]
demo$race <- race_labels[as.character(demo$C0005300)]
demo$sex <- sex_labels[as.character(demo$C0005400)]

llm <- read.csv(llm_path)
llm <- merge(llm[, c("C0000100", "y_true", "probability")], demo, by = "C0000100")
names(llm)[names(llm) == "probability"] <- "score"

logit <- read.csv(logit_path)
logit <- merge(logit[, c("C0000100", "y_true", "logit_probability")], demo, by = "C0000100")
names(logit)[names(logit) == "logit_probability"] <- "score"

llm_threshold <- 0.25
logit_threshold <- best_threshold(logit_threshold_path)

metric_rows <- rbind(
  make_metric_rows(llm, "BoL LLM", llm_threshold, "sex", "Sex"),
  make_metric_rows(llm, "BoL LLM", llm_threshold, "race", "Race"),
  make_metric_rows(logit, "Logistic regression", logit_threshold, "sex", "Sex"),
  make_metric_rows(logit, "Logistic regression", logit_threshold, "race", "Race")
)

gap_rows <- make_gaps(metric_rows)

write.csv(metric_rows, out_metrics, row.names = FALSE)
write.csv(gap_rows, out_gaps, row.names = FALSE)

cat("Fairness metrics written to", out_metrics, "\n")
cat("Fairness gaps written to", out_gaps, "\n\n")
cat("Key subgroup metrics:\n")
print(metric_rows[, c("model", "attribute", "subgroup", "n", "base_rate", "predicted_positive_rate", "accuracy", "auc", "tpr", "fpr", "fnr", "ppv")])
cat("\nKey gaps:\n")
print(gap_rows[gap_rows$metric %in% c("predicted_positive_rate", "accuracy", "auc", "tpr", "fpr", "fnr", "ppv"), ])
