import json
import time
import argparse
import requests
import re

from datetime import datetime

from http.server import BaseHTTPRequestHandler, HTTPServer
hostName = "127.0.0.1"
serverPort = 4344

# Relevant URLs to access Netatmo REST API
netatmo_oauth2_ep = "https://api.netatmo.com/oauth2/authorize"
netatmo_token_ep = "https://api.netatmo.com/oauth2/token"

auth_data = dict()

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

def get_netatmo_access_token(auth_data,code):
    body = {
        'grant_type' : 'authorization_code',
        'client_id' : auth_data['client_id'],
        'client_secret' : auth_data['client_secret'],
        'code' : code,
        'redirect_uri' : f"http://{hostName}:{serverPort}/redirect",
        'scope' : 'read_station'
        }
    headers = { 'Content-Type':'application/x-www-form-urlencoded' }
    return rest_request(requests.post,netatmo_token_ep,headers,body)

def redirect_to_netatmo(oauth2_url,app_id):
    params = dict()
    params["client_id"] = app_id
    params["redirect_uri"] = "abc"
    params["scope"] = "read_station"
    params["state"] = "xyz"
    headers = dict()
    data = dict()  
    r = requests.post(oauth2_url,params=params,headers=headers,data=data,allow_redirects=True)
    return r

def create_netatmo_oauth_url(base_url,app_id):
    url = f'{base_url}?client_id={app_id}&redirect_uri=http://{hostName}:{serverPort}/redirect&scope=read_station&state=xyz'
    return url

def extract_state_and_code(path,expected_state):
    # Example http://127.0.0.1:4344/redirect?state=xyz&code=23f24d978404c0b165b0350240508786
    pattern = "^.*state=(.+)&code=(.+)$"
    r = re.match(pattern,path)
    if r and r.group(1) == expected_state:
        return r.group(2)
    return None

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_data
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.write("<html><head><title>CoReef - Netatmo OAuth</title></head>")
            self.write("<body>")
            self.write("<p>Redirecting to netatmo:</p>")
            self.write(f"<a href='/netatmo'>{netatmo_oauth2_ep} method='post'</a>")
            self.write("</body></html>")
        elif self.path == "/netatmo":
            url = create_netatmo_oauth_url(netatmo_oauth2_ep,auth_data['client_id'])
            self.send_response(307)
            self.send_header("Location", url)
            self.end_headers()
        elif self.path.startswith("/redirect"):
            code = extract_state_and_code(self.path,"xyz")
            token = get_netatmo_access_token(auth_data,code)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.write("<html><head><title>CoReef - Netatmo OAuth</title></head>")
            self.write("<body>")
            self.write(f"<p>Token is <{token}></p>")
            self.write("</body></html>")            
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.write("<html><head><title>CoReef - Netatmo OAuth</title></head>")
            self.write("<body>")
            self.write(f"<p>Unknown path {self.path}.</p>")
            self.write("<p>For debug purposes no error code 404 is returned :-)")
            self.write("</body></html>")
            # self.send_error(404)

    def write(self,s):
        self.wfile.write(bytes(s,"utf-8"))

def main():
    global auth_data
    # Defining and parsing all the arguments used by this script
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="The file containing all the authentication data (JSON encoded)")
    parser.add_argument("--path", type=str, required=False, help="The location where to store the access token",default=".")
    args = parser.parse_args()
    token_file_path = args.path
    # Load authentication data as a dictionary
    auth_data = read_json_file(args.file)

    print("netatmo_oauth started")
    webServer = HTTPServer((hostName, serverPort), MyServer)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()

if __name__ == '__main__':
    main()
