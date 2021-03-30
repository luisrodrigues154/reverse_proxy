#!/bin/python

from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

from requests.exceptions import RequestException

global CACHE
global WORKER

# --------------------------------------

CACHE = ""
WORKER = ""
VERBOSE = True

# --------------------------------------

def printIt(prefix, text):
    global VERBOSE
    if(VERBOSE):
        print("[{}] {}".format(prefix, text)) 


class Cache:
    def __init__(self, invalidate_after):
        # invalidate is used in requests number just for a PoC
        printIt("SETUP", "Initializing Cache")
        self.invalidator = invalidate_after
        self.cache = {}

    def cacheData(self, page, data):
        self.cache[page] = [data, 0]
        printIt("CACHE", "Caching request")
    
    def isCached(self, page):
        if(page in self.cache):
            if(self.cache[page][1] == self.invalidator):
                printIt("CACHE", "Threshold reached")
                self.clear(page)
                return False

            self.cache[page][1] += 1
            printIt("CACHE", "Request found. Using cached response")
            return self.cache[page][0]

        return False
    
    def clear(self, sock_port, page):
        self.cache[page] = ["",0]
        printIt("CACHE", "Request invalidated")


class Worker(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    def do_GET(self):
        self.agnosticProcessor("GET", requests.get)

    def do_HEAD(self):
        self.agnosticProcessor("HEAD", requests.head)
        
    def do_POST(self):
        data = False
        try:
            contentLen = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(contentLen)
        except Exception as err:
            printIt("ERROR", "Parsing post body: "+  str(err))
            return

        self.agnosticProcessor("POST", requests.post, data)

    def do_PUT(self):
        self.agnosticProcessor("PUT", requests.put)
    
    def do_DELETE(self):
        self.agnosticProcessor("DELETE", requests.delete)

    def do_OPTIONS(self):
        self.agnosticProcessor("OPTIONS", requests.options)
    
    def do_PATCH(self, body):
        self.agnosticProcessor("PATCH", requests.patch)
    
    def agnosticProcessor(self, httpMethod, requestMethodHandler, data=False):
        try:
            host = self.headers.get("Host") 
            uri = ""
            if("http" not in host and "https" not in host ):
                uri = "https://" + host

            uri += self.path
            (cliAddr, cliPort) = self.client_address
            printIt("CONN ({})".format(httpMethod), "Connection from {}:{} to {}".format(cliAddr, cliPort, host))
            
            self.modifyHeader(self.headers, "Host", host)
            
            isCached = CACHE.isCached(uri)

            if(not isCached):
                printIt("CACHE", "Cache miss, will relay to server")
                isCached = self.relayRequest(uri, httpMethod, requestMethodHandler, data)
                CACHE.cacheData(uri, isCached)

            self.relayResponse(cliAddr, cliPort, isCached)

        except Exception as err:
            printIt("ERROR", "Agnostic processor error: " + str(err))
        

    def relayResponse(self, cliAddr, cliPort, response):
        global NOT_USE_HEADERS
        printIt("RESPONSE", "Relaying to client {}:{}".format(cliAddr, cliPort))
        
        # modify server header
        response.headers = self.modifyHeader(response.headers, "Server", "localhost:1414")
        # send status code
        self.send_response(response.status_code)
        
        # send headers
        for key in response.headers:
            self.send_header(key,response.headers[key])
        self.end_headers()
        
        # send body
        self.wfile.write(response.content)
        pass

    def relayRequest(self, uri, httpMethod, requestMethodHandler, data=False):
        try:
            printIt("REQUEST", "Relaying ({}) to {}".format(httpMethod, uri))
            if(data):
                response = requestMethodHandler(uri, data=data, headers=self.headers, verify=True)
            else:
                response = requestMethodHandler(uri, headers=self.headers, verify=True)
            return response
        except RequestException as err:
            printIt("ERROR", "Error while relaying request: " + str(err))
        return None
    
    def modifyHeader(self, headers, headerKey, newValue):
        try:
            old = headers[headerKey] 
            del(headers[headerKey])
            headers[headerKey] = newValue
            printIt("DBG", "Header '{}' modified ({} -> {})".format(headerKey, old, newValue))
            return headers
        except KeyError as err:
            printIt("ERROR", "Error while modifying headers: " + str(err))
        return None

def main():
    global CACHE
    CACHE = Cache(4)
    addr = ("127.0.0.1", 1414)
    server = HTTPServer(addr, Worker)
    printIt("SERVER", "Listening on {}".format(addr))
    server.serve_forever()

if __name__ == "__main__":
    main()