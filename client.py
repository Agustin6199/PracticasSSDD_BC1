#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet


class Client(Ice.Application):
    
    def run(self, argv):
        if(len(argv) != 3 and len(argv) != 2):
                print("Error - The format is: ./client.py <proxy> <url> ó ./client.py <proxy> ")
                return -1

        proxy = self.communicator().stringToProxy(argv[1])
        orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)

        if not orchestrator:
            raise RuntimeError('Invalid proxy')

        if(len(argv[2]) > 0):
            try:
                fileInfoBack = orchestrator.downloadTask(argv[2])
                print("Name: "+ fileInfoBack.name + "   ID: " + fileInfoBack.hash)
            except TrawlNet.DownloadError as e:
                print(e.reason)
        else:
            files = orchestrator.getFileList()
            if(len(files)==0):
                print("There is not any downloaded file.")
            else:
                print("File list:")
                for file in files:
                    print("Name: "+ file.name + "   ID: " + file.hash)

        return 0


sys.exit(Client().main(sys.argv))
