#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
import IceStorm
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class FileUpdatesEventI(Trawlnet.UpdateEvent):
    orchestrator = None
    def newFile(self, fileInfo, current=None):
        if self.orchestrator:
            if fileInfo.hash not in self.orchestrator.files:
                self.orchestrator.files[fileInfo.hash]=fileInfo.name


class OrchestratorI(TrawlNet.Orchestrator):
    def downloadTask(self, url, current=None):
        
        proxyServer = Ice.Application.communicator().stringToProxy(sys.argv[1])
        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyServer)
        
        if not downloader:
            raise RuntimeError('Invalid proxy')

        print("Descargando...")
        downloader.addDownloadTask(url)
        print("Descarga realizada con éxito.")
        return "Descarga realizada correctamente."
        
    def getFileList(self, current=None):
        
        print("Enviando la lista de ficheros descargados")
        return listaFicheros
        
    def announce(self, other):
        


class Server(Ice.Application):
        def run(self, argv):
            if(len(sys.argv) != 2):
                print("Error en la línea de comandos. El formato es: ./orchestrator.py --Ice.Config=Orchestrator.config <proxyServer>")
                return -1

        broker = self.communicator()
        servant = OrchestratorI()

        adapter = broker.createObjectAdapter("OrchestratorAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("orchestrator1"))

        print(proxy, flush=True)
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

class Publisher(Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print "property", key, "not set"
            return None
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
        
    def run(self, argv):
        
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print ': invalid proxy'
            return 2
        topic_name = "UpdateEvents"
        try:
            topic = topic_mgr_retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            print "no such topic found, creating"
            topic = topic_mgr.create(topic_name)
        publisher = topic.getPublisher()
        printer = Example.PrinterPrx.uncheckedCast(publisher)
        
        return 0
        
            
server = Server()
sys.exit(server.main(sys.argv))
