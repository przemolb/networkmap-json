#!/usr/bin/env bash

echo
echo "This script will install the following python 3 libraries using 'pip3':"
echo
sleep 3
cat ./requirements.txt
echo 
echo "(sleeping for 7 seconds to let you CTRL-C it in case you use something else than pip)"
sleep 7

pip3 install --user -r ./requirements.txt