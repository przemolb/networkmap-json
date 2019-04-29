#!/usr/bin/env python3

import sys

try:
    import json
    import os
    import requests
    from flask import Flask, Response, redirect, render_template, request, url_for, send_file
    from flask_table import Table, Col
    # from jinja2.nodes import Output
    import configparser
    from io import StringIO, BytesIO
    import csv
    import datetime
    import webbrowser
    import re
except ImportError as error:
    print("\n\nMissing python 3 library: '{0}' - please install it with i.e. 'pip3 install {0}'\n\n".format(error.name))
    sys.exit(1)

tab_not_opened = True
class Envs:
    
    def readIniFile(self):
        self.config_file_name = os.path.splitext(__file__)[0] + '.ini'
        if not os.path.exists(self.config_file_name):
            print("\n\nERROR: missing config file: '{0}'\n\n".format(self.config_file_name))
            sys.exit(2)
        else:
            self.config.read(self.config_file_name) # base name + 'ini'

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.readIniFile()
        self.environments = self.config._sections
        for section in self.config.sections():
            keys = self.config.options(section)

    def rereadIniFile(self):
        self.readIniFile()
    
    def getEnvironmentsList(self):
        self.envList = []
        for env in self.environments.items():
            self.envList.append(env[0])
        return self.envList
        
    def getUrlForEnvironment(self, envname):
        return self.environments[envname]['url']

    def getEnvDescription(self, envname):
        return self.environments[envname]['description']
        
class ItemTable(Table):
    serial = Col('Serial')
    platform_version = Col('Platform version', column_html_attrs={'align': 'right'},)
    legal_identity = Col('Legal Identity')
    host = Col('Host')
    port = Col('Port')

def help():
    return render_template("help.html", environments=environments.getEnvironmentsList())

app = Flask(__name__)
app.add_url_rule('/', 'help', help)
app.register_error_handler(404, lambda x: help())
if tab_not_opened:
    # global tab_not_opened
    webbrowser.open_new_tab("http://127.0.0.1:5000/")
    tab_not_opened = False


@app.route('/')
def reroute_to_help():
    return redirect(url_for('help'))

@app.route('/env/<envname>')
def env(envname):
    environments.rereadIniFile()
    if envname not in environments.getEnvironmentsList():
        return redirect(url_for('help'))
    else:
        rows = list()
        nwm_url = environments.getUrlForEnvironment(envname)
        try:
            response = requests.get(nwm_url, timeout=5)
        except requests.exceptions.Timeout:
            rows.append('ERROR: Timeout')
            no_of_servers = 0
            description='Failed to establish connection: timeout while connecting to "' + envname + '"'
        except requests.exceptions.ConnectionError:
            rows.append('ERROR: ConnectionError')
            no_of_servers = 0
            description='Failed to establish connection: url of "' + envname + '" not known'
        else:
            nwmlist = json.loads(response.text)
            for item in nwmlist:
                rows.append(dict(\
                    serial=str(item.get('Serial')),
                    platform_version=str(item.get('Platform Version')),
                    legal_identity=str((item.get('Legal Identities')[0]).get('Name')),
                    host=str(item.get('addresses')[0]['host']),
                    port=str(item.get('addresses')[0]['port'])
                    ))
            no_of_servers = len(rows)
            description=environments.getEnvDescription(envname)
    return render_template("main.html", rows=rows, env=envname, environments=environments.getEnvironmentsList(), no_of_servers=no_of_servers, description=description)

def read_all_servers(envname):
    environments.rereadIniFile()
    if envname not in environments.getEnvironmentsList():
        return redirect(url_for('help'))
    else:
        rows = list()
        nwm_url = environments.getUrlForEnvironment(envname)
        try:
            response = requests.get(nwm_url, timeout=5)
        except requests.exceptions.Timeout:
            rows.append('ERROR: Timeout')
            error_message='Failed to establish connection: timeout while connecting to "' + envname + '"'
        except requests.exceptions.ConnectionError:
            rows.append('ERROR: ConnectionError')
            no_of_servers = 0
            error_message='Failed to establish connection: url of "' + envname + '" not known'
        else:
            nwmlist = json.loads(response.text)
            return nwmlist

@app.route('/env/<envname>/csv')
def env_csv(envname):
    nwmlist = read_all_servers(envname)
    csv_output_text = StringIO()
    # writer = csv.writer(csv_output_text, dialect='excel', delimiter=',')
    writer = csv.writer(csv_output_text)
    writer.writerow(['Serial', 'Platform Version', 'O', 'L', 'C', 'OU', 'CN', 'S', 'Host', 'Port'])
    for item in nwmlist:
        LE=str((item.get('Legal Identities')[0]).get('Name'))
        O =re.search('O=(.*?),' , LE)
        L =re.search('L=(.*?),' , LE)
        C =re.search('C=(.*)'   , LE)
        OU=re.search('OU=(.*?),', LE)
        CN=re.search('CN=(.*?),', LE)
        S =re.search('S=(.*?),' , LE)
        if O:
            O_output=O.group(1)
        else:
            O_output=''
        if L:
            L_output=L.group(1)
        else:
            L_output=''
        if C:            
            C_output=C.group(1)
        else:
            C_output=''
        if OU:
            OU_output=OU.group(1)
        else:
            OU_output=''
        if CN:
            CN_output=CN.group(1)
        else:
            CN_output=''
        if S:
            S_output=S.group(1)
        else:
            S_output=''
        writer.writerow([
            str(item.get('Serial')),
            str(item.get('Platform Version')),
            O_output,
            L_output,
            C_output,
            OU_output,
            CN_output,
            S_output,
            str(item.get('addresses')[0]['host']),
            str(item.get('addresses')[0]['port'])
    ])
    csv_output_binary = BytesIO()
    csv_output_binary.write(csv_output_text.getvalue().encode('utf-8'))
    csv_output_binary.seek(0)
    csv_output_text.close()
    date_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return send_file(csv_output_binary, as_attachment=True, attachment_filename="{}-{}.csv".format(envname,date_time), mimetype='text/csv')

# taken from https://stackoverflow.com/questions/23112316/using-flask-how-do-i-modify-the-cache-control-header-for-all-output/23115561#23115561
@app.after_request
def add_header(response):
    # force web browsers not to cache it
    response.cache_control.max_age = 0
    return response    

if __name__ == '__main__':
    environments = Envs()
    app.run(debug=True, port=5000, use_reloader=False) #run app in debug mode on port 5000

