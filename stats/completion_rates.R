library('lme4')  # for glmer model fitting

completion_rates <- read.csv("/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.completions-2016-07-14_18:00.csv")

# Turn success into a binary variable
completion_rates$Success <- ifelse(completion_rates$Finished.Early == "Y", 1, 0)

# Convert concern index into factor so we can split it
completion_rates$Concern <- as.factor(completion_rates$Concern.Index)

# Convert user into a factor so it's considered categorical
completion_rates$User.Factor <- as.factor(completion_rates$User)

# Convert concern rank into a binary variable for each level
# Source: stackoverflow.com/questions/5048638/automatically-expanding-an-r-factor-into-a-collection-of-1-0-indicator-variables
concern_predictors <- model.matrix(
  ~ Concern - 1,
  data = completion_rates
)

# Join concern predictors into the original data frame
completion_rates <- cbind(completion_rates, concern_predictors)

# Fit a generalized linear model, using concerns as a preditor
# and each participant as a random effect.
# This piece of code has been adapted from a Cross Validated post:
# http://stats.stackexchange.com/questions/30686/what-test-is-appropriate-for-binary-outcome-with-repeated-measures-and-binary-o
# I need to return to this with someone who knows R and statistics to
# verify that this was appropriate
model <- glmer(
  Success ~ Concern + (1|User.Factor),
  data = completion_rates,
  family = "binomial"
)

# Note: with one of the versions of the data I was seing that
# columns and coefficients were getting dropped because the model
# matrix was "rank deficient".  I need to look into this some more.
# I also don't see any indicators of statistical significance.
print(summary(model))