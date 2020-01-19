#!/bin/sh
#

echo "Downloading audio..."
./client.py <proxy> --download <url> \
--Ice.Config=client.config

echo ""
echo "List request..."
./client.py <proxy> --Ice.Config=client.config

echo ""
echo "Init transfer..."
./client.py <proxy> --transfer <file_name> \
--Ice.Config=client.config
