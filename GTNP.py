from BeautifulSoup import BeautifulSoup
import urllib2, re
from selenium import webdriver
import time
import pandas as pd
import csv
import os
import unicodedata
from selenium.webdriver.common.keys import Keys
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
        self.files_to_dl = list()
        self.out_dir = wd
        self.log = list()
        self.SuccessfulURL = list()
        self.SkippedURL = list()
        self.FailedURL = list()
        self.FFprofile = webdriver.FirefoxProfile()
        
        # RunFunctions
        self.BuildFF()
        
    def BuildFF(self):
        # Set preferences to automatically download
        self.FFprofile.set_preference("browser.download.panel.shown", False)
        self.FFprofile.set_preference("browser.helperApps.neverAsk.openFile","text/csv,application/vnd.ms-excel")
        self.FFprofile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/vnd.ms-excel")
        self.FFprofile.set_preference("browser.download.folderList", 2);
        self.FFprofile.set_preference("browser.download.dir", self.out_dir)
    
    def getMeta(self,url):
        try:
            html = urllib2.urlopen(url).read()
            soup = BeautifulSoup(html)
        except:
            print("Page not found. Error 404. %s added to list of failed sites") %url
            if url not in self.FailedURL:
                self.FailedURL.append(url)
            return
        
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
        self.cur_siteMeta = metaDict
        
        try:
            metafile = self.out_dir + "/" + self.cur_siteMeta["Site"] + "_metadata.csv"
        except:
            metafile = self.out_dir + "/" + self.cur_siteMeta["TC-Code"] + "_metadata.csv"
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
        try:
            datafile = self.out_dir + "/" + self.cur_siteMeta["Site"] + "_dataLinks.csv"
        except:
            datafile = self.out_dir + "/" + self.cur_siteMeta["GTN-P"] + "_dataLinks.csv"
        data.to_csv(datafile, sep=',', encoding = 'utf-8')
    
    def getData(self,url, pageopen=False, keepopen=False):       
        if pageopen == False:   
            # assumes everything is hunky-dory with accesing the data pages            
            # Load browser with preferences and get to the site
            self.driver = webdriver.Firefox(self.FFprofile)
            
        elif pageopen == True:
            pass

        self.driver.get(url) # sometimes this doesn't load

        #click click click - this downloads the data
        getdata=self.driver.find_element_by_class_name("button")
        getdata.click()
        Agree=self.driver.find_elements_by_class_name("ui-widget-content")[2]
        Agree.click()
        if keepopen == False:
            self.driver.close()
        elif keepopen == True:
            self.driver.back()  
       
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
                if ("##Name:" in line[0]) and self.dataname == "NoName":  ### TODO: unique-ify by linking to pd table
                    dataname = re.search("Name:(.*)",line[0])
                    self.dataname = dataname.group(1)
                if "##Variable:" in line[0]:
                    datakind = re.search("Variable:(.*)",line[0])
                    self.datakind = datakind.group(1)
                if "##Frequency:" in line[0]:
                    datawhen = re.search("Frequency:(.*)",line[0])
                    self.datawhen = datawhen.group(1)
                if "##Start:" in line[0]:
                    datastart = re.search("Start:(.*)",line[0])
                    self.datastart = datastart.group(1)
            elif not "#" in line[0]:
                data.append(line)
        
        # Open File  Todo: change this to use WITH
        outdata = self.out_dir + "/" + self.dataname +"_" + self.datakind +"_" +self.datawhen + "_data.csv" ###  TODO: add self.cur_siteMeta fields?
        outcomments = self.out_dir + "/" + self.dataname +"_" +self.datakind +"_" +self.datawhen + "_comments.csv"
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
            os.rename(PFile,re.sub('csv$',"MASKcsvX",PFile))
        
    def ProwlPage(self,url,verbose=False):
        # for each
        # Get Meta
        # check somewhere here that data exists
        # Get links, keep window open
        # for all links, get data, window=open, keepopen =True
        # Process data and rename file
        # close window
        
    
    def CheckData(self,url=None):
        if url==None:
            url = 'http://gtnpdatabase.org/datasets?alholeid=' + self.cur_siteMeta["index"]        
        # open site
        html = urllib2.urlopen(url).read() 
        soup = BeautifulSoup(html)
   
        #test if data is there
        if len(soup.findAll("a")) == 1:
            return(False)   
    
        elif len(soup.findAll("a")) > 1:
            return(True)
 

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
        for line in self.FailedURL:
            outfile.writelines(line + "\n")
        outfile.close()
        
    def Trawl(self,startID,fileList,datatype = "unknwntyp"):
        originaldir = self.out_dir
        self.out_dir = self.out_dir + "/" + datatype
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        for url in fileList:
            try:
                self.TrawlPage(url,verbose=True)
            except:
                print("error in processing" + url)
                self.FailedURL.append(url)
        self.writeLog() # write log
        self.log = list() # reset log
        self.out_dir = originaldir # reset working directory
        

F = GTNProwler("/Users/Nick/Desktop/DataAcquision")


