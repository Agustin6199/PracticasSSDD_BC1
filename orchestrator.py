#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('TaskManager.ice')
import Download

class Intermediary(Download.Intermediary):
    def downloadTask(self, url, current=None):
        
        proxyServer = Ice.Application.communicator().stringToProxy(sys.argv[1])
        downloader = Download.DownloaderPrx.checkedCast(proxyServer)
        
        if not downloader:
            raise RuntimeError('Invalid proxy')

        msgBack = downloader.addDownloadTask(url)
        print(msgBack, url)

        return "Tarea enviada correctamente"


class Server(Ice.Application):
    def run(self, argv):

        if(len(sys.argv) != 2):
            print("Error en la línea de comandos. El formato es: ./orchestrator.py --Ice.Config=Orchestrator.config <proxyServer>")
            return -1

        broker = self.communicator()
        servant = Intermediary()

        adapter = broker.createObjectAdapter("IntermediaryAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("intermediary1"))

        print(proxy, flush=True)
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

            
server = Server()
sys.exit(server.main(sys.argv))
