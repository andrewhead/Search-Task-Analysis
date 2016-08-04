library('ARTool')  # required for aligned rank transform

concern_ranks <- read.csv("/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.concern_ranks-2016-07-14_13:31:42.csv")

# Remove pilot study users and null ratings
# Errata: I'm not sure if we impact our test by filtering out this null rating
filtered <- confidence_ratings[confidence_ratings$User > 4,]
filtered <- filtered[filtered$Concern != "None",]

# Cast user to a factor to use as a random effect
filtered$User.Factor = factor(filtered$User)

# Function to map from concern text to its index
concern_texts = c(
  "I will find good How-To documentation for all the tasks I want to do.",
  "Other developers will answer questions I ask as fast as I need them to.",
  "The documentation will be up-to-date with the code.",
  "The community will be welcoming when they respond to questions I ask.",
  "I can trust the developers of the package to make reliable, usable software.",
  "The package was designed for users with my technical knowledge and goals."  
)
label_concern <- function(concern_text) {
  match(concern_text, concern_texts) - 1
}
filtered$Concern.Index.Factor <- 
  as.factor(sapply(filtered$Concern, label_concern))

# Run the test!
# Currently I don't see any F-values of ANOVAs on aligned responses
# "not of interest" reported, so they aren't necessarily all 0.
# Though my guess is this is just related to only having one factor to test
m <- art(Rank ~ Concern.Index.Factor + Error(User.Factor), data=filtered)
print(summary(m))
print("Effect of Concern.Index.Factor")
print(anova(m))