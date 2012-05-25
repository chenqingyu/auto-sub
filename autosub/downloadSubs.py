# Autosub Db.py - http://code.google.com/p/auto-sub/
#
# The Autosub downloadSubs module
#

import logging

import autosub
import os

from autosub.Db import lastDown
from autosub.Bierdopje import API
import autosub.notify as notify

log = logging.getLogger('thelogger')

class downloadSubs():
    """
    Check the TODOWNLOADQUEUE and try to download everything in it.
    """
    def run(self):
        if len(autosub.TODOWNLOADQUEUE) > 0:
            if not autosub.Helpers.checkAPICalls():
                log.error("downloadSubs: out of api calls")
                return True
            
            toDelete_toDownloadQueue = []
            log.debug("downloadSubs: Something in downloadqueue, Starting downloadSubs")
            if autosub.TODOWNLOADQUEUELOCK or autosub.WANTEDQUEUELOCK:
                log.debug("downloadSubs: Exiting, another threat is using the queues")
                return False
            else:
                autosub.TODOWNLOADQUEUELOCK = True
                autosub.WANTEDQUEUELOCK = True
            for index, downloadItem in enumerate(autosub.TODOWNLOADQUEUE):
                if 'destinationFileLocationOnDisk' in downloadItem.keys() and 'downloadLink' in downloadItem.keys():
                    destsrt = downloadItem['destinationFileLocationOnDisk']
                    downloadLink = downloadItem['downloadLink']

                    try:
                        bierdopjeapi = API(downloadLink)
                        log.debug("downloadSubs: Trying to download the following subtitle %s" %downloadLink)
                    except:
                        log.error("downloadSubs: The server returned an error for request %s" % downloadLink)
                        continue
                    
                    destdir = os.path.split(destsrt)[0]
                    if not os.path.exists(destdir):
                        toDelete_toDownloadQueue.append(index)
                        log.debug("checkSubs: no destination directory %s" %destdir)
                        continue
                    elif not os.path.lexists(destdir):
                        log.debug("checkSubs: no destination directory %s" %destdir)
                        toDelete_toDownloadQueue.append(index)
                        continue
                    
                    try:
                        if bierdopjeapi.resp:
                            open(destsrt, 'wb').write(bierdopjeapi.resp.read())
                        bierdopjeapi.close()
                    except:
                        log.error("downloadSubs: Error while writing subtitle file. Check if the destination is writeable! Destination: %s" % destsrt)
                        toDelete_toDownloadQueue.append(index)
                        continue

                    log.info("downloadSubs: DOWNLOADED: %s" % destsrt)
                    toDelete_toDownloadQueue.append(index)
                    
                    lastDown().setlastDown(dict = autosub.TODOWNLOADQUEUE[index])
                    
                    notify.notify(autosub.TODOWNLOADQUEUE[index]['downlang'], destsrt, downloadItem["originalFileLocationOnDisk"])

                    if autosub.POSTPROCESSCMD:
                        postprocesscmdconstructed = autosub.POSTPROCESSCMD + ' "' + downloadItem["destinationFileLocationOnDisk"] + '" "' + downloadItem["originalFileLocationOnDisk"] + '"'
                        log.debug("downloadSubs: Postprocess: running %s" % postprocesscmdconstructed)
                        log.info("downloadSubs: Running PostProcess")
                        postprocessoutput, postprocesserr = autosub.Helpers.RunCmd(postprocesscmdconstructed)
                        if postprocesserr:
                            log.error("downloadSubs: PostProcess: %s" % postprocesserr)
                        log.debug("downloadSubs: PostProcess Output:% s" % postprocessoutput)
                    
                    #toDownloadQueue.remove(downloadItem)
                else:
                    log.error("downloadSub: No downloadLink or locationOnDisk found at downloadItem, skipping")
                    continue

            i = len(toDelete_toDownloadQueue) - 1
            while i >= 0:
                log.debug("downloadSubs: Removed item from the toDownloadQueue at index %s" % toDelete_toDownloadQueue[i])
                autosub.TODOWNLOADQUEUE.pop(toDelete_toDownloadQueue[i])
                i = i - 1
            autosub.TODOWNLOADQUEUELOCK = False
            autosub.WANTEDQUEUELOCK = False
        return True
