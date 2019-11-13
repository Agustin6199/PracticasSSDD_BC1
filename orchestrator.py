#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('TaskManager.ice')
import Download

class Intermediary(Download.Intermediary):
    def downloadTask(self, url, current=None):
	print(url)
	return "Tarea enviada"


class Server(Ice.Application):
    def run(self, argv):
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
