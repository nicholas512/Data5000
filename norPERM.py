from BeautifulSoup import BeautifulSoup
import urllib2, re
from selenium import webdriver
import time
import pandas as pd
import csv
import os

#################
"""Trawler"""  ## an object to scrape data from norperm
#################

class Trawler(object):
    def __init__(self,wd):
        print("initialized")
        self.cur_metaURL = list()
        self.cur_dataURL = list()
        self.cur_siteMeta = dict()
        self.cur_nFiles = None
        self.out_dir = wd
        self.log = list()
        self.SuccessfulURL = list()
        self.SkippedURL = list()
        self.FailedURL = list()
    
    def CheckData(self,url):
        # open site
        html = urllib2.urlopen(url).read() 
        soup = BeautifulSoup(html)
        
        #test if data is there
        if len(soup.findAll("a")) == 1:
            return(False)   
    
        elif len(soup.findAll("a")) > 1:
            return(True)

    def getMeta(self,url): 
## Get metadata for multiple
        html = urllib2.urlopen(url).read() 
        soup = BeautifulSoup(html)
       
        info = soup.findAll("b")  
        info3 = [piece.nextSibling for piece in info]
        info2 = [piece.parent.nextSibling.nextSibling for piece in info] 
        
        # build keys
        keys=list()
        for item in info:
            key = str(item.text)
            key = re.sub(":","",key)
            key = re.sub("\.","",key)
            key = re.sub(" $","",key)
            key = re.sub(" ","_",key)
            key = re.sub("__","_",key)
            key = re.sub("^[_;\-,]*","",key) #trim leading garbage
            keys.append(key)
        
        # unique-ify keys
        unikeys = list()
        for key in keys:
            ind = 1
            testkey = key
            if not keys.count(str(testkey)) == 1:
                testkey = key + "_%s" %str(ind)    
            while testkey in unikeys:
                    testkey = key + "_%s" %str(ind)
                    ind += 1
            unikeys.append(testkey)          
        
        #build dictionary
        Metadata = dict() 
        for key in unikeys:
            val = ""
            if info2[unikeys.index(key)]:
                try:
                    val = str(info2[unikeys.index(key)].text)
                except:
                    val = "Unable to process"                
            elif not info2[unikeys.index(key)]:
                try:
                    val = str(info3[unikeys.index(key)])
                except:
                    val = "Unable to process"
            
            val = re.sub("[;, /-/.]*$","",val) # trim trailing garbage
            Metadata.update({key:val})
        
        # Add stop times (don't worry about this for now) TODO: worry about this       
        #if Metadata["Measuring_date"]:
        #    endDate = info.index(filter(lambda x: re.search("Measuring date",str(x)),info)[0])
        #    endDate = info[endDate].parent.nextSibling.nextSibling.nextSibling.nextSibling.text
        #    Metadata.update({"Measuring_date_Stop":endDate})
        
        Metadata.update({"URL":url})

        #save to object (temporary storage)
        self.cur_siteMeta = Metadata 
        
        # Write to CSV
        try:
            metafile = self.out_dir + "/" + self.cur_siteMeta["Name"] + "-" + self.cur_siteMeta["Id"] + "metadata.csv"
        except:
            metafile = self.out_dir + "/" + self.cur_siteMeta["Borehole_ID"] + "-" + self.cur_siteMeta["Name_on_Borehole"] + "metadata.csv"
        writer = csv.writer(open(metafile, 'wb'))
        for key, value in self.cur_siteMeta.items():
            writer.writerow([key, value])
        
    def TrawlPage(self,url,verbose=False):
        if self.CheckData(url) == True:  #is there data there?
            # Build Metadata
            self.getMeta(url)
            try:
                datasource = self.cur_siteMeta["Name"]
                sourceID = self.cur_siteMeta["Id"]    
            except:
                datasource = self.cur_siteMeta["Borehole_ID"]
                sourceID = self.cur_siteMeta["Name_on_Borehole"]        
            
            # Get links
            self.getDataLinks2(url)
            self.nFiles = len(self.cur_dataURL)
            
            # Gather data for each dataset on metadata page
            for link in self.cur_dataURL: 
                index = self.cur_dataURL.index(link)+1
                self.getData(link,datasource = datasource,sourceID="_FiLE-"+str(index))
            if verbose == True:
                self.log.append("Data successfully read from " +url)
                if not url in self.SuccessfulURL:
                    self.SuccessfulURL.append(url)
        else:
            if verbose == True:
                self.log.append(url+" skipped due to no data")
                if not url in self.SkippedURL:
                    self.SkippedURL.append(url)
            
    def getData(self,url,datasource="datasource",sourceID="1"):  
        # Load HTML page
        html = urllib2.urlopen(url).read()  #could probably save time here somehow
        soup = BeautifulSoup(html)
        
        #Parse HTML 
        data = soup.findAll("td","text10n") # only get data lines
        
        # Make files for data and comments
        commentsdir = self.out_dir + "/"+datasource+sourceID+"_comments.txt" # make these unique
        outdir = self.out_dir + "/"+datasource+sourceID+"_data.txt"          #make these unique
        
        # Write data and comments to file
        commentsfile = open(commentsdir,"w")
        outfile = open(outdir,"w")
        for line in data:  
            if "#" in str(line):
                outline = re.search(">(.*)<",str(line))
                outline = outline.group(1) 
                commentsfile.writelines(outline+"\n")
            elif not "#" in str(line):
                outline = re.search(">(.*)<",str(line))  # Todo: format dates better so they match with GEOtop
                outline = outline.group(1)# 
                outline = re.sub(";",",",outline)
                outline = re.sub(" ","",outline)
                outfile.writelines(outline+"\n")
        
        # Close files
        commentsfile.close()
        outfile.close()
 
    def getDataLinks2(self, url):  # same as getdatalinks but flexible for multiple data links (boreholes)
        # Open browser window to metadata page 
        driver = webdriver.Firefox()
        driver.get(url)
        
        # Find Javascript links to data
        datalinks = driver.find_elements_by_partial_link_text('measur')
        self.cur_dataURL = list()
        
        # Go through Javascript links and find stable URLs for data
        beforepop = driver.window_handles # get a list of windows
        for link in datalinks:
            link.click() #open then click
            afterpop = driver.window_handles # get the identifier of the new popup
            afterpop.remove(beforepop[0])  # remove old identified
            driver.switch_to_window(afterpop[0]) # switch to popup window
            dataURL = driver.current_url  # get URL of popup
            self.cur_dataURL.append(str(dataURL)) # add URL for that popup to list
            driver.close() # close popup
            driver.switch_to_window(beforepop) # go back to main page
        driver.switch_to_window(beforepop) # go back to main page
        driver.close() # close metadata page   

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
        

F = Trawler("/Users/Nick/Desktop/DataAcquision")


