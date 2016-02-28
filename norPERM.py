from BeautifulSoup import BeautifulSoup
import urllib2, re
from selenium import webdriver
import time
import pandas as pd
import csv

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
        

    def getMeta(self,url): 
        html = urllib2.urlopen(url).read() 
        soup = BeautifulSoup(html)
        
        # parse HTML to get relevant information
        info = soup.findAll("b")  
        info2 = [piece.parent.nextSibling.nextSibling for piece in info] 
        
        # build dictionary for metadata lookup
        Metadata = dict() 
        for item in info2:
            if item:
                key = str(info[info2.index(item)].text)
                key = re.sub(":","",key)
                key = re.sub("\.","",key)
                key = re.sub(" $","",key)
                key = re.sub(" ","_",key)
                val = str(item.text)
                Metadata.update({key:val})
        if Metadata["Measuring_date"]:
            endDate = info.index(filter(lambda x: re.search("Measuring date",str(x)),info)[0])
            endDate = info[endDate].parent.nextSibling.nextSibling.nextSibling.nextSibling.text
            Metadata.update({"Measuring_date_Stop":endDate})
        Metadata.update({"URL":url})

        #save to object (temporary storage)
        self.cur_siteMeta = Metadata 
        
        # Write to CSV
        metafile = self.out_dir + "/" + self.cur_siteMeta["Name"] + "-" + self.cur_siteMeta["Id"] + "metadata.csv"
        writer = csv.writer(open(metafile, 'wb'))
        for key, value in self.cur_siteMeta.items():
            writer.writerow([key, value])
        
    def TrawlPage(self,url):  # Todo: build this.
        
        # Build Metadata
        self.getMeta(url)
        datasource = self.cur_siteMeta["Name"]
        sourceID = self.cur_siteMeta["Id"]    
        
        # Get links
        self.getDataLinks2(url)
        self.nFiles = len(self.cur_dataURL)
        
        # Gather data for each dataset on metadata page
        for link in self.cur_dataURL: 
            index = self.cur_dataURL.index(link)
            self.getData(link,datasource = self.cur_siteMeta['Name'],sourceID="_FiLE-"+str(index))
            
    def getData(self,url,datasource="datasource",sourceID="1"):  
        # Load HTML page
        html = urllib2.urlopen(url).read()  #could probably save time here somehow
        soup = BeautifulSoup(html)
        
        #Parse HTML 
        data = soup.findAll("td","text10n") # only get data lines
        
        # Make files for data and comments
        commentsdir = "/Users/Nick/Desktop/DataAcquision" + "/"+datasource+sourceID+"_comments.txt" # make these unique
        outdir = "/Users/Nick/Desktop/DataAcquision" + "/"+datasource+sourceID+"_data.txt"          #make these unique
        
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
            link.click() #open thenk
            afterpop = driver.window_handles # get the identifier of the new popup
            afterpop.remove(beforepop[0])  # remove old identified
            driver.switch_to_window(afterpop[0]) # switch to popup window
            dataURL = driver.current_url  # get URL of popup
            self.cur_dataURL.append(str(dataURL)) # add URL for that popup to list
            driver.close() # close popup
            driver.switch_to_window(beforepop) # go back to main page
        driver.switch_to_window(beforepop) # go back to main page
        driver.close() # close metadata page   

    def getDataLinks(self, url):
        driver = webdriver.Firefox()
        driver.get(url)
        beforepop = driver.window_handles
        driver.find_elements_by_partial_link_text('measur')[0].click() #iterate over this to get multiple links?
        afterpop = driver.window_handles
        driver.switch_to_window(afterpop[1])
        self.cur_dataURL = str(driver.current_url)
        driver.close()
        driver.switch_to_window(beforepop)
        driver.close()

  #  def Trawl(self,startID):
        

F = Trawler("/Users/Nick/Desktop/DataAcquision")
F.getDataLinks('http://aps.ngu.no/pls/oradb/minres_pe_fakta.pe_mtd?p_id=511&p_spraak=E')

F.getData('http://aps.ngu.no/pls/oradb/minres_pe_fakta.EXP_MTD_DATA?p_id=583&p_spraak=E')  
F.getMeta("http://aps.ngu.no/pls/oradb/minres_pe_fakta.pe_mtd?p_id=477&p_spraak=E")

links = soup.findAll('a')
dataLink = soup.findAll(href=re.compile("measuring"))
newHTML = re.search('(http://.*spraak=E)',str(dataLink))


## Get metadata for multiple
html = urllib2.urlopen('http://aps.ngu.no/pls/oradb/minres_pe_fakta.pe_mtd?p_id=501&p_spraak=E').read() 
soup = BeautifulSoup(html)
        
info = soup.findAll("b")  
info2 = [piece.parent.nextSibling.nextSibling for piece in info] 

Metadata = dict() 
for item in info2:
    if item:
        print("this item %s")%(str(item)) 
        ind = 2
        key = str(info[info2.index(item)].text)
        key = re.sub(":","",key)
        key = re.sub("\.","",key)
        key = re.sub(" $","",key)
        key = re.sub(" ","_",key)
        val = str(item.text)
        testkey = key
        while testkey in Metadata.keys():
            print(str(testkey) +"is already in the keys")
            testkey = key + "_%s" %str(ind)
            ind += 1  
        Metadata.update({testkey:val})

if Metadata["Measuring_date"]:
    endDate = info.index(filter(lambda x: re.search("Measuring date",str(x)),info)[0])
    endDate = info[endDate].parent.nextSibling.nextSibling.nextSibling.nextSibling.text
    Metadata.update({"Measuring_date_Stop":endDate})
Metadata.update({"URL":url})

##  Get metadata and write to Csv
html = urllib2.urlopen('http://aps.ngu.no/pls/oradb/minres_pe_fakta.pe_mtd?p_id=477&p_spraak=E').read()
soup = BeautifulSoup(html)
info = soup.findAll("b")
info2 = [piece.parent.nextSibling.nextSibling for piece in info]
Metadata = dict()
for item in info2:
    if item:
        key = str(info[info2.index(item)].text)
        key = re.sub(":","",key)
        key = re.sub("\.","",key)
        key = re.sub(" $","",key)
        key = re.sub(" ","_",key)
        val = str(item.text)
        Metadata.update({key:val})


## Get data and write to csv
html = urllib2.urlopen('http://aps.ngu.no/pls/oradb/minres_pe_fakta.EXP_MTD_DATA?p_id=593&p_spraak=E').read()  #could probably save time here somehow
soup = BeautifulSoup(html)
data = soup.findAll("td","text10n") # only get data lines
commentsdir = "/Users/Nick/Desktop/DataAcquision" + "/comments1.txt"
outdir = "/Users/Nick/Desktop/DataAcquision" + "/data1.txt"
commentsfile = open(commentsdir,"w")
outfile = open(outdir,"w")
for line in data:
    if "#" in str(line):
        outline = re.search(">(.*)<",str(line))
        outline = outline.group(1) 
        commentsfile.writelines(outline+"\n")
    elif not "#" in str(line):ta.str
        outline = re.search(">(.*)<",str(line))
        outline = outline.group(1)# t
        outline = re.sub(";",",",outline)
        outline = re.sub(" ","",outline)
        outfile.writelines(outline+"\n")
commentsfile.close()
outfile.close()

#  Get link for data
driver = webdriver.Firefox()
driver.get('http://aps.ngu.no/pls/oradb/minres_bo_fakta.boho?p_id=154&p_spraak=E')
datalinks = driver.find_elements_by_partial_link_text('measur')contenturl = "http://www.bank.gov.ua/control/en/curmetal/detail/currency?period=daily"
soup = BeautifulSoup(urllib2.urlopen(contenturl).read())
outlinks = list()
beforepop = driver.window_handles # get a list of windows
for link in datalinks:
    link.click() #open the link
    afterpop = driver.window_handles # get the identifier of the new popupsoup
    
    afterpop.remove(beforepop[0])  # remove old identified
    driver.switch_to_window(afterpop[0]) # switch to popup window
    dataURL = driver.current_url  # get URL of popup
    outlinks.append(str(dataURL)) # add URL for that popup to list
    driver.close() # close popup
    driver.switch_to_window(beforepop) # go back to main page
driver.switch_to_window(beforepop) # go back to main page
driver.close() # close metadata page

##  http://aps.ngu.no/pls/oradb/minres_bo_fakta.boho?p_id=154&p_spraak=E  this is a borehole


## Get metadata for multiple
html = urllib2.urlopen('http://aps.ngu.no/pls/oradb/minres_pe_fakta.pe_mtd?p_id=501&p_spraak=E').read() 
soup = BeautifulSoup(html)
        
info = soup.findAll("b")  
info2 = [piece.parent.nextSibling.nextSibling for piece in info] 

# build keys
keys=list()
for item in info:
    key = str(item.text)
    key = re.sub(":","",key)
    key = re.sub("\.","",key)
    key = re.sub(" $","",key)
    key = re.sub(" ","_",key)
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
    if info2[unikeys.index(key)]:
        val = str(info2[unikeys.index(key)].text)
        Metadata.update({key:val})

# Add stop times (don't worry about this for now) TODO: worry about this       
#if Metadata["Measuring_date"]:
#    endDate = info.index(filter(lambda x: re.search("Measuring date",str(x)),info)[0])
#    endDate = info[endDate].parent.nextSibling.nextSibling.nextSibling.nextSibling.text
#    Metadata.update({"Measuring_date_Stop":endDate})

Metadata.update({"URL":url})