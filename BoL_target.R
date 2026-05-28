library(dplyr)
library(ggplot2)

# charlotte's files:

# codebook <- read.csv("~/Downloads/nlsy79_child_youngadult_codebook_unique.csv")

# merged <- read.csv("~/Downloads/nlsy79_child_youngadult_combined.csv")

# downloaded the selected crime variables form the nslinfo page:
# (variable explanations in the google doc)

target <- read.table("~/Downloads/targetvariables(1)/targetvariables.dat")

all_crime_vars <- c(
  "CPUBID_XRND",
  "MPUBID_XRND", 
  "CRACE_XRND",
  "CSEX_XRND",
  "CYRB_XRND",
  "YASR-67C~000012",
  "YASR-65A~000012",
  "YASR-65A~000007",
  "YASR-67C~000007",
  "YASR-67C~000005",
  "YASR-65A~000005",
  "YASR-65A~000003",
  "YASR-67C~000003",
  "YASR-65A~000002",
  "YASR-65A~000008",
  #"YASR-9A",
  #"YASR-9B",
  "YASR-9C",
  #"YASR-9D",
 # "YASR-9E",
  "YASR-65A~000009",
  "YASR-65A~000010",
  "YASR-65A~000006",
  "YASR-65A~000001",
  "YASR-65A~000004",
  "YASR-65A~000011",
  # "YASR-9F",
  # "YASR-9G",
  # "YASR-9H",
  # "YASR-9I",
  # "YASR-9J",
  # "YASR-9K",
  # "YASR-9L",
  # "YASR-9M",
  # "YASR-9N",
  "YASR-63_",
  "YASR-67_"
)

 repeated_crime <- c(#"YASR-9A", 
#                     "YASR-9F",
#                     "YASR-9G",
#                     "YASR-9B",
                    "YASR-9C",
                    # "YASR-9H",
                    # "YASR-9I",
                    # "YASR-9J",
                    # "YASR-9D",
                    # "YASR-9K",
                    # "YASR-9L",
                    # "YASR-9E",
                    # "YASR-9M",
                    # "YASR-9N", 
                    "YASR-63_", 
                    "YASR-67_")

demographic <- c("CPUBID_XRND",
                 "MPUBID_XRND",
                 "CRACE_XRND",
                 "CSEX_XRND",
                 "CYRB_XRND")

severity_var <- setdiff(all_crime_vars, c(repeated_crime, demographic))

# important:
# source("targetvariables.R") # source R file that cleans the downloaded data

selected_target <- categories %>% select(starts_with(c(all_crime_vars)))

# summary(selected_target)

# Replace YES/NO text values with 1/0 

selected_target[] <- lapply(selected_target, function(col) {
  
  # Convert to character temporarily
  col_char <- as.character(col)
  
  # Replace YES variants with 1
  col_char[col_char %in% c("1: YES", "YES", "Yes", "1: Yes", "0: Yes")] <- "1"
  
  # Replace NO variants with 0
  col_char[col_char %in% c("2: NO", "NO", "No", "0: NO", "0: No")] <- "0"
  
  # Convert back to numeric if possible
  suppressWarnings({
    if (all(na.omit(col_char) %in% c("0", "1"))) {
      return(as.numeric(col_char))
    }
  })
  
  return(col_char)
})


# classifying the variables for easier access

mild <- c("YASR-67C~000012",
          "YASR-65A~000012",
          "YASR-65A~000007",
          "YASR-67C~000007",
          "YASR-67C~000005",
          "YASR-65A~000005",
          "YASR-65A~000003",
          "YASR-67C~000003")

intermediate <- c(
  "YASR-65A~000002",
  "YASR-65A~000008",
  "YASR-9A",
  "YASR-9B",
  "YASR-9C",
  "YASR-9D",
  "YASR-9E",
  "YASR-65A~000009",
  "YASR-65A~000010",
  "YASR-65A~000006"
)

major <- c(
  "YASR-65A~000001",
  "YASR-65A~000004",
  "YASR-65A~000011"
)


# if R has committed any of the major crimes in any year -> major
# most severe is intermediate crime -> intermediate
# most severe is minor crime -> minor

selected_target <- selected_target %>%
  mutate(
    severity = case_when(
      
      if_any(matches(
        "YASR-65A~000001|YASR-65A~000004|YASR-65A~000011"
      ), ~ . == 1) ~ "major",
      
      if_any(matches(
        "YASR-65A~000002|YASR-65A~000008|YASR-9A|YASR-9B|YASR-9C|YASR-9D|YASR-9E|YASR-65A~000009|YASR-65A~000010|YASR-65A~000006"
      ), ~ . == 1) ~ "intermediate",
      
      if_any(matches(
        "YASR-67C~000012|YASR-65A~000012|YASR-65A~000007|YASR-67C~000007|YASR-67C~000005|YASR-65A~000005|YASR-65A~000003|YASR-67C~000003"
      ), ~ . == 1) ~ "mild",
      
      TRUE ~ NA_character_
    )
  )

# plotting the target variables 

ggplot(selected_target) +
  geom_bar(aes(x = severity))

selected_target <- selected_target %>%
  mutate(
    total_repeated_crime = rowSums(
      across(starts_with("YASR-63"), ~ as.numeric(.x)),
      na.rm = TRUE
    )
  )

selected_target <- selected_target %>%
  mutate(
    total_probation = rowSums(
      across(starts_with("YASR-67_"), ~ as.numeric(.x)),
      na.rm = TRUE
    )
  )


ggplot(selected_target) +
  geom_histogram(aes(x = log(total_probation)))


ggplot(selected_target) +
  geom_histogram(aes(x = log(total_repeated_crime)))

