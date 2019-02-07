#!/usr/bin/env python3

import sys

try:
    import json
    import os
    import requests
    from flask import Flask, Response, redirect, render_template, request, url_for
    from flask_table import Table, Col
    from jinja2.nodes import Output
    import configparser
except ImportError as error:
    print("\n\nMissing python 3 library: '{0}' - please install it with i.e. 'pip3 install {0}'\n\n".format(error.name))
    sys.exit(1)


environments = {}

class ItemTable(Table):
    serial = Col('Serial')
    platform_version = Col('Platform version', column_html_attrs={'align': 'right'},)
    legal_identity = Col('Legal Identity')
    host = Col('Host')
    port = Col('Port')

def read_environments():
    environments.clear() # you can update the ini file while running this app
    config = configparser.ConfigParser()
    config.read(os.path.splitext(__file__)[0] + '.ini') # base name + 'ini'
    for section in config.sections():
        environments[section] = config[section]['url']

def build_help_output():
    read_environments()
    help_output = dict()
    help_output = ['Click one of the following environments: ']
    for key, _ in environments.items():
        help_output.append("<a href={}>{}</a> ".format(request.url_root + 'env/' + key, key))
    help_output += '<p>'
    return help_output

def help():
    return render_template("help.html", environments=environments)

app = Flask(__name__)
app.add_url_rule('/', 'help', help)
app.register_error_handler(404, lambda x: help())

@app.route('/')
def reroute_to_help():
    return redirect(url_for('help'))

@app.route('/env/<envname>')
def env(envname):
    read_environments()
    if envname not in environments:
        return redirect(url_for('help'))
    else:
        rows = list()
        # output = build_help_output()
        nwm_url = environments[envname]
        try:
            response = requests.get(nwm_url, timeout=5)
        except requests.exceptions.Timeout:
            rows.append('ERROR: Timeout')
        except requests.exceptions.ConnectionError:
            rows.append('ERROR: ConnectionError')
        else:
            nwmlist = json.loads(response.text)
            for item in nwmlist:
                rows.append(dict(\
                    serial=str(item.get('Serial')),
                    platform_version=str(item.get('Platform Version')),
                    legal_identity=str(item.get('Legal Identities')[0]),
                    host=str(item.get('addresses')[0]['host']),
                    port=str(item.get('addresses')[0]['port'])
                    ))
            no_of_servers = len(rows)
    return render_template("main.html", rows=rows, environments=environments, no_of_servers=no_of_servers)

if __name__ == '__main__':
    read_environments()
    app.run(debug=True, port=5000) #run app in debug mode on port 5000
