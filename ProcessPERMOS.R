source("GTN_Process.R")

setwd("Q:\\CommonData\\PermafrostData\\PERMOS")



PERMOS2GTop <- function(filename){
  NPraw = read.csv(filename,
                   sep=",", header=T,colClasses="character",skip=4)
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