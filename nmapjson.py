#!/usr/bin/env python3

import json
import requests
import sys

environments = {'cnuat':        'https://netmap.uat.corda.network/3FCF6CEB-20BD-4B4F-9C72-1EFE7689D85B/network-map/json/node-infos',
                'cnprod':       'https://netmap.corda.network/ED5D077E-F970-428B-8091-F7FCBDA06F8C/network-map/json/node-infos',
                'daywatch3':    'http://day3.cordaconnect.io:10001/network-map/json/node-infos'}
if len(sys.argv) != 2:
    sys.stderr.write("You need to specify one of the following environments:")
    # print("You need to specify one of the following environments:")
    for key in environments.keys():
        # print(" {}".format(key))
        sys.stderr.write(" {}".format(key))
    sys.exit(1)
    
nm_url = environments[str(sys.argv[1])]
print("URL in use: {}".format(nm_url))
response = requests.get(nm_url)
nmlist = json.loads(response.text)
for item in nmlist:
    print("{},{:>3d},{:<90s},{}:{}".format(\
        item.get('Serial'),
        item.get('Platform Version'),
        item.get('Legal Identities')[0],
        item.get('addresses')[0]['host'],
        item.get('addresses')[0]['port']
    ))