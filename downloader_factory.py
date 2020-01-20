#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import os
import sys
import binascii

import Ice
import IceGrid

Ice.loadSlice('trawlnet.ice')
import TrawlNet

try:
    import youtube_dl
except ImportError:
    print('ERROR: do you have installed youtube-dl library?')
    sys.exit(1)
import IceStorm


APP_DIRECTORY = './'
DOWNLOADS_DIRECTORY = os.path.join(APP_DIRECTORY, 'downloads')


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


def download_mp3(url, destination=DOWNLOADS_DIRECTORY):
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
    filename = filename[filename.rindex('/') - 1:filename.rindex('.') + 1]
 
    return filename, meta['id']


class DownloaderFactoryI(TrawlNet.DownloaderFactory):

    def __init__(self, server):
        self.serverMaster = server

    def create(self, current):
        servant = DownloaderI(self.serverMaster)
        proxy = current.adapter.addWithUUID(servant)
        print('# New downloader #', flush=True)
        
        return TrawlNet.DownloaderPrx.checkedCast(proxy)


class DownloaderI(TrawlNet.Downloader):
    
    def __init__(self, server):
        self.serverMaster = server
    
    def addDownloadTask(self, url, current=None):
        print("Download:", url)
        fileName, fileId = download_mp3(url)
        fileinfo = TrawlNet.FileInfo()
        fileinfo.name = fileName[2:len(fileName)-1]
        fileinfo.hash = fileId
        orch = TrawlNet.UpdateEventPrx.uncheckedCast(self.serverMaster.publisher)
        orch.newFile(fileinfo)
        return fileinfo

    def destroy(self, current):
        try:
            current.adapter.remove(current.id)
            print('DOWNLOADER DESTROYED', flush=True)
        except Exception as e:
            print(e, flush=True)
        
        
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
        properties = broker.getProperties()

        servantDownloader = DownloaderFactoryI(self)

        adapter = broker.createObjectAdapter('DownloaderAdapter')
        downloader_id = properties.getProperty('DownloaderFactoryIdentity')
        proxy = adapter.add(servantDownloader, broker.stringToIdentity(downloader_id))
        
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
