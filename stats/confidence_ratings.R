confidence_ratings$User.Factor = factor(confidence_ratings$User)
confidence_ratings$Concern.Index.Factor = factor(confidence_ratings$Concern.Index)
confidence_ratings$Question.Index.Factor = factor(confidence_ratings$Question.Index)

filtered <- confidence_ratings[confidence_ratings$User > 4,]
m <- art(Confidence ~ Concern.Index.Factor + Error(User.Factor), data=filtered)
summary(m)
print("Effect of Concern.Index.Factor")
print(anova(m))

filtered <- confidence_ratings[confidence_ratings$User > 4,]
m <- art(Confidence ~ Question.Index.Factor + Error(User.Factor), data=filtered)
summary(m)
print("Effect of Question.Index.Factor")
print(anova(m))

print("Statistical summary of confidence")
print(summary(filtered$Confidence))