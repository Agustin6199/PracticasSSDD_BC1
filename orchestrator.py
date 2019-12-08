#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet
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


class Orchestrator(TrawlNet.Orchestrator):

    serverMaster = None

    def __init__(self, server):
        self.serverMaster = server
    
    def downloadTask(self, url, current=None):
        
        proxyServer = Ice.Application.communicator().stringToProxy(sys.argv[1])
        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyServer)
        
        if not downloader:
            raise RuntimeError('Invalid proxy')

        try:
            inFiles, idFile = self.serverMaster.checkFile(url)
        except:
            fileinfo = TrawlNet.FileInfo()
            fileinfo.name = 'Error'
            fileinfo.hash = '-1'
            return fileinfo
            
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
        fileList = self.serverMaster.getFiles()
        return fileList


##class filesUpdatesEventI(TrawlNet.UpdateEvent):
    
    
class Server(Ice.Application):

    files = {}

    def run(self, argv):
        if(len(sys.argv) != 2):
            print("Error en la línea de comandos. El formato es: ./orchestrator.py --Ice.Config=Orchestrator.config <proxyServer>")
            return -1

        broker = self.communicator()
        servant = Orchestrator(self)

        adapter = broker.createObjectAdapter("OrchestratorAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("orchestrator1"))

        print(proxy, flush=True)
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

    def checkFile(self, url):
        ydl_opts = {}
        ydl_opts.update(_YOUTUBEDL_OPTS_)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download = False)
        
        if meta['id'] not in self.files:
            return True, None
        
        return False, meta['id']
        
    def getFiles(self):
        return self.files
       
            
server = Server()
sys.exit(server.main(sys.argv))
