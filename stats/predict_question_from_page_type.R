library('plyr')    # required for ddply
library('ARTool')  # required for aligned rank transform

location_visits <- read.csv("/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.location_visits-2016-07-14_11:39:13.csv", sep="|")

# Filter out the pilot participants
location_visits <- location_visits[location_visits$User > 4,]

# Convert factor columns to factors to let us make a model
location_visits$User.Factor <- factor(location_visits$User)
location_visits$Concern.Index.Factor <- factor(location_visits$Concern.Index)

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

# Make table wide, with one measurement for each page type
# so we can predict question from time spent on page types
dwell_times_wide <- reshape(
   dwell_times,
   idvar = c("User.Factor", "Concern.Index.Factor"),
   timevar = "Page.Type",
   direction = "wide"
)

for (concern_index in 0:5) {
  
  # Start with fresh data
  model_data <- dwell_times_wide
  
  # Move the question under consideration into a binary variable
  # so we can do logistic regression.
  model_data$Is.Concern <- ifelse(model_data$Concern.Index.Factor == as.character(concern_index), 1, 0)
  model <- lm(
    Is.Concern ~ . - User.Factor - Concern.Index.Factor,
    data = model_data
  )
  # Skipped model of linear regression.  Too biased from little data?
  # model <- glm(Is.Concern.0 ~ . - User.Factor, data = model_data, family = "binomial")
  # print("")
  # print("")
  # print("====================")
  # print(paste("Summary of model for concern index", concern_index))
  # print(paste("Significant page types for concern:", concern_index))
  # print("====================")
  
  # REUSE: this snippet comes from user tcash21 on Stack Overflow
  # The snippet extracts the estimates and signficiance of coefficients
  # that have a p-value of less than .05
  # Source: http://stackoverflow.com/questions/16070926
  write.table(
    data.frame(summary(model)$coef[summary(model)$coef[,4] <= .05, c(1,4)]),
    sep = '\t',
    file = ""
  )
  # print(summary(model))
  
}

# Create a model with aligned rank transform
# Look for effect from page type and concern index
# Also look for an interaction between page type and concern index
# model <- art(Time ~ Page.Type * Concern.Index.Factor + Error(User.Factor), data=dwell_times)
# summary(model)

# Show results of running ANOVA on the model
# print("Is there a significant difference in page time by page type and concern index?")
# print(anova(model))