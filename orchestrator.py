#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class Orchestrator(TrawlNet.Orchestrator):
    def downloadTask(self, url, current=None):
        
        proxyServer = Ice.Application.communicator().stringToProxy(sys.argv[1])
        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyServer)
        
        if not downloader:
            raise RuntimeError('Invalid proxy')

        print("Descargando...")
        downloader.addDownloadTask(url)
        print("Descarga realizada con éxito.")
        return "Descarga realizada correctamente."


class Server(Ice.Application):
    def run(self, argv):

        if(len(sys.argv) != 2):
            print("Error en la línea de comandos. El formato es: ./orchestrator.py --Ice.Config=Orchestrator.config <proxyServer>")
            return -1

        broker = self.communicator()
        servant = Orchestrator()

        adapter = broker.createObjectAdapter("OrchestratorAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("orchestrator1"))

        print(proxy, flush=True)
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

            
server = Server()
sys.exit(server.main(sys.argv))
