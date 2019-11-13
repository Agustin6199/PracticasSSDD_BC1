#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('TaskManager.ice')
import Download


class Client(Ice.Application):
    def run(self, argv):
	
	if(len(argv) != 3)
		print("Error en la línea de comandos. El formato es: ./client.py <proxy> <url>")
		return -1

        proxy = self.communicator().stringToProxy(argv[1])
        intermediary = Download.IntermediaryPrx.checkedCast(proxy)

        if not intermediary:
            raise RuntimeError('Invalid proxy')

        msgBack = intermediary.downloadTask(argv[2])
	print(msgBack)
	
        return 0


sys.exit(Client().main(sys.argv))
