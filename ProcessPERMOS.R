library(stringr)

PERMOS2GTop <- function(filename){
  if (length(grep('_Metadata', filename))==1 | length(grep('_obs', filename))==1) {
    return(NULL)
  }
  NPraw = read.csv(filename,
                   sep=",", header=T,colClasses="character", skip=4)
    # A few checks
  if (sum(dim(NPraw)) == 1) {
    return(NULL)
  }
  
  # Define output file name
  outfile <- sub("(.csv$)","_obs.csv", filename)

  
  # Put headers in body to get good names
  Depths <- names(NPraw)[-1]
  re <- regexpr("\\d\\.?\\d?$", Depths)
  Depths_mm <- as.numeric(regmatches(Depths, re))*1000
  
  # Fix Dates
  NPraw[,1] <- as.Date(NPraw[,1],format="%Y-%m-%d %H:%M:%S")
  NPraw[,1] <- format(NPraw[,1],"%Y/%m/%d %H:%M")
  
  top = c("Date",Depths_mm)
  
  out <- rbind(top,NPraw)
  write.table(out,file=outfile,quote=F,sep=",",row.names=F,col.names=F)
}

PERMOS <- function(filepath, info=1){
  # Get ID code
  code <- str_match(filepath,"[\\\\/]([A-Z]{3}_\\d{4})")[2]
  dir <- dirname(filepath)
  datafile <- list.files(dir,pattern = paste(code,".*","_obs",sep=""),full.names=T)
  
  # read in metadata
  Metadata <- read.csv(filepath,
                   sep=",", header=T)
  
  # read in data file
  Data <- read.csv(datafile, header=F, stringsAsFactors=F)
  Data.top <- Data[1,]
  Data.body <- Data[-1,]
  dates = as.Date(Data.body[,1],format="%Y/%m/%d %H:%M")
  
  # get start, end date delta t
  Start <- min(dates)
  Finish <- max(dates)
  dt <- Finish-Start
  
  # get total number of depths
  Depths <- as.numeric(Data.top[-1])
  nz <- length(Depths)
  
  # get min/max depth
  zmin = min(Depths)
  zmax = max(Depths)
  
  # get NA information for depths
  countNA <- apply(Data.body[,-1], 2, function(x) length(which(is.na(x))))
  percentNA <- round((countNA*100 / dim(Data.body)[1]),1)
  
  NAinfo <- data.frame(depth_mm = Depths,countNA = countNA,
                       percentNA = percentNA,
                       Code= rep(code,length(Depths)))
  # number of NA depths with cutoff?
  
  extra <- data.frame(Start.Date = Start, End.Date = Finish, dt = dt, 
                      dt2 = as.numeric(dt), nz = nz, zmin_mm = zmin,
                      zmax_mm = zmax)
  out <- cbind(Metadata,extra)
  
  if (info == 1) {return(out)
  } else if (info == 2) {return(NAinfo)}
}

