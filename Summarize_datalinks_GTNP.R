setwd("Q:\\CommonData\\PermafrostData\\GTNP\\data")

## for GTNP, how many daily, annual etc.?
ranks = c("Hourly","Daily","Monthly","Quarterly","Annually","Unknown")

#Read in data
DLS <-  read.csv("Q:\\CommonData\\PermafrostData\\GTNP\\data\\DataLinks_Summay.csv",stringsAsFactors = F)

# adjust time 
DLS$Start <- as.Date(DLS$Start,format="%d. %b %Y")
DLS$End <- as.Date(DLS$End,format="%d. %b %Y")
DLS$Fullyears <- floor(as.numeric((DLS$End - DLS$Start)/365))

#only take ground temp. data
DLS <- DLS[DLS$Variable == 'Ground Temperature',]

#Adjust frequency naming
DLS$Frequency[grep("[hH]our",DLS$Frequency)] <- "Hourly"
DLS$Frequency[grep("Not Planned",DLS$Frequency)] <- "Unknown"
DLS$Frequency[grep("Continual",DLS$Frequency)] <- "Daily"
DLS$Frequency[grep("As Needed",DLS$Frequency)] <- "Unknown"

# Make ordindal frequency data
F.rank <- DLS$Frequency
F.rank[grep("Hourly",F.rank)] <- 1
F.rank[grep("Daily",F.rank)] <- 2
F.rank[grep("Monthly",F.rank)] <- 3
F.rank[grep("Quarterly",F.rank)] <- 4
F.rank[grep("Annually",F.rank)] <- 5
F.rank[grep("Unknown",F.rank)] <- 6
F.rank <- as.numeric(F.rank)

# What is the best frequency for each site
best <- as.matrix(by(F.rank,DLS$filename,min))

plotdat <-as.matrix(by(DLS$Frequency,as.factor(DLS$Frequency),length))
plotsort <- c(3,2,4,5,1,6)
plotdat<- plotdat[plotsort]
names(plotdat) <- ranks

barplot(height=as.numeric(plotdat),names.arg = ranks,ylim=c(0,150))

counts <- as.matrix(by(best,as.factor(best),length))

hist(best,breaks=c(0,1,2,3,4,5,6))
length(best)  # 312 sites with data
length(best[best==1]) # 39 sites with sub-daily
length(best[best==2]) # 
