from BeautifulSoup import BeautifulSoup
import urllib2, re
from selenium import webdriver
import time
import pandas as pd
import csv
import os
import unicodedata
from selenium.webdriver.common.keys import Keys
import glob

#################
"""Prowler"""  ## an object to scrape data from GTN-P
#################

class GTNProwler(object):
    def __init__(self,wd):
        print("initialized")
        #Set Values 
        self.cur_groundDataURL = list()
        self.cur_surfaceDataURL = list()
        self.cur_airDataURL = list()
        self.cur_siteMeta = dict()
        self.cur_siteData = pd.DataFrame()
        self.cur_siteExistsData = False
        self.files_to_dl = list()
        self.out_dir = wd
        self.log = list()
        self.SuccessfulURL = list()
        self.SkippedURL = list()
        self.failedURL = list()
        self.FFprofile = webdriver.FirefoxProfile()
        self.boreholesWithData = list()
        self.boreholeNames = ['Name','TC-Code','GTN-P']
        self.dataNames = ['Site','TC-Code','GTN-P','Frequency','Type']
        # RunFunctions
        self.BuildFF()
    
    def resetSite(self):
        self.files_to_dl = list()
        self.cur_siteMeta = list()
        self.cur_groundDataURL = list()
        self.cur_surfaceDataURL = list()
        self.cur_airDataURL = list()  
        self.cur_siteData = pd.DataFrame()
        self.cur_siteExistsData = False

        
    def buildNameStringBH(self):
        name=''
        for i in self.boreholeNames:
            try:
                name = name + self.cur_siteMeta[i] + "_"
            except:
                pass
        return(name)
            
    def BuildFF(self):

        # Make output directory
        downloadDir = self.out_dir + "/" + "downloads"
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir)
        self.downloadDir = downloadDir

        # Set preferences to automatically download
        self.FFprofile.set_preference("browser.download.panel.shown", False)
        self.FFprofile.set_preference("browser.helperApps.neverAsk.openFile","text/csv,application/vnd.ms-excel")
        self.FFprofile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/vnd.ms-excel")
        self.FFprofile.set_preference("browser.download.folderList", 2);
        self.FFprofile.set_preference("browser.download.dir", downloadDir)
    
    def getMeta(self,url):  # Get metadata from gtnpdatabase.org/boreholes/view/#### page
        try:
            html = urllib2.urlopen(url).read()
            soup = BeautifulSoup(html)
        except:
            print("Page not found. Error 404. %s added to list of failed sites") %url
            if url not in self.failedURL:
                self.failedURL.append(url)
            return
        # Get pagename ##TODO: assert this is the same as the page name somewhere else?
        pageName = soup.div(id="formHeader")[0].h1.text
        
        # Get other data from table structure
        meta = [x.text for x in soup.findAll("tr")]
        meta = [unicodedata.normalize('NFKD', x).encode('ascii','ignore') for x in meta]
        metaDict = dict()
        for info in meta:
            if ":" in info:
                info = re.sub("&#176","deg",info)
                info = re.sub("&nbsp;","",info)
                info = info.split(":")
                metaDict.update({info[0]:info[1]})
        index = re.search("view/(\d+)",url)
        index = index.group(1)
        metaDict.update({"URL":url})
        metaDict.update({"index":index})
        metaDict.update({"Name":pageName})
        self.cur_siteMeta = metaDict
        
        outstr = self.buildNameStringBH()

        ## write to csv
        metafile = self.out_dir + "/" + outstr + "_metadata.csv"
        writer = csv.writer(open(metafile, 'wb'))
        for key, value in self.cur_siteMeta.items():
            writer.writerow([key, value])
    
    def getDataLinks(self, url = None, keepOpen=False):  # should be run AFTER getMeta
        if url == None:
            url = self.cur_siteMeta["URL"]
        # Open browser window to metadata page 
        self.driver = webdriver.Firefox(self.FFprofile)
        self.driver.get(url)
        
        # Go to data page and get HTML soup then maybe close data page
        datalink = self.driver.find_element_by_id("dataButton")
        datalink.click()
        soup = BeautifulSoup(self.driver.page_source)

        
        if keepOpen == False:
            self.driver.close()
        else:
            pass

        ## Build Table
        table = soup.findAll("table")[1]
        datalinks = ["http://gtnpdatabase.org"+ x['href'] for x in table.findAll('a')]
        
        # Interrupt: check to see if there is actually data there
        if len(datalinks) == 0:
            print("No data here.  Aborting %s")%url
            return
        # Keep going with the table     
        header = [th.text for th in table.find('thead').findAll('th')]
        body   = [[td.text for td in row.findAll('td')] for row in table.findAll('tr')]
        body = body[1:]
        [x.append(datalinks[body.index(x)]) for x in body]
        header.append("Link")
        data = pd.DataFrame(body, columns = header)
        
        ## Get ground temperature links
        Gtemps = data['Link'][data['Variable']=="Ground Temperature"]
        Stemps = data['Link'][data['Variable']=="Surface Temperature"]
        Atemps = data['Link'][data['Variable']=="Air Temperature"]
        
        if len(Gtemps) + len(Stemps) + len(Atemps) != 0:  # is there data? should we bother?
            self.cur_siteExistsData = True

        #Record ground temperature links (they might not exist)
        try:
            self.cur_groundDataURL = list(Gtemps.values)
        except:
            pass
        try:
           self.cur_airDataURL = list(Atemps.values)
        except:
            pass
        try:
           self.cur_surfaceDataURL = list(Stemps.values)
        except:
            pass

        ## Add table to storage
        self.cur_siteData = data
              
        ## Write table to csv
        outstr = self.buildNameStringBH()
        datafile = self.out_dir + "/" + outstr + "_dataLinks.csv"
        data.to_csv(datafile, sep=',', encoding = 'utf-8')
    
    def getData(self,url, pageOpen=False, keepOpen=False):       
        if pageOpen == False:  
            # URL is link of dataset page, from dataset links 
            # assumes everything is hunky-dory with accesing the data pages            
            # Load browser with preferences and get to the site
            # TODO: add some failsafes to make sure its on the right page and going to the right URL
            # Maybe should feed it with the previous page?
            # TODO: seems to be some trouble if it quits unexpectedly with loading the FFprofile.
            #   Maybe make it so it automatically kills the active driver at the end if it crashes...
            self.driver = webdriver.Firefox(self.FFprofile)
            
        elif pageOpen == True:
            pass

        self.driver.get(url) # sometimes this doesn't load
        # Assert that its a view 
        ### TODO: otherwise revert to most recent page and click through manually 

        #click click click - this downloads the data
        getdata=self.driver.find_element_by_class_name("button")
        getdata.click()
        Agree=self.driver.find_elements_by_class_name("ui-widget-content")[2]
        Agree.click()
        self.driver.back() 
        if keepOpen == False:
            self.driver.close()
        elif keepOpen == True:
            pass  
       
    def ProcessData(self,PFfile,addSiteMeta=False,rename=False):  # Go through downloaded file and split it up
        with open(PFfile, 'rb') as f:
            reader = csv.reader(f)
            orig_csv = list(reader)
        
        # Make up some containers
        comments = list()
        data = list()
        self.dataname = "NoName"
        self.datakind = "NoKind"
        self.datawhen = "NoWhen"
        self.datastart = "NoStart"
        
        ## Split file into comments and data and put in container
        for line in orig_csv:
            if "#" in line[0]:
                comments.append(line)
                #if ("##Name:" in line[0]) and self.dataname == "NoName":  ### TODO: unique-ify by linking to pd table
                #    dataname = re.search("Name:(.*)",line[0])
                #    self.dataname = dataname.group(1)
                if "##Variable:" in line[0]:
                    datakind = re.search("Variable:(.*)",line[0])
                    self.datakind = datakind.group(1)
                if "##Frequency:" in line[0]:
                    datawhen = re.search("Frequency:(.*)",line[0])
                    self.datawhen = datawhen.group(1)
                #if "##Start:" in line[0]:
                #    datastart = re.search("Start:(.*)",line[0])
                #    self.datastart = datastart.group(1)
            elif not "#" in line[0]:
                data.append(line)
        
        # Open File  Todo: change this to use WITH
        outstr = self.buildNameStringBH()
        outdata = self.out_dir + "/" + outstr + self.datawhen +"_" +self.datakind + "_data.csv" ###  TODO: add self.cur_siteMeta fields?
        outcomments = self.out_dir + "/" + outstr + self.datawhen +"_" +self.datakind + "_comments.csv"
        commentsfile = open(outcomments,'wb')
        datafile = open(outdata,'wb')

        # Create Writer Object
        wrCOM = csv.writer(commentsfile, dialect='excel')
        wrDAT = csv.writer(datafile, dialect='excel')
        
        # Write Data to File
        for item in comments:
            wrCOM.writerow(item)
        """ if addSiteMeta = True then add info from self.cur_siteMeta """
        for item in data:
            wrDAT.writerow(item)
            
        #Close files
        commentsfile.close()
        datafile.close()
        
        #Mask out csv file
        if rename == True:
            os.rename(PFfile,re.sub('csv$',"MASKcsvX",PFfile))
    
    def unmaskCSV(self,direc):
        for PFfile in glob.glob(direc +'/.MASKcsvX'):
                os.rename(PFfile,re.sub("MASKcsvX$",'csv$',PFfile))
    
    def processMainpage(self,GTNPmain="inSameDirectory"):
        
        if GTNPmain == "inSameDirectory":
            GTNPmain = self.out_dir +'/GTNP_Main.txt'

        ## Open gtnpdatabase.org HTML - you need to get this from page source (inspect) directly
        with open(GTNPmain) as markup:  
            GTNP = BeautifulSoup(markup.read())
        
        ## Build a table 
        table = GTNP.findAll("table")[0]
        datalinks = ["http://gtnpdatabase.org"+ x['href'] for x in table.findAll('a')] # get all links
        datalinks = [x for x in datalinks  if ('borehole' in x)]
        header = [th.text for th in table.find('thead').findAll('th')]
        body   = [[td.text for td in row.findAll('td')] for row in table.findAll('tr')]
        body = body[1:]
        [x.append(datalinks[body.index(x)]) for x in body]
        header.append("Link")
        data = pd.DataFrame(body, columns = header)
        
        #Make note of sites to prowl
        self.boreholesWithData = list(data['Link'][data['Data']=="Yes"])
        
        # Write it as a CSV
        datafile = self.out_dir + "/" + "_GTNP_main.csv"
        data.to_csv(datafile, sep=',', encoding = 'utf-8')    
         
    def prowlPage(self,url,verbose=False):
        
        #Gather borehole metadata
        self.getMeta(url)
        
        # Get data links and record in self
        self.getDataLinks(link,keepOpen=True)
        
        if self.cur_siteExistsData==True:
            # Get data for each link (right now only ground temps) and process)
            for link in self.cur_GroundDataURL:
                # scan downloads directory for CSV, process, and rename
                self.getData(link,pageOpen=True, keepOpen=True)          
                newCSV = glob.glob(downloadDir + '/*.csv')
                self.processData(newCSV, addSiteMeta=Tue, rename=True)
            
        # close window
        self.webdriver.close()
    
    def writeLog(self):
        outdir = self.out_dir + "/"+ "log.txt"
        outfile = open(outdir,"w")
        outfile.writelines("Successfully read URLs: \n")
        for line in self.SuccessfulURL:
            outfile.writelines(line + "\n")
        outfile.writelines("Skipped URLs: \n")
        for line in self.SkippedURL:
            outfile.writelines(line + "\n")
        outfile.writelines("Error URLs: \n")
        for line in self.failedURL:
            outfile.writelines(line + "\n")
        outfile.close()
        
    def prowl(self,subfolder = "Boreholes",fileList="mainpage in directory",mainpage="/GTNP_Main.csv"):
        
        #Get lists
        if fileList == "mainpage in directory":
            self.processMainpage(self.out_wd+mainpage)
            fileList = self.boreholesWithData
        elif fileList != "mainpage in directory":
            fileList = fileList
            
        # get data for all pages in fileList            
        for borehole in fileList:
            try:
                self.prowlPage(borehole, verbose=True)
            except:
                print("Error. Something went wrong with site, skipping %s")%borehole
                if not borehole in self.failedURL:
                    self.failedURL.append(borehole)
        #tidy up 
        self.unmaskCSV(self.downloadDir)         
        self.writeLog() # write log
        self.log = list() # reset log


F = GTNProwler("/Users/Nick/Desktop/DataAcquision")



