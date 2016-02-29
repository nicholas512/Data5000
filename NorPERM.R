## Deal with scraped NorPERM data
options(stringsAsFactors=FALSE)

#Make processed files for use as observation files
NP2GT <- function(filename){
NPraw = read.table(filename,
               sep=",", header=T,colClasses="character")

outfile = sub("_data\\.","_obs\\.",filename)

Date = paste(as.character(NPraw$dd),"/",
             as.character(NPraw$mm),"/",
             NPraw$yyyy," ",as.character(NPraw$hh),":",as.character(NPraw$mi),
             sep="")

Depths = names(NPraw)[-(1:6)]
re = regexpr("\\d\\.\\d*$",Depths)
Depths_mm = as.numeric(regmatches(Depths,re))*1000

top = c("Date",Depths_mm)
out.data = data.frame(Date,NPraw[,-(1:6)])
out = rbind(top,out.data)
# return(out)
write.table(out,file=outfile,quote=F,sep=",",row.names=F,col.names=F)
}

## Process directory
NP2GT_ALL <- function(dir){
  orig.dir = getwd()
  setwd(direc)
  items = list.files(direc,pattern="_data.txt")
  lapply(items,NP2GT)
  setwd(orig.dir)
}

## Summarize metadata
summarize <- function(direc){
  orig.dir = getwd()
  setwd(direc)
  items = list.files(direc,pattern="metadata")
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
    print(paste(index," files processed",sep=""))
    index = index + 1
  }
summary = summary[,-1]
summary$Latitude[is.na(summary$Latitude)]<-summary$Latitude_1[is.na(summary$Latitude)]
summary$Latitude[is.na(summary$Latitude)]<-summary$Latitude_2[is.na(summary$Latitude)]
summary$Longitude[is.na(summary$Latitude)]<-summary$Longitude_1[is.na(summary$Latitude)]
summary$Longitude[is.na(summary$Latitude)]<-summary$Longitude_2[is.na(summary$Latitude)]

setwd(orig.dir)
return(summary)
}



