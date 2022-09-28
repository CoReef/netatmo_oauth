import json
import time
import argparse
import requests

from datetime import datetime

from http.server import BaseHTTPRequestHandler, HTTPServer
# hostName = "127.0.0.1"
hostName = "0.0.0.0"
serverPort = 4344

# Relevant URLs to access Netatmo REST API
netatmo_auth_ep = "https://api.netatmo.com/oauth2/token"

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

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.write("<html><head><title>CoReef - Netatmo OAuth</title></head>")
            self.write("<body>")
            self.write("<p>Redirecting to netatmo:</p>")
            self.write("</body></html>")
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.write("<html><head><title>CoReef - Netatmo OAuth</title></head>")
            self.write("<body>")
            self.write(f"<p>Received path {self.path} </p>")
            self.write("</body></html>")
            # self.send_error(404)

    def write(self,s):
        self.wfile.write(bytes(s,"utf-8"))

def main():
    # Defining and parsing all the arguments used by this script
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="The file containing all the authentication data (JSON encoded)")
    parser.add_argument("--path", type=str, required=False, help="The location where to store the access token",default=".")
    args = parser.parse_args()
    auth_file = args.file
    token_file_path = args.path

    print("netatmo_oauth started")
    webServer = HTTPServer((hostName, serverPort), MyServer)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()

if __name__ == '__main__':
    main()
