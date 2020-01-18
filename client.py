#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet
import os
import binascii

DOWNLOADS_DIRECTORY="./"

class Client(Ice.Application):
    
    orchestrator = None 

    def transfer_request(self, file_name):
        remote_EOF = False
        BLOCK_SIZE = 1024
        transfer = None

        try:
            transfer = self.orchestrator.getFile(file_name)
        except TrawlNet.TransferError as e:
            print(e.reason)
            return 1

        with open(os.path.join(DOWNLOADS_DIRECTORY, file_name), 'wb') as file_:
            remote_EOF = False
            while not remote_EOF:
                data = transfer.recv(BLOCK_SIZE)
                if len(data) > 1:
                    data = data[1:]
                data = binascii.a2b_base64(data)
                remote_EOF = len(data) < BLOCK_SIZE
                if data:
                    file_.write(data)
            transfer.close()

        transfer.destroy()
        print('Transfer finished!')

    def run(self, argv):
        if(len(argv) != 3 and len(argv) != 2):
                print("Error - The format is: ./client.py <proxy> <url> ó ./client.py <proxy> ")
                return -1

        proxy = self.communicator().stringToProxy(argv[1])
        self.orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)

        if not self.orchestrator:
            raise RuntimeError('Invalid proxy')

        if(len(argv[2]) > 0):
            if(argv[2].find("www.")!=-1 or argv[2].find("https://")!=-1):
                try:
                    fileInfoBack = self.orchestrator.downloadTask(argv[2])
                    print("Name: "+ fileInfoBack.name + "   ID: " + fileInfoBack.hash)
                except TrawlNet.DownloadError as e:
                    print(e.reason)
            else:
                self.transfer_request(argv[2])
                
        else:
            files = self.orchestrator.getFileList()
            if(len(files)==0):
                print("There is not any downloaded file.")
            else:
                print("File list:")
                for file in files:
                    print("Name: "+ file.name + "   ID: " + file.hash)

        return 0


sys.exit(Client().main(sys.argv))
