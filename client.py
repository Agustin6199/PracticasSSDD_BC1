#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet


class Client(Ice.Application):
    def run(self, argv):
        if(len(argv) != 3 or len(argv) != 2):
                print("Error en la línea de comandos. El formato es: ./client.py <proxy> <url> ó ./client.py <proxy> ")
                return -1

        proxy = self.communicator().stringToProxy(argv[1])
        orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)

        if not orchestrator:
            raise RuntimeError('Invalid proxy')

        if(len(argv) = 3):
            fileInfoBack = orchestrator.downloadTask(argv[2])
            print("Name: "+ fileInfoBack.name + "   ID: " + fileInfoBack.hash)
	else:
            fileList = orchestrator.getFileList()
            ##MOSTRAR FILELIST

        return 0


sys.exit(Client().main(sys.argv))
