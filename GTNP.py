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
import time

"""
                         ..,co88oc.oo8888cc,..
  o8o.               ..,o8889689ooo888o"88888888oooc..
.88888             .o888896888 .88888888o'?888888888889ooo....
a888P          ..c6888969""..,"o888888888o.?8888888888"".ooo8888oo.
088P        ..atc88889"".,oo8o.86888888888o 88988889",o888888888888.
888t  ...coo688889"'.ooo88o88b.'86988988889 8688888'o8888896989^888o
 888888888888"..ooo888968888888  "9o688888' "888988 8888868888'o88888
  ""G8889""'ooo888888888888889 .d8o9889""'   "8688o."88888988 o888888o .
           o8888''''''''''''   o8688"          88868. 888888.68988888"o8o.
           88888o.              "8888ooo.        '8888. 88888.8898888o"888o.
           "888888'               "888888'          '""8o"8888.8869888oo8888o .
      . :.:::::::::::.: .     . :.::::::::.: .   . : ::.:."8888 "8888888888 8o
                                                        :..8888,. "88888888888.
                                                        .:o888.o8o.  "866o9888o
                                                         :888.o8888.  "88."89".
                                                        . 89  888888    "88":.
                                                        :.     '8888o
                                                         .       "8888..
                                                                   888888o.
                                                                    "888889,
                                                             . : :.:::::::.: :.

"""

#################
"""Prowler"""  ## an object to scrape data from GTN-P
#################
## TODO: make some internal things private (__) or (_)
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
        self.out_dir = wd
        self.log = list()
        self.successfulURL = list()
        self.skippedURL = list()
        self.failedURL = list()
        self.FFprofile = webdriver.FirefoxProfile()
        self.boreholesWithData = "No boreholes with data, try processing mainpage HTML"
        self.boreholeNames = ['Name','TC-Code','GTN-P']
        self.dataNames = ['Site','TC-Code','GTN-P','Frequency','Type']
        # RunFunctions
        self.BuildFF()
    
    def resetSite(self):
        self.cur_siteMeta = list()
        self.cur_groundDataURL = list()
        self.cur_surfaceDataURL = list()
        self.cur_airDataURL = list()  
        self.cur_siteData = pd.DataFrame()
        self.cur_siteExistsData = False
        
    def logAppend(self,url,event):
        if event == "fail":
            log = self.failedURL
        elif event == "success":
            log = self.successfulURL
        elif event == "skip":
            log = self.skippedURL
        if not url in log:
            log.append(url)
        
    def buildNameStringBH(self):
        name=''
        for i in self.boreholeNames:
            try:
                name = name + self.cur_siteMeta[i] + "_"
            except:
                pass
        return(name)
            
    def BuildFF(self):
        """ Make firefox profile for webdriver to automatically download things"""
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
    
    def getMeta(self,url):  
        """Get metadata from gtnpdatabase.org/boreholes/view/#### page"""
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
    
    def getDataLinks(self, url, keepOpen=False):  # should be run AFTER getMeta
        """ Get links of all relevant data (ground, air, surface temperatures) linked from meta page"""
        if len(self.cur_siteMeta) == 0:
            print("run siteMeta() first to populate data fields for naming purpose")
        
        if url != self.cur_siteMeta["URL"]:
            self.getMeta(url)
        # Open browser window to metadata page 
        time.sleep(1)
        try:
            if len(self.driver.window_handles) == 0: ###  check if there's already a driver loaded,
                self.driver = webdriver.Firefox(self.FFprofile)
        except:   #otherwise load a new one
            self.driver = webdriver.Firefox(self.FFprofile)
        self.driver.get(url)

        # Go to data page and get HTML soup then maybe close data page
        try:
            datalink = self.driver.find_element_by_id("dataButton")
        except:
            print("data page does not exist.  Err 404")
            self.driver.close()
            return

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
    
    def getData(self,url, pageOpen=False, keepOpen=False,CurrentMeta="self"):       # This is kind of awkward...
        if pageOpen == False:  
            # url is link of dataset page
            # CurrentMeta is the URL of the metadata /borehole page that leads to the url  
            # assumes everything is hunky-dory with accesing the data pages            
            # TODO: seems to be some trouble if it quits unexpectedly with loading the FFprofile.
            #   Maybe make it so it automatically kills the active driver at the end if it crashes...
            
            # Load firefox profile with preferences
            time.sleep(1)
            self.driver = webdriver.Firefox(self.FFprofile)
            
            # Specify current borehole metadata either from self, or argument
            if CurrentMeta == "self":
                self.driver.get(self.cur_siteMeta["URL"]) # load metadata page
            elif CurrentMeta != "self":
                self.driver.get(CurrentMeta)
            
            #Open up data links page 
            datalink = self.driver.find_element_by_id("dataButton") # taken from getdatalinks
            datalink.click()
            
            #Go to specific data page
            try:
                match = re.search("/datasets/view/\d+",url)
                match = match.group(0)
                css="a[href*='"+match+"']"
                self.driver.find_element_by_css_selector(css).click()
            except:
                print("warning, link URL does not match specified current metadata")

        # If the brower page is already open, just go straight to the link
        elif pageOpen == True:
            self.driver.get(url) # sometimes this doesn't load

        # Hope that you're on the right page, then download the data. 
        if 'datasets/view' in self.driver.current_url:
            #click click click - this downloads the data from the view page
            getdata=self.driver.find_element_by_class_name("button")
            getdata.click()
            Agree=self.driver.find_elements_by_class_name("ui-widget-content")[2]
            Agree.click()
            self.driver.back() 
            if keepOpen == False:
                self.driver.close()
            elif keepOpen == True:
                pass
        else:
            print('something went wrong, unable to load %s')%url
            self.logAppend(url,"fail")
       
    def processData(self,PFfile,addSiteMeta=False,rename=False):  # Go through downloaded file and split it up
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
        for PFfile in glob.glob(direc +'/*.MASKcsvX'):
                os.rename(PFfile,re.sub("MASKcsvX$",'csv',PFfile))
    
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
        # url is for borehole metadata page
        
        #Gather borehole metadata
        self.getMeta(url)
        
        # Get data links and record in self
        self.getDataLinks(url,keepOpen=True)
        
        if self.cur_siteExistsData==True:
            # Get data for each link and process
            longlist = self.cur_groundDataURL + self.cur_airDataURL + self.cur_surfaceDataURL
            for link in longlist:
                self.getData(link,pageOpen=True, keepOpen=True)
                # scan downloads directory for CSV, process, and rename
                counter = 0
                while counter < 10 and len(glob.glob(self.downloadDir + '/*.csv')) ==0: #wait for file to d/l
                    time.sleep(1)
                    counter += 1    
                newCSV = max(glob.iglob(self.downloadDir + '/*.csv'),key=os.path.getctime) # get newest file                                  
                self.processData(newCSV, addSiteMeta=True, rename=True)
        else:
            print("warning, no temperature data found for %s")%url
            self.logAppend(url,"skip")
            
        # close window
        self.driver.close()
    
    def writeLog(self):
        outdir = self.out_dir + "/"+ "log.txt"
        outfile = open(outdir,"w")
        outfile.writelines("Successfully read URLs: \n")
        for line in self.successfulURL:
            outfile.writelines(line + "\n")
        outfile.writelines("Skipped URLs (No Data): \n")
        for line in self.skippedURL:
            outfile.writelines(line + "\n")
        outfile.writelines("Error URLs: \n")
        for line in self.failedURL:
            outfile.writelines(line + "\n")
        outfile.close()
        
    def prowl(self,fileList="mainpage in directory",subfolder = "Boreholes",mainpage="/GTNP_Main.csv"):
        
        #Get lists
        if fileList == "mainpage in directory":
            self.processMainpage(self.out_dir+mainpage)
            fileList = self.boreholesWithData
        elif fileList != "mainpage in directory":
            fileList = fileList
            
        # get data for all pages in fileList            
        for borehole in fileList:
            try:
                self.prowlPage(borehole, verbose=True)
                self.logAppend(borehole,"success")
                self.resetSite()
                
            except:
                print("Error. Something went wrong with site, skipping %s")%borehole
                self.logAppend(borehole,"fail")
        #tidy up 
        self.unmaskCSV(self.downloadDir)         
        self.writeLog() # write log
        self.log = list() # reset log