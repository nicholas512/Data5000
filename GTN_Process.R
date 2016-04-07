library(lubridate)
library(stringr)
## Deal with scraped NorPERM data
options(stringsAsFactors=FALSE)

# Replace -999 and -888
setNA <- function(NA.val){
  function(x) {
    x[x == NA.val] <-NA
    return(x)
  }
}

#Make processed files for use as observation files
GTN2GTop <- function(filename){
NPraw = read.csv(filename,
               sep=",", header=T,colClasses="character")
if (sum(dim(NPraw)) == 1){
  return(NULL)
}

outfile = sub("_data\\.","_obs\\.",filename)
in.Date = as.data.frame(str_match(NPraw[,1],"(\\d{4})-(\\d{2})-(\\d{2}) (\\d{2}):(\\d{2}):(\\d{2})"))
colnames(in.Date)=c("str","year","month","day","hour","minute","second")
  
Date = paste(as.character(in.Date$day),"/",
             as.character(in.Date$month),"/",
             in.Date$year," ",as.character(in.Date$hour),":",as.character(in.Date$minute),
             sep="")
Depths = names(NPraw)[-1]
re = regexpr("\\d\\.\\d*$",Depths)
Depths_mm = as.numeric(regmatches(Depths,re))*1000

top = c("Date",Depths_mm)

fix999 = setNA(-999)
fix888 = setNA(-888)

data = as.data.frame(NPraw[,-1])
data = apply(data,2,function(x) fix999(as.numeric(x)))
data = apply(data,2,function(x) fix888(as.numeric(x)))

out.data = data.frame(Date,data)
out = rbind(top,out.data)
write.table(out,file=outfile,quote=F,sep=",",row.names=F,col.names=F)
}

## Process directory
GTN2GTop_ALL <- function(direc){
  orig.dir = getwd()
  setwd(direc)
  items = list.files(direc,pattern="_data.csv")
  lapply(items,function(x) try(GTN2GTop(x)))
  setwd(orig.dir)
}

## Get datalinks info
datalinks <- function(metadatafilename){
  in.filename = gsub("_metadata","_dataLinks",metadatafilename)
  in.file = read.csv(in.filename,header=T)
  num.GND = nrow(in.file[in.file$Variable=="Ground Temperature",])
  num.AIR = nrow(in.file[in.file$Variable=="Air Temperature",])
  num.SUR = nrow(in.file[in.file$Variable=="Surface Temperature",])
  return(list(GND=num.GND,AIR=num.AIR,SUR=num.SUR))
  #return(in.file)
}

## Summarize metadata
summarize <- function(direc){
  orig.dir = getwd()
  setwd(direc)
  items = list.files(direc,pattern="_metadata")
  summary = data.frame()
  summary[1,1]=NA
  index=1
  for (k in items){
    G = read.csv(k,header=F)
    val = G[,1][!G[,1] %in% names(summary)] # mismatching
    matching = G[,1][G[,1] %in% names(summary)] # matching
    lapply(val, function(x) summary[index,x] <<- NA) # add mismatching cols
    if (length(val) != 0){lapply(val, function(x) summary[index,x]<<-G[G$V1==x,2])} #populate mismatching cols
    if (length(matching) != 0) {lapply(matching, function(x) summary[index,x]<<-G[G$V1==x,2])} #populate matching cols
    links = datalinks(k)
    summary[index,"NumGND"]=links$GND
    summary[index,"NumAIR"]=links$AIR
    summary[index,"NumSUR"]=links$SUR
    summary[index,"totalDatasets"]= sum(c(links$SUR,links$AIR,links$GND))
    print(paste(index," files processed",sep=""))
    print(paste("completed",k))
    index = index + 1
  }
summary = summary[,-1]

summary$Depth = gsub(" +m","",summary$Depth)
summary$Latitude = gsub(" deg;","",summary$Latitude)
summary$Longitude = gsub(" deg;","",summary$Longitude)
summary$Elevation = gsub(" +m","",summary$Elevation)
summary$Slope = gsub(" deg;","",summary$Slope)


summary <- summary[,order(colnames(summary))]
write.csv(summary,"Summary.csv")
print("Summary file written to Summary.csv")
setwd(orig.dir)
return(summary)
}

## Summarize Data Links

summarizeDataLinks <-function(direct){
  setwd(direct)
  data <- list.files(pattern="_dataLinks.csv",full.names = T)
  datasummary = data.frame(Data=character(0), Frequency=character(0),
                           DataType=character(0), Method=character(0),
                           Resolution=character(0), Start=character(0),
                           End=character(0), Policy=character(0), Link=character(0),filename=character(0))
  doCompile <- function(file){
    nam <- gsub("__dataLinks.csv","",basename(file))
    infile <- read.csv(file,header=T)
    infile <- infile[,-1]
    infile$filename <- nam
    datasummary <<- rbind(datasummary,infile)
  }
  # for (file in data){
  #   infile <- read.csv(file,header=T)
  #   infile <- infile[,-1]
  #   datasummary <- rbind(datasummary,infile)
  # }
  lapply(data,doCompile)
  write.csv(datasummary,paste(direct,"/DataLinks_Summay.csv",sep=""))
  return(datasummary)
}

DL <- summarizeDataLinks("Q:\\CommonData\\PermafrostData\\GTNP\\data")


