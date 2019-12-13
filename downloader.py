#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
import os
Ice.loadSlice('trawlnet.ice')
import TrawlNet
try:
    import youtube_dl
except ImportError:
    print('ERROR: do you have installed youtube-dl library?')
    sys.exit(1)
import IceStorm


class NullLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

_YOUTUBEDL_OPTS_ = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': NullLogger()
}

def download_mp3(url, destination='./'):
    '''
    Synchronous download from YouTube
    '''
    options = {}
    task_status = {}
    def progress_hook(status):
        task_status.update(status)
    options.update(_YOUTUBEDL_OPTS_)
    options['progress_hooks'] = [progress_hook]
    options['outtmpl'] = os.path.join(destination, '%(title)s.%(ext)s')
    with youtube_dl.YoutubeDL(options) as youtube:
        youtube.download([url])
        meta = youtube.extract_info(url, download=False)
    filename = task_status['filename']
    # BUG: filename extension is wrong, it must be mp3
    filename = filename[:filename.rindex('.') + 1]
 
    return filename, meta['id']


class Downloader(TrawlNet.Downloader):
    
    def __init__(self, server):
        self.serverMaster = server
    
    def addDownloadTask(self, url, current=None):
        print("Descargando tarea:", url)
        fileName, fileId = download_mp3(url)
        ##print("Nombre: " + fileName[2:len(fileName)-1] + "  ID: " + fileId)
        fileinfo = TrawlNet.FileInfo()
        fileinfo.name = fileName[2:len(fileName)-1]
        fileinfo.hash = fileId
        orch = TrawlNet.UpdateEventPrx.uncheckedCast(self.serverMaster.publisher)
        orch.newFile(fileinfo)
        return fileinfo
        
        
class Server(Ice.Application):
    
    publisher = None
    
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print ("property {} not set".format(key))
            return None
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, argv):
        broker = self.communicator()
        servant = Downloader(self)
        
        adapter = broker.createObjectAdapter("ServerAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("downloader1"))
        
        print(proxy, flush=True)
        
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print ('Invalid porxy')
            return 2
            
        topic_name = "UpdateEvents"
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)
            
        self.publisher = topic.getPublisher()
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
        return 0
        
        
server = Server()
server.main(sys.argv)
sys.exit()
