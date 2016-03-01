## Tests

F = GTNProwler("/Users/Nick/Desktop/DataAcquision/test")

F.getMeta('http://gtnpdatabase.org/boreholes/view/832/')

# process GTNP mainpage (must have mainpage HTML in directory)
F.processMainpage()

# Get a list of boreholes with data
boreholeData = F.boreholesWithData  

F.getDataLinks(url = 'http://gtnpdatabase.org/boreholes/view/832/', keepOpen=False) # no data

# how about a good site?
F.getMeta('http://gtnpdatabase.org/boreholes/view/1144/')
F.getDataLinks(keepOpen=True)
F.getData('http://gtnpdatabase.org/datasets/view/1978',pageOpen=True,keepOpen=False)

F.ProcessData('/Users/Nick/Desktop/DataAcquision/test/downloads/FR.boreholes.AdM-NE.Ground_Temperature.Daily.1978.csv',rename=True)

#    def resetSite(self):       
#    def buildNameStringBH(self):
#
#            
#    def BuildFF(self):
#
#
#    def getMeta(self,url):  # Get metadata from gtnpdatabase.org/boreholes/view/#### page
#
#    
#    def getDataLinks(self, url = None, keepOpen=False):  # should be run AFTER getMeta
#
#
#    def getData(self,url, pageOpen=False, keepOpen=False):       
#
#       
#    def ProcessData(self,PFfile,addSiteMeta=False,rename=False):  # Go through downloaded file and split it up
#
#          
#    def unmaskCSV(self,direc):
#
#    
#    def processMainpage(self,GTNPmain):
#    
#         
#    def prowlPage(self,url,verbose=False):
#        
#
#    def writeLog(self):
#
#       
#    def prowl(self,subfolder = "Boreholes",fileList="mainpage in directory",mainpage="/GTNP_Main.csv"):
        




