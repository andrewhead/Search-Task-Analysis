library('ARTool')  # required for aligned rank transform

confidence_ratings <- read.csv(
  "/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.confidence_ratings-2016-07-14_13:32:03.csv",
  as.is = c("Confidence")
)

# Remove pilot study users
filtered <- confidence_ratings[confidence_ratings$User > 4,]

# Remove all "Don't know" or "N/A" confidences
filtered <- confidence_ratings[grep("None", confidence_ratings$Confidence, invert = TRUE),]

# Make factor columns into factors, case confidence to integer
filtered$Confidence = as.integer(filtered$Confidence)
filtered$User.Factor = factor(filtered$User)
filtered$Concern.Index.Factor = factor(filtered$Concern.Index)
filtered$Question.Index.Factor = factor(filtered$Question.Index)

# Measure effect of concern on confidence
m <- art(Confidence ~ Concern.Index.Factor + Error(User.Factor), data=filtered)
print(summary(m))
print("Effect of Concern.Index.Factor")
print(anova(m))

# Measure effect of question on confidence
m <- art(Confidence ~ Question.Index.Factor + Error(User.Factor), data=filtered)
print(summary(m))
print("Effect of Question.Index.Factor")
print(anova(m))

# Describe the confidence levels
print("Statistical summary of confidence")
print(summary(filtered$Confidence))