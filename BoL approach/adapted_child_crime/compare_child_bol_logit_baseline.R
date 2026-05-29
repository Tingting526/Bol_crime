options(stringsAsFactors = FALSE)

`%||%` <- function(x, y) if (is.null(x)) y else x

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_path <- if (length(file_arg)) sub("^--file=", "", file_arg[[1]]) else "bolt_nlsy79_starter_v0-2/compare_child_bol_logit_baseline.R"
repo <- normalizePath(dirname(script_path))
project_repo <- normalizePath(file.path(repo, ".."))
out_dir <- file.path(repo, "data", "processed_child_crime")

data_path <- file.path(
  project_repo,
  "output/share_with_team/nlsy79_child_youngadult_combined_bundle/nlsy79_child_youngadult_selected_crime_features.csv"
)
targets_path <- file.path(
  project_repo,
  "output/child_youngadult/constructed_justice_contact_baseline/constructed_justice_contact_targets.csv"
)
feature_index_path <- file.path(out_dir, "child_crime_bol_feature_index.csv")
sample_ids_path <- file.path(out_dir, "child_crime_sample_ids.csv")
llm_predictions_path <- file.path(out_dir, "child_crime_llm_predictions.csv")

comparison_path <- file.path(out_dir, "child_crime_llm_vs_logit_comparison.csv")
logit_predictions_path <- file.path(out_dir, "child_crime_logit_same_features_predictions.csv")

target <- "justice_contact_repeated"
missing_codes <- c(-1, -2, -3, -4, -5, -7)

read_csv <- function(path) read.csv(path, check.names = FALSE)

clean_missing <- function(x) {
  x <- suppressWarnings(as.numeric(x))
  x[x %in% missing_codes] <- NA
  x
}

auc_rank <- function(y, p) {
  if (length(unique(y)) < 2) return(NA_real_)
  n_pos <- sum(y == 1)
  n_neg <- sum(y == 0)
  ranks <- rank(p, ties.method = "average")
  (sum(ranks[y == 1]) - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
}

metrics_at <- function(y, p, threshold) {
  pred <- as.integer(p >= threshold)
  tp <- sum(pred == 1 & y == 1)
  tn <- sum(pred == 0 & y == 0)
  fp <- sum(pred == 1 & y == 0)
  fn <- sum(pred == 0 & y == 1)
  data.frame(
    threshold = threshold,
    accuracy = mean(pred == y),
    auc = auc_rank(y, p),
    sensitivity_tpr = ifelse(tp + fn > 0, tp / (tp + fn), NA),
    specificity_tnr = ifelse(tn + fp > 0, tn / (tn + fp), NA),
    fpr = ifelse(fp + tn > 0, fp / (fp + tn), NA),
    fnr = ifelse(fn + tp > 0, fn / (fn + tp), NA),
    predicted_positive_rate = mean(pred == 1),
    tp = tp,
    tn = tn,
    fp = fp,
    fn = fn
  )
}

best_accuracy_threshold <- function(y, p) {
  grid <- sort(unique(c(seq(0.05, 0.95, by = 0.05), p)))
  acc <- sapply(grid, function(t) mean(as.integer(p >= t) == y))
  grid[which.max(acc)]
}

data <- read_csv(data_path)
targets <- read_csv(targets_path)
feature_index <- read_csv(feature_index_path)
sample_ids <- read_csv(sample_ids_path)$C0000100

feature_cols <- intersect(feature_index$csv_code, names(data))
model_df <- merge(
  data[, c("C0000100", feature_cols), drop = FALSE],
  targets[, c("C0000100", target), drop = FALSE],
  by = "C0000100"
)
model_df <- model_df[!is.na(model_df[[target]]), ]

for (col in feature_cols) {
  model_df[[col]] <- clean_missing(model_df[[col]])
}

categorical_cols <- intersect(c("C0005300", "C0005400"), feature_cols)
numeric_cols <- setdiff(feature_cols, categorical_cols)

for (col in numeric_cols) {
  med <- median(model_df[[col]], na.rm = TRUE)
  if (is.na(med)) med <- 0
  model_df[[col]][is.na(model_df[[col]])] <- med
}

for (col in categorical_cols) {
  tab <- sort(table(model_df[[col]]), decreasing = TRUE)
  fill <- as.numeric(names(tab)[1])
  model_df[[col]][is.na(model_df[[col]])] <- fill
  model_df[[col]] <- factor(model_df[[col]])
}

test <- model_df[model_df$C0000100 %in% sample_ids, ]
train <- model_df[!model_df$C0000100 %in% sample_ids, ]

formula <- as.formula(paste(target, "~", paste(feature_cols, collapse = " + ")))
fit <- glm(formula, data = train, family = binomial())

train_prob <- as.numeric(predict(fit, newdata = train, type = "response"))
test_prob <- as.numeric(predict(fit, newdata = test, type = "response"))
logit_threshold <- best_accuracy_threshold(as.integer(train[[target]]), train_prob)

logit_preds <- data.frame(
  C0000100 = test$C0000100,
  y_true = as.integer(test[[target]]),
  logit_probability = test_prob,
  logit_prediction_threshold_0_5 = as.integer(test_prob >= 0.5),
  logit_prediction_train_best_threshold = as.integer(test_prob >= logit_threshold)
)
write.csv(logit_preds, logit_predictions_path, row.names = FALSE)

rows <- list()
add_row <- function(model, threshold_name, m) {
  cbind(data.frame(model = model, threshold_name = threshold_name), m)
}

y_test <- as.integer(test[[target]])
rows[[length(rows) + 1]] <- add_row("tabular_logistic_regression", "0.50", metrics_at(y_test, test_prob, 0.5))
rows[[length(rows) + 1]] <- add_row("tabular_logistic_regression", "train_best_accuracy", metrics_at(y_test, test_prob, logit_threshold))

if (file.exists(llm_predictions_path)) {
  llm <- read_csv(llm_predictions_path)
  llm <- llm[!is.na(llm$y_true) & !is.na(llm$probability), ]
  y_llm <- as.integer(llm$y_true)
  p_llm <- as.numeric(llm$probability)
  rows[[length(rows) + 1]] <- add_row("book_of_life_llm", "0.50", metrics_at(y_llm, p_llm, 0.5))
  rows[[length(rows) + 1]] <- add_row("book_of_life_llm", "0.25", metrics_at(y_llm, p_llm, 0.25))
}

comparison <- do.call(rbind, rows)
write.csv(comparison, comparison_path, row.names = FALSE)

cat("Train N:", nrow(train), "| Test N:", nrow(test), "| Features:", length(feature_cols), "\n")
cat("Logistic train-best threshold:", round(logit_threshold, 3), "\n\n")
print(comparison)
cat("\nWrote comparison to", comparison_path, "\n")
cat("Wrote logistic predictions to", logit_predictions_path, "\n")
