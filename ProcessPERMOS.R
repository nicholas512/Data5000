PERMOS2GTop <- function(filename){
  NPraw = read.csv(filename,
                   sep=",", header=T,colClasses="character", skip=4)
  
  # A few checks
  if (sum(dim(NPraw)) == 1 | length(grep('_Metadata', filename))==1) {
    return(NULL)
  }
  
  # Define output file name
  outfile <- sub("(.csv$)","_obs.csv", filename)

  
  # Put headers in body to get good names
  Depths <- names(NPraw)[-1]
  re <- regexpr("\\d\\.?\\d?$", Depths)
  Depths_mm <- as.numeric(regmatches(Depths, re))*1000
  
  top = c("Date",Depths_mm)

  out <- rbind(top,NPraw)
  write.table(out,file=outfile,quote=F,sep=",",row.names=F,col.names=F)
}

