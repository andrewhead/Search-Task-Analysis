# This is the "neither/both" rating when we cast the comparison ratings
# to an integer in R.  We consider the "polarity" of a rating to be
# its distance from this middle rating.
MIDDLE_RATING = 3

library('ARTool')  # required for aligned rank transform

package_preferences <- read.csv("/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.package_preference-2016-07-14_17:02:02.csv")
community_preferences <- read.csv("/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.package_community_quality-2016-07-14_13:32:27.csv")
documentation_preferences <-read.csv("/Users/andrew/Adventures/design/studies/01-lab/software/Search-Task-Analysis/data/dump.package_documentation_quality-2016-07-14_13:32:21.csv") 

clean_data <- function(data_frame) {
  
  # Filter out the pilot participants
  data_frame <- data_frame[data_frame$User > 4,]
  
  # Convert all "None" values to a middle rating  
  data_frame$Comparison.Rating <- as.character(data_frame$Comparison.Rating)
  data_frame$Rating <- ifelse(
    data_frame$Comparison.Rating == "None",
    '2',  # this is the middle value of the data
    data_frame$Comparison.Rating
  )
  data_frame$Rating <- as.integer(data_frame$Rating)
  
  # Reshape to a wide table so we can compute the difference in preference
  data_frame <- reshape(
    data_frame,
    idvar = c("User"),
    timevar = "Stage",
    direction = "wide",
    drop = c("Package.1", "Package.2", "Comparison.Rating")
  )
  
  # Compute the absolute change in the rating value
  data_frame$Change = abs(data_frame$Rating.after - data_frame$Rating.before)
  
  return(data_frame)
  
}

# Clean all data frames of spurious data, normalize out-of-bounds values
package_preferences <- clean_data(package_preferences)
community_preferences <- clean_data(community_preferences)
documentation_preferences <- clean_data(documentation_preferences)

plot_change <- function(data_frame, title) {
  hist(
    data_frame$Change,
    c(-.5, .5, 1.5, 2.5, 3.5, 4.5),
    main = paste("Change:", title)
  )
}

print("Package preference change")
print(summary(package_preferences$Change))
print(sd(package_preferences$Change))
plot_change(package_preferences, "Package Preferences")

print("Community preference change")
print(summary(community_preferences$Change))
print(sd(community_preferences$Change))
plot_change(community_preferences, "Community Preferences")

print("Documentation preference change")
print(summary(documentation_preferences$Change))
print(sd(documentation_preferences$Change))
plot_change(documentation_preferences, "Documentation Preferences")
