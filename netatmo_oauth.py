import json
import random
import argparse
import requests
import re
import os.path

from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

config = {
    'host_ip' : '127.0.0.1',
    'host_port' : 4344,
    'oauth2_ep' : "https://api.netatmo.com/oauth2/authorize",
    'token_ep' : "https://api.netatmo.com/oauth2/token"
}

# Reading the content of the given JSON encoded file; returns a dictionary
def read_json_file(filename):
    with open(filename) as f:
        return json.load(f)

# generic REST request (f should be requests.get or requests.post)
def rest_request (f,url,headers,body):
    try:
        response=f(url,headers=headers,data=body)
    except Exception as e:
        return { "success" : False, "content" : repr(e) }
    if response.ok:
        return { "success" : True, "content" : json.loads(response.text) }
    else:
        # TODO maybe there is more in response that should be returned
        return { "success" : False, "content" : response.status_code }

def get_netatmo_access_token(config,code):
    body = {
        'grant_type' : 'authorization_code',
        'client_id' : config['client_id'],
        'client_secret' : config['client_secret'],
        'code' : code,
        'redirect_uri' : f"http://{config['host_ip']}:{config['host_port']}/redirect",
        'scope' : 'read_station'
        }
    headers = { 'Content-Type':'application/x-www-form-urlencoded' }
    return rest_request(requests.post,config['token_ep'],headers,body)

def write_access_token(token,config):
    content = {
        'client_id' : config['client_id'],
        'client_secret' : config['client_secret']
        }
    for k in token.keys():
        content[k] = token[k]
    t = json.dumps(content, indent=2)
    filename = config['token_path']
    t_dir = os.path.dirname(os.path.abspath(filename))
    if not os.path.isdir(t_dir):
        os.makedirs(t_dir)
    with open(filename,'w') as fd:
        fd.write(t)

class OAuth2Handler(BaseHTTPRequestHandler):
    """Derived class that handles the OAuth2 authentication process"""

    def do_GET(self):
        global config
        if self.path == '/':
            self.handle_path_root()
        elif self.path == "/netatmo":
            self.handle_path_netatmo()
        elif self.path.startswith("/redirect"):
            code = self.extract_state_and_code(self.path,config['state'])
            token = get_netatmo_access_token(config,code)
            if token['success']:
                write_access_token(token['content'],config)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.write("<html><head><title>CoReef - Netatmo OAuth</title></head>")
            self.write("<body>")
            self.write(f"<p>Token is <{token}></p>")
            self.write("</body></html>")            
        else:
            self.handle_path_unknown()
            # self.send_error(404)

    def write(self,s):
        self.wfile.write(bytes(s,"utf-8"))

    @staticmethod
    def extract_state_and_code(path,expected_state):
        # Example http://127.0.0.1:4344/redirect?state=xyz&code=23f24d978404c0b165b0350240508786
        pattern = "^.*state=(.+)&code=(.+)$"
        r = re.match(pattern,path)
        if r and r.group(1) == expected_state:
            return r.group(2)
        return None

    def handle_path_root(self):
        global config
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.write("<html><head><title>CoReef - Netatmo OAuth</title></head>")
        self.write("<body>")
        self.write("<p>Redirecting to netatmo:</p>")
        self.write(f"<a href='/netatmo'>{config['oauth2_ep']} method='post'</a>")
        self.write("</body></html>")

    def handle_path_netatmo(self):
        global config
        config['state'] = f'CoReef{str(random.randint(1,100000))}'
        url = f"{config['oauth2_ep']}?client_id={config['client_id']}&redirect_uri=http://{config['host_ip']}:{config['host_port']}/redirect&scope=read_station&state={config['state']}"
        self.send_response(307)
        self.send_header("Location", url)
        self.end_headers()

    def handle_path_unknown(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.write("<html><head><title>CoReef - Netatmo OAuth</title></head>")
        self.write("<body>")
        self.write(f"<p>Unknown path {self.path}.</p>")
        self.write("<p>For debug purposes no error code 404 is returned :-)")
        self.write("</body></html>")

def main():
    global config
    # Defining and parsing all the arguments used by this script
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="The file containing all the authentication data (JSON encoded)")
    parser.add_argument("--path", type=str, required=False, help="The filename to store the access token",default=".")
    args = parser.parse_args()
    config['token_path'] = args.path
    # Load authentication data as a dictionary
    auth_data = read_json_file(args.file)
    config['client_id'] = auth_data['client_id']
    config['client_secret'] = auth_data['client_secret']

    print("netatmo_oauth started")
    webServer = HTTPServer((config['host_ip'], config['host_port']), OAuth2Handler)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()

if __name__ == '__main__':
    main()
