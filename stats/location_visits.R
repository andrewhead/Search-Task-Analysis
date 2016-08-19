library('plyr')    # required for ddply
library('ARTool')  # required for aligned rank transform

# Let's show the results of all ANOVAs where the p-value
# of the result is less than .01
THRESHOLD_P = .01

location_visits <- read.csv("/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.location_visits-2016-07-14_11:39:13.csv", sep="|")

# Filter out the pilot participants
location_visits <- location_visits[location_visits$User > 4,]

# Convert factor columns to factors to let us make a model
location_visits$User.Factor = factor(location_visits$User)
location_visits$Concern.Index.Factor = factor(location_visits$Concern.Index)

# Aggregate the time spent by each user on each page type for each question
# We use ddply instead of 'aggregate' as it gives you the option to fill the rows
# that represent conditions that didn't appear with 0s
dwell_times <- ddply(
  location_visits,
  .(Page.Type, Concern.Index.Factor, User.Factor),
  summarize,
  Time = sum(Time.passed..s.),
  .drop = FALSE
)

page_types <- as.vector(unique(dwell_times$Page.Type))
for (page_type_index in 1:length(page_types)) {
  
  # Filter to only the measurements for this page type
  page_type <- page_types[page_type_index]
  page_dwell_times <- dwell_times[dwell_times$Page.Type == page_type,]

  # Create a model with aligned rank transform
  model <- art(
    Time ~ Concern.Index.Factor + Error(User.Factor),
    data = page_dwell_times
  )
  anova_results <- anova(model)
  if (anova_results$`Pr(>F)` <= THRESHOLD_P) {
    
    cat("=============================\n")
    cat("Signs of significant variance\n")
    cat("Page type: ", page_type, "\n")
    cat("=============================\n")
    cat("F(", anova_results$Df, ",", anova_results$Df.res, ") =" ,
        anova_results$`F value`, ". p =", anova_results$`Pr(>F)`, "\n")
    
    page_type_mean_time <- mean(page_dwell_times$Time)
    concern_mean_times <- ddply(
      page_dwell_times,
      .(Concern.Index.Factor),
      summarize,
      Time = mean(Time),
      .drop = FALSE
    )
    cat("Mean time on this type of page:", page_type_mean_time, "\n")
    cat("Mean time by concern:\n")
    print(concern_mean_times)
    
    # cat("Check the summary for valid ART application:\n")
    # print(summary(model))
    # cat("\n")
  }
}