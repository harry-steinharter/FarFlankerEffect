#### Set Up ####
library(dplyr)
library(magrittr)
library(ggplot2)
library(tibble)
library(lme4)
library(ggpubr)
library(afex)
library(merTools)
library(emmeans)


MC <- function(L_max, L_min = 112.6482, nDigits=4){
  # Function to find michelson contrast using L_min as the background luminance in PsychoPy units
  michelson_contrast <- (L_max-L_min) / (L_max+L_min)
  michelson_contrast %<>% round(nDigits)
  return(michelson_contrast)
}

toCandela <- function(x, nDigits = 10){
  CandelaPerMeterSquared <- (x * 112.417) + 112.6482
  CandelaPerMeterSquared %<>% round(nDigits)
  return(CandelaPerMeterSquared)
}

setwd('/Users/harrysteinharter/Documents/MSc/Timo Internship/FarFlankerExp/Analysis')
file_list <- list.files(path = "../Outputs/", pattern = "\\.csv$", full.names = TRUE)
all_data <- do.call(rbind, lapply(file_list, read.csv))

dfReal <- all_data %>% subset(!endsWith(Condition,'_null'))

#### Mutate data frame ####
df <- dfReal %>% group_by(Participant_Number,Condition,Target_Contrast) %>% 
  summarise(
    accuracy = mean(Correct_Response, na.rm = TRUE),
    weights = n(),
    .groups = "drop")
df$Condition %<>% as.factor()
df$TC_factor <- cut_number(df$Target_Contrast,3,c('Low','Medium','High'))
df$TC_michelson <- df$Target_Contrast %>% toCandela() %>% MC()
df$TC_michelson_c <- scale(df$TC_michelson, scale = FALSE) %>% c()

#### Summary data frames ####
dfCondSummary <- df %>% group_by(Participant_Number,Condition,TC_factor) %>% 
  summarise(mean = weighted.mean(accuracy,weights), .groups = 'drop')
dfGrandMean <- df %>% group_by(Participant_Number,Condition) %>% 
  summarise(grandMean = weighted.mean(accuracy, weights), .groups = 'drop')

#### GLM ####
model_glmer <- glmer(data = df,
                     formula = "accuracy ~ Condition * TC_michelson_c + (1 | Participant_Number)",
                     family = binomial(link = 'logit'),
                     weights = weights,
                     contrasts = list(Condition = levels(df$Condition) %>% contr.treatment()),
                     control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e6),
                                            check.conv.grad = .makeCC("warning", tol = 0.005, relTol = NULL))
                     )
df$probability <- predict(model_glmer, type='response', re.form = NA) # re.form=NA is fixed effects only. =NULL is both
#### LRT ####
model_LRT <- mixed(data = df,
                   formula = "accuracy ~ Condition * TC_michelson_c + (1 | Participant_Number)",
                   family = binomial(link = 'logit'),
                   weights = weights,
                   method = 'LRT',
                   type = 3,
                   control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e6),
                                          check.conv.grad = .makeCC("warning", tol = 0.005, relTol = NULL))
                   )

#### ANOVA ####
model_lm <- lmer(data = df,
                       formula = "accuracy ~ Condition * TC_factor + (1 | Participant_Number)",
                       weights = weights,
                       contrasts = list(Condition = levels(df$Condition) %>% contr.treatment()))

model_anova <- car::Anova(model_lm,type = 3)
em_pairs <- emmeans(model_lm, specs = ~ Condition|TC_factor) %>% pairs()

#### T-Test ####
model_t <- lm(data = df,
              formula = 'accuracy ~ Condition',
              weights = weights,
              contrasts = list(Condition = levels(df$Condition) %>% contr.treatment()))

#### Line Plot ####
palette <- c('Together' = 'firebrick', 'Seperate' = 'dodgerblue')
factorCuts <- subset(df, TC_factor == 'Medium', select = TC_michelson) %>% range()
ggplot(data = df,
       mapping = aes(x = TC_michelson, y = probability, colour = Condition)) +
  geom_line(linewidth = 1) +
  scale_x_continuous(transform = 'log10', labels = scales::label_number(accuracy = .0001)) +
  scale_color_manual(values = palette, name = 'Condition') +
  xlab("Target Contrast") +
  ylab("Detection Probability") +
  theme_pubr() +
  theme(
    legend.title = element_text(hjust = .5, vjust = .5),
    text = element_text(size=16,family='times'),
    legend.position = 'top') + 
  geom_vline(xintercept = factorCuts, linetype = 'dotted')

#### ANOVA Plot ####
ggplot(data = dfCondSummary,
       mapping = aes(x = TC_factor, y = mean, color = Condition)) +
  stat_summary(
    geom = 'point',
    position = position_dodge(width = .9),
    fun = 'mean',
    size = I(5)) + 
  stat_summary(
    geom = 'errorbar',
    fun.data = mean_cl_normal,
    position = position_dodge(width = 0.9), 
    width = 0.2,
    linetype = I('solid')) +
  scale_color_manual(values = palette, name = 'Condition') +
  xlab("Target Contrast") +
  ylab("Mean Response Rate") +
  theme_pubr() +
  theme(
    legend.title = element_text(hjust = .5, vjust = .5),
    text = element_text(size=16,family='times'),
    legend.position = 'top') 

#### T-Test Plot ####
ggplot(data = dfGrandMean,
       mapping = aes(x = Condition, y = grandMean, color = Condition)) +
  stat_summary(
    geom = 'point',
    position = position_dodge(width = .9),
    fun = 'mean',
    size = I(5),
    show.legend = FALSE) + 
  stat_summary(
    geom = 'errorbar',
    fun.data = mean_cl_normal,
    position = position_dodge(width = 0.9), 
    width = 0.2,
    linetype = I('solid'),
    show.legend = FALSE) +
  scale_color_manual(values = palette, name = 'Condition') +
  xlab("Condition") +
  ylab("Mean Response Rate") +
  theme_pubr() +
  theme(text = element_text(size=16,family='times'))
        