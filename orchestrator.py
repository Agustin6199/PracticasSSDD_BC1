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
                print("Añadido a la lista de ficheros el archivo descargado por otro orchestrator: " + nfile.name)
                self.serverMaster.files[nfile.hash] = nfile.name


class Orchestrator(TrawlNet.Orchestrator):

    def __init__(self, server):
        self.serverMaster = server
    
    def downloadTask(self, url, current=None):
        
        proxyServer = Ice.Application.communicator().stringToProxy(sys.argv[1])
        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyServer)
        
        if not downloader:
            raise RuntimeError('Invalid proxy')

        try:
            inFiles, idFile = self.serverMaster.checkFile(url)
        except Exception:
            print("Se ha producido un error en la descarga: ", url)
            raise TrawlNet.DownloadError("URL no válida")
            
        if(inFiles):
            print("Descargando...")
            fileinfo = downloader.addDownloadTask(url)
            print("Descarga realizada con éxito.")
            self.serverMaster.files[fileinfo.hash] = fileinfo.name
        else:
            print("Archivo descargado previamente.")
            fileinfo = TrawlNet.FileInfo()
            fileinfo.hash = idFile
            fileinfo.name = self.serverMaster.files[idFile]
        return fileinfo

    def getFileList(self, current=None):
        fileList = self.serverMaster.files
        return self.serverMaster.dictToList(fileList)

    def announce(self, prx, current=None):
        self.serverMaster.orchList.append(prx)
        print('Previous Orchestrator: ', prx)
        

class Server(Ice.Application):

    files = {}
    orchList = []
    topicUpdate = None

    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        pr = self.communicator().propertyToProxy(key)
        if pr is None:
            print("property {} not set".format(key))
            return None

        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(pr)

    def run(self, argv):
        if(len(sys.argv) != 2):
            print("Error en la línea de comandos. El formato es: ./orchestrator.py --Ice.Config=Orchestrator.config <proxyServer>")
            return -1

        broker = self.communicator()
        servant = Orchestrator(self)

        adapter = broker.createObjectAdapter("ServerAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("orchestrator1"))

        self.orchList.append(proxy)
        print(proxy, flush=True)
        
        #####
        
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Invalid proxy')
            return 2

        ###SUBSCRIBER SYNC###
        helloServant = OrchestratorEvent(self, proxy)
        subscriber = adapter.addWithUUID(helloServant)

        topic_name = "OrchestratorSync"
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)

        topic.subscribeAndGetPublisher(qos, subscriber)
        print("Waiting events... '{}'".format(subscriber))
	
        ##adapter.activate()

        ###PUBLISHER SYNC###
        
        publisher = topic.getPublisher()
        orch = TrawlNet.OrchestratorEventPrx.uncheckedCast(publisher)
        
        orch.hello(TrawlNet.OrchestratorPrx.checkedCast(proxy))
        
        ###SUBSCRIBER UPDATEFILE###
        
        updatefileServant = UpdateEvent(self)
        subscriberUpdate = adapter.addWithUUID(updatefileServant)
        
        topic_nameUpdate = "UpdateEvents"
        qosUpdate = {}
        try:
            self.topicUpdate = topic_mgr.retrieve(topic_nameUpdate)
        except IceStorm.NoSuchTopic:
            self.topicUpdate = topic_mgr.create(topic_nameUpdate)
            
        self.topicUpdate.subscribeAndGetPublisher(qosUpdate, subscriberUpdate)
        print("Waiting events2... '{}'".format(subscriberUpdate))
        
        adapter.activate()
        
        ###PUBLISHER UPDATEFILE###
        
        
        
        
        
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
