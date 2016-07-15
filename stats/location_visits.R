library('plyr')    # required for ddply
library('ARTool')  # required for aligned rank transform

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

# Create a model with aligned rank transform
# Look for effect from page type and concern index
# Also look for an interaction between page type and concern index
model <- art(Time ~ Page.Type * Concern.Index.Factor + Error(User.Factor), data=dwell_times)
summary(model)

# Show results of running ANOVA on the model
print("Is there a significant difference in page time by page type and concern index?")
print(anova(model))