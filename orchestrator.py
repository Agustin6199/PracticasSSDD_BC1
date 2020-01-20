#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet
import IceStorm
try:
    import youtube_dl
except ImportError:
    print('ERROR: do you have installed youtube-dl library?')
    sys.exit(1)


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


class OrchestratorEvent(TrawlNet.OrchestratorEvent):
    
    def __init__(self, server, orch):
        self.serverMaster = server
        self.orchestrator = orch

    def hello(self, prx, current=None):
        if prx!=self.orchestrator:
            print("New Orchestrator: ", prx)
            self.serverMaster.orchList.append(prx)
            prx.announce(TrawlNet.OrchestratorPrx.checkedCast(self.orchestrator))
            
            publisherUpdate = self.serverMaster.topicUpdate.getPublisher()
            orchUpdate = TrawlNet.UpdateEventPrx.uncheckedCast(publisherUpdate)
            filesDict = self.serverMaster.files
            fileList = self.serverMaster.dictToList(filesDict)
            for file in fileList:
                orchUpdate.newFile(file)


class UpdateEvent(TrawlNet.UpdateEvent):   
    
    def __init__(self, server):
        self.serverMaster = server
        
    def newFile(self, nfile, current=None):
        if self.serverMaster:
            if nfile.hash not in self.serverMaster.files:
                print("New file downloaded by another orchestrator: " + nfile.name)
                self.serverMaster.files[nfile.hash] = nfile.name


class Orchestrator(TrawlNet.Orchestrator):
    
    def __init__(self, server):
        self.serverMaster = server
    
    def downloadTask(self, url, current=None):
        
        proxyServer = Ice.Application.communicator().stringToProxy('downloader_factory')
        downloaderFactory = TrawlNet.DownloaderFactoryPrx.checkedCast(proxyServer)
        downloader = downloaderFactory.create()

        if not downloader:
            raise RuntimeError('Invalid proxy')

        try:
            inFiles, idFile = self.serverMaster.checkFile(url)
        except Exception:
            print("An error has occured with the download: ", url)
            raise TrawlNet.DownloadError("Invalid URL")
            
        if(inFiles):
            print("Downloading...")
            fileinfo = downloader.addDownloadTask(url)
            print("Succesful download: ", fileinfo.name)
            self.serverMaster.files[fileinfo.hash] = fileinfo.name
        else:
            print("This file already exists.")
            fileinfo = TrawlNet.FileInfo()
            fileinfo.hash = idFile
            fileinfo.name = self.serverMaster.files[idFile]
            
        downloader.destroy()

        return fileinfo

    def getFileList(self, current=None):
        fileList = self.serverMaster.files
        return self.serverMaster.dictToList(fileList)

    def announce(self, prx, current=None):
        self.serverMaster.orchList.append(prx)
        print('Previous Orchestrator: ', prx)

    def getFile(self, fileName, current=None):
        proxyServer = Ice.Application.communicator().stringToProxy('transfer_factory')
        factory = TrawlNet.TransferFactoryPrx.checkedCast(proxyServer)        
        transfer = factory.create(fileName)
        return TrawlNet.TransferPrx.checkedCast(transfer)
        

class Server(Ice.Application):

    files = {}
    orchList = []
    topicUpdate = None

    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        pr = self.communicator().stringToProxy('YoutubeDownloadsApp.IceStorm/TopicManager')
        if pr is None:
            print("property {} not set".format(key))
            return None
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(pr)

    def run(self, argv):
        if(len(sys.argv) != 1):
            print("Error en la línea de comandos. El formato es: ./orchestrator.py --Ice.Config=orchestrator-node.config")
            return -1

        broker = self.communicator()
        properties = broker.getProperties()
        servant = Orchestrator(self)

        adapter = broker.createObjectAdapter('OrchestratorAdapter')
        indirect_proxy = adapter.addWithUUID(servant)
        identity_ = indirect_proxy.ice_getIdentity()
        proxy = adapter.createDirectProxy(identity_)

        self.orchList.append(proxy)
        print(proxy, flush=True)
        
        #####
        
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Invalid proxy')
            return 2

        ###SUBSCRIBER SYNC###
        
        helloServant = OrchestratorEvent(self, proxy)
        indirect_subscriber = adapter.addWithUUID(helloServant)
        object_identity = indirect_subscriber.ice_getIdentity()
        subscriber = adapter.createDirectProxy(object_identity)
        topic_name = "OrchestratorSync"
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)
        topic.subscribeAndGetPublisher(qos, subscriber)
        print("Waiting new events in OchestratorSync...")
        
        ###SUBSCRIBER UPDATEFILE###
        
        updatefileServant = UpdateEvent(self)
        indirect_subscriberUpdate = adapter.addWithUUID(updatefileServant)
        object_identityUpdate = indirect_subscriberUpdate.ice_getIdentity()
        subscriberUpdate = adapter.createDirectProxy(object_identityUpdate)
        topic_nameUpdate = "UpdateEvents"
        qosUpdate = {}
        try:
            self.topicUpdate = topic_mgr.retrieve(topic_nameUpdate)
        except IceStorm.NoSuchTopic:
            self.topicUpdate = topic_mgr.create(topic_nameUpdate)
        self.topicUpdate.subscribeAndGetPublisher(qosUpdate, subscriberUpdate)
        print("Waiting new events in UpdateEvents...")
        
        adapter.activate()
        
        ###PUBLISHER SYNC###
        
        publisher = topic.getPublisher()
        orch = TrawlNet.OrchestratorEventPrx.uncheckedCast(publisher)
        orch.hello(TrawlNet.OrchestratorPrx.checkedCast(proxy))
        
        #####
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        topic.unsubscribe(subscriber)

        return 0

    def dictToList(self, dict):
        retVal=[]
        for hash, name in dict.items():
            file=TrawlNet.FileInfo()
            file.hash = hash
            file.name = name
            retVal.append(file)
        return retVal

    def checkFile(self, url):
        ydl_opts = {}
        ydl_opts.update(_YOUTUBEDL_OPTS_)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download = False)
        
        if meta['id'] not in self.files:
            return True, None
        
        return False, meta['id']
        
            
server = Server()
sys.exit(server.main(sys.argv))
