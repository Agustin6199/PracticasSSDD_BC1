#!/bin/sh

PROXY=$(tempfile)

./downloader.py --Ice.Config=Downloader.config>$PROXY &

sleep .5

./orchestrator.py --Ice.Config=Orchestrator.config "$(cat $PROXY)"

