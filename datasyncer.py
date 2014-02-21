import psycopg2
import md5
import MultipartPostHandler, urllib2, cookielib
import json
import os, stat

sqlserverIp = "192.168.174.56"
sqlserverPort = "5432"
imgroot = 'imgori'
fileuploadUrl = "http://localhost/files/"
filestatusUrl = "http://localhost/status/"
maxsize = 10000
class Sync():
    def insertTestQueue(self):
        cookies = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
        params = {"theFile" : open("client_samples/python/files/a.png", "rb"),
          'FileId': "testtesttesttest" }
        #print opener.open(fileuploadUrl, params).read()
        conn = psycopg2.connect(database="prometheus_development", user="postgres", password="123", host=sqlserverIp, port=sqlserverPort)
        cur = conn.cursor()
        testfile = open("client_samples/python/files/a.png", "rb");
        sql = "INSERT INTO file_sync_queues(fileid,starttime,md5,suffix,priority) VALUES('%s',now(),'%s','%s',0)" % ('testtesttesttest',  md5.new(testfile.read()).hexdigest(),'png')
        print sql
        cur.execute(sql)
        testfile.close()
        conn.commit()
        cur.close()
        conn.close()
        
    def startUploading(self,fileInfo,count = 1,startPoint = 0):
        if count > 3:
            print "tried 3 times, cannot upload, will try later"
            return False
        print startPoint
        #print fileInfo
        if startPoint == 0:
            self.UpdateQueueStartTime(fileInfo)
        suffix = fileInfo[4]
        filename = fileInfo[1]
        realpath = '/'.join([imgroot,suffix,filename[1:3], filename[4:6], filename[7:9],filename[10:]])
        if suffix != 'none':
            realpath = realpath+'.'+suffix
        filesize = os.path.getsize(realpath)
        if startPoint*maxsize > filesize:
            return True
        cookies = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler(startPoint*maxsize,maxsize))
        params = {"theFile" : open(realpath, "rb"),
          'FileId': filename }
        res = opener.open(fileuploadUrl, params) 
        resstr = res.read()
        #print resstr
        resdic = json.loads(resstr)
        if not resdic["success"]:
            return self.startUploading(fileInfo,count+1,startPoint)
        else:
            return self.startUploading(fileInfo,count,startPoint+1)
        #=======================================================================
        # try:
        #     res = opener.open(fileuploadUrl, params) 
        #     resstr = res.read()
        #     print resstr
        #     resdic = json.loads(resstr)
        #     if not resdic["success"]:
        #         return self.startUploading(fileInfo,count+1,startPoint)
        #     else:
        #         return self.startUploading(fileInfo,count,startPoint+1)
        # except:
        #     return self.startUploading(fileInfo,count+1,startPoint)
        #=======================================================================
    def UpdateQueueStartTime(self,fileInfo):
        conn = psycopg2.connect(database="prometheus_development", user="postgres", password="123", host=sqlserverIp, port=sqlserverPort)
        cur = conn.cursor()
        sql = "UPDATE file_sync_queues SET starttime = now() WHERE id = %s" % (fileInfo[0])
        print sql
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        
    def InsertIntoRes(self,fileInfo):
        conn = psycopg2.connect(database="prometheus_development", user="postgres", password="123", host=sqlserverIp, port=sqlserverPort)
        cur = conn.cursor()
        sql = "INSERT INTO file_sync_results(fileid,starttime,endtime,md5,suffix) VALUES('%s','%s',now(),'%s','%s')" % (fileInfo[1],fileInfo[2],fileInfo[3],fileInfo[4])
        print sql
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    
    def deleteRow(self,queueid):
        conn = psycopg2.connect(database="prometheus_development", user="postgres", password="123", host=sqlserverIp, port=sqlserverPort)
        cur = conn.cursor()
        sql = "DELETE FROM file_sync_queues WHERE id = %s" % (queueid)
        print sql
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()

    def startSyncing(self):
        conn = psycopg2.connect(database="prometheus_development", user="postgres", password="123", host=sqlserverIp, port=sqlserverPort)
        cur = conn.cursor()
        rows = []
        pri = -1
        while len(rows) == 0:
            pri = (pri + 1) % 3
            cur.execute("SELECT * FROM file_sync_queues WHERE priority = %s Limit 1;" % (pri))
            rows = cur.fetchall()
        firstrow = 0
        while len(rows) != 0:
            suc = self.startUploading(rows[firstrow])
            if not suc:
                rows = []
                pri = -1
                while len(rows) == 0:
                    pri = (pri + 1) % 3
                    cur.execute("SELECT * FROM file_sync_queues WHERE priority = %s Limit 2;" % (pri))
                    rows = cur.fetchall()
                    print rows
                if len(rows) == 1:
                    firstrow = 0
                else:
                    firstrow = 1
                continue
            opener = urllib2.build_opener()
            md5 = opener.open(filestatusUrl+rows[firstrow][1]+'.' +rows[firstrow][4]).read()
            if md5 != rows[firstrow][3]:
                print 'md5 not the same'
                continue
            self.InsertIntoRes(rows[firstrow])
            self.deleteRow(rows[firstrow][0]) 
            rows = []
            pri = -1
            while len(rows) == 0:
                pri = (pri + 1) % 3
                cur.execute("SELECT * FROM file_sync_queues WHERE priority = %s Limit 1;" % (pri))
                rows = cur.fetchall()
            firstrow = 0   
        
        conn.commit()
        cur.close()
        conn.close()
        
if __name__ == "__main__":
    sync = Sync()
    #sync.insertTestQueue()
    sync.startSyncing()
    
    #===========================================================================
    # i=0
    # while i < 331:
    #     sync.deleteRow(i)
    #     i+=1
    #===========================================================================