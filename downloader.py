#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class Downloader(TrawlNet.Downloader):
    def addDownloadTask(self, url, current=None):
        print("Tarea descargada:", url)
        return "Tarea enviada a Downloader correctamente: "
        
        
class Server(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        servant = Downloader()
        
        adapter = broker.createObjectAdapter("DownloaderAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("downloader1"))
        
        print(proxy, flush=True)
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
        return 0
        
        
server = Server()
sys.exit(server.main(sys.argv))
