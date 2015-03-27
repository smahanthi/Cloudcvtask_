
from models import *

import httplib2
import random
import string
import os, sys
import urllib,  urllib2
import mechanize 
from bs4 import BeautifulSoup
from urlparse import urlparse
import hashlib
from shutil import rmtree

from PyQt4.QtGui import *  
from PyQt4.QtCore import *  
from PyQt4.QtWebKit import * 
from contextlib import closing

from flask.ext.sqlalchemy import SQLAlchemy

import flickrapi
import zipfile
import glob

import xml.etree.ElementTree as ET
#Flicker API key and Secret
api_key = u'329dc004c67aecaf2fff7abf41e6985a'
api_secret = u'afcf872419042ba6'
#------------------------------------------
myjobid = ""
curruserid = 0

basedirec = os.path.dirname(os.path.abspath(__file__))

def dropboxfunc(dburl,  jobid):
    dburl = dburl[:-1]
    url = str(dburl)+'1'
    print "Downloading dropbox zip file"
    urllib.urlretrieve(url, basedirec+"/testfolder/"+str(jobid)+"/dropbox.zip")
    print "Extracting zip file"
    fh = open(basedirec+"/testfolder/"+str(jobid)+"/dropbox.zip", "rb")
    z = zipfile.ZipFile(fh)
    for name in z.namelist():
        makenewdir(basedirec+"/testfolder/"+str(jobid)+"/dropbox/")
        outpath = basedirec+"/testfolder/"+str(jobid)+"/dropbox/"
        z.extract(name, outpath)
    fh.close()
    basepath = basedirec+"/testfolder/"+str(jobid)+"/dropbox/"
    testpath = basedirec+"/testfolder/"+str(jobid)+"/test/"
    print "Sorting out the images and moving them to test folder"
    imlist = glob.glob(basepath+"*.jpg")
    imlinks = []
    i = len(imlist)
    while(i):
        os.rename(imlist[i-1], testpath+"image"+str(i)+".jpg")
        imlinks.append("/testimages/"+str(jobid)+"/test/"+"image"+str(i)+".jpg")
        i=i-1
    os.remove(basedirec+"/testfolder/"+str(jobid)+"/dropbox.zip")
    rmtree(basepath)
    return imlinks

def flickrsearch(sterm,  num):
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
    photos = flickr.photos.search(text=str(sterm), per_page=num, sort='relevance')
    print "Searching for images from Flickr"
    piclist = photos['photos']['photo']
    top = num
    count = 0
    picurllist = []
    while(top):
        picurl='https://farm'+str(piclist[count]['farm'])+'.staticflickr.com/'+str(piclist[count]['server'])+'/'+str(piclist[count]['id'])+'_'+str(piclist[count]['secret'])+'.jpg'
        picurllist.append(picurl)
        count = count+1
        top = top-1
    return picurllist

def storetodb(userid):
    #Check if userid already exists in the table
    rows = 0
    global curruserid
    global myjobid
    temp = db.session.query(User).filter_by(username=userid).first()
    if temp:
        rows = temp.id
        curruserid = rows
        usernotexists = 0
        print "User already exists in the records"
    else:    
        rows = db.session.query(User).count()
        curruserid = rows+1
        curruserid = rows+1
        usernotexists = 1
    #Create a new jobid for the user and save it to the database    
    if usernotexists:
        userinfo = User(userid, curruserid)
        db.session.add(userinfo)
        print "New user created!"
    db.session.commit()    
    return curruserid

def setjobid():
    key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                         for x in xrange(8))
    while(checkkey(key)):
        key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                         for x in xrange(8))
    print "New job id set for user = "+str(key)
    return key

def checkkey(key):
    global curruserid
    keylist = db.session.query(jobid).filter_by(job_id=key).first()
    if keylist:
        return 1
    else:
        jobid_ = jobid(curruserid, key)
        db.session.add(jobid_)
        db.session.commit()
        return 0

def makenewdir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

def bingimsearch(sterm, num):
    keyBing = 'icnKxefA7YKWHUa+eLV57KHkZx9uslbtTqbNhyqZ+Qs'        # get Bing key from: https://datamarket.azure.com/account/keys
    credentialBing = 'Basic ' + (':%s' % keyBing).encode('base64')[:]
    searchString = str(sterm)
    top = num
    offset = 0
    url = 'https://api.datamarket.azure.com/Bing/Search/Image?' + \
      'Query=%s&$top=%d&$skip=%d&$format=json' % (searchString, top, offset)
    request = urllib2.Request(url)
    request.add_header('Authorization', credentialBing)
    requestOpener = urllib2.build_opener()
    response = requestOpener.open(request) 
    results = json.load(response)
    return results

def googleimsearch(sterm, num):    
    i = 1
    imnumber = num
    jsonresult = []
    while(i<imnumber):
        google_request = imservice.cse().list(q=str(sterm),searchType='image',start=i,cx='001934278735806547088:3rsif3omdzw')
        result = google_request.execute(http=http)
        jsonresult.append(json.dumps(result));
        i = i+9;
    
    response = make_response(json.dumps(jsonresult), 200)
    return response
#------------------------------------------------------------------------
#Search functions without using Google API
class JSrender(QWebPage):  
  def __init__(self, url):  
    self.app = QApplication(sys.argv)  
    QWebPage.__init__(self)  
    self.loadFinished.connect(self._loadFinished)  
    self.mainFrame().load(QUrl(url))  
    self.app.exec_()  
  
  def _loadFinished(self, result):  
    self.frame = self.mainFrame()  
    self.app.quit()  

def saveallPics(imlist, jobid, term):
    img_list = imlist
    imdirectory = basedirec+"/testfolder/"+str(jobid)+"/train/"+str(term)+"/"
    makenewdir(imdirectory)
    makenewdir(basedirec+"/testfolder/"+str(jobid)+"/test/")
    makenewdir(basedirec+"/testfolder/"+str(jobid)+"/util/")	        
    i = 0
    if len(img_list)>0:
        for img in img_list:
            savePic(img, imdirectory, 'image'+str(i))
            i = i+1
    print "All files saved!    Directory=" + str(imdirectory)    

def savePic(url,imdir, fname):
    urllib.urlretrieve(url, str(imdir+fname+'.jpg'))
    print "Saved:  "+url
#    hs = hashlib.sha224(url).hexdigest()
#    file_extension = url.split(".")[-1]
#    uri = ""
#    dest = uri+hs+"."+file_extension
#    print dest
#    try:
#        (finame, fheaders) = urllib.urlretrieve(url,dest)
#        shutil.move(finame, str(imdir)+str(fname)+"."+file_extension)
#    except:
#        print "save failed" 

def getPic (search):
    search = search.replace(" ","%20")
    try:
        url = "https://www.google.com/search?site=imghp&tbm=isch&source=hp&biw=1414&bih=709&q="+search+"&oq="+search
        content = JSrender(url)
        content = unicode(r.frame.toHtml())
        img_urls = []
        formatted_images = []
        soup = BeautifulSoup(content)
        results = soup.findAll("a")
        for r in results:
            try:
                if "imgres?imgurl" in r['href']:
                    img_urls.append(r['href'])
            except:
                a=0
        
        for im in img_urls:
            refer_url = urlparse(str(im))
            image_f = refer_url.query.split("&")[0].replace("imgurl=","")
            formatted_images.append(image_f)
        
        return  formatted_images

    except:
        return []


#------------------------------------------------------------------------
