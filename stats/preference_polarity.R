# This is the "neither/both" rating when we cast the comparison ratings
# to an integer in R.  We consider the "polarity" of a rating to be
# its distance from this middle rating.
MIDDLE_RATING = 3

library('ARTool')  # required for aligned rank transform

preferences <- read.csv("/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.package_comparisons-2016-07-14_17:43:49.csv")

# Filter out the pilot participants
filtered <- preferences[preferences$User > 4,]

# Remove all "Don't know" or "N/A" ratings
filtered <- filtered[grep("None", filtered$Comparison.Rating, invert = TRUE),]

# Convert factor columns to factors to let us make a model
filtered$Concern.Index.Factor <- factor(filtered$Concern.Index)
filtered$User.Factor <- factor(filtered$User)

# Compute polarity as distance from middle rating
filtered$Comparison.Rating.Integer <- as.integer(filtered$Comparison.Rating)
filtered$Polarity <- abs(filtered$Comparison.Rating.Integer - MIDDLE_RATING)

# Create a model with aligned rank transform
# Look for effect from concern
# We stopped looking for an effect from the package as we got a warning
# from the ARTool package, though it would be good to find out why this was.
# We also see a bunch of blank numbers from the ARTool when we print the summary.
# I don't know why this is, but it may be a bad sign.
model <- art(Polarity ~ Concern.Index.Factor + Error(User.Factor), data=filtered)
print(summary(model))

# Show results of running ANOVA on the model
print("Is there a significant difference in rating polarity by concer?")
print(anova(model))