#!/usr/bin/env python

import socket, time
import copy
import random 
import _thread
import signal 
import subprocess 
import os 

global LOAD_BALANCER
global CACHE
global WORKER

RCV_SIZE = 8096
VERBOSE = True

LOAD_BALANCER= ""
CACHE = ""
WORKER = ""

def printIt(prefix, text):
    global VERBOSE
    if(VERBOSE):
        print("[{}] {}".format(prefix, text)) 

class LoadBalancer:
    def __init__(self, n_addr):
        printIt("SETUP", "Initializing load balancer")
        self.addr = []
        for i in range(0, n_addr):
            self.addr.append(("127.0.0.1", 8080+i))
        self.addr_n = n_addr
        self.launchServers()

    def launchServers(self):
        printIt("SETUP", "Launching backend servers")
        for addr in self.addr:
            os.system("python -m http.server --directory www --bind {} {} &".format(addr[0], addr[1]))
            #print(result.stdout)

    def getAddress(self) :
        n = random.randint(0, self.addr_n-1)
        return self.addr[n]

class Cache:
    def __init__(self, invalidate_after):
        # invalidate is used in requests number just for a PoC
        printIt("SETUP", "Initializing Cache")
        self.invalidator = invalidate_after
        self.cache = {}

    def cacheData(self, sock_port, page, data):
        self.cache[page] = [data, 0]
        printIt("CACHE:{}".format(sock_port), "Caching request")
    
    def isCached(self, sock_port, page):
        
        if(page in self.cache):
            if(self.cache[page][1] == self.invalidator):
                printIt("CACHE:{}".format(sock_port), "Threshold reached")
                self.clear(sock_port, page)
                return False

            self.cache[page][1] += 1
            return self.cache[page][0]

        return False
    
    def clear(self, sock_port, page):
        self.cache[page] = ["",0]
        printIt("CACHE:{}".format(sock_port), "Request invalidated")

class PortWorker:
    def __init__(self, addr, port):
        self.port = port
        self.addr = addr
        self.sock_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def recv(self, conn_sock, size):
        data = b""
        while True:
            packet = conn_sock.recv(size)
            if len(packet) < size:
                data += packet
                return data
            time.sleep(0.1)
            data += packet
        
    def spawn(self):
        printIt("INFO", "Trying to spawn socket [{}:{}]".format(self.addr, self.port))
        try:
            self.sock_in.bind((self.addr, self.port))
        except Exception as err:
            printIt("ERROR:{}".format(self.port), str(err))
            return True
        self.sock_in.listen(5)
        return False

    def start(self):
        if(self.spawn()): return
        printIt("INFO", "Listening on {}:{}".format(self.addr, self.port))
        while True:
            (cli_sock, (cli_addr, cli_port)) = self.sock_in.accept()
            printIt("SOCKET:{}".format(self.port), "Connection from {}:{}".format(cli_addr, cli_port))
            _thread.start_new_thread(self.connWorker, (cli_sock, cli_addr, cli_port))

    def connWorker(self, cli_sock, cli_addr, cli_port):
        global RCV_SIZE, CACHE
        req = self.recv(cli_sock, RCV_SIZE)

        in_cache = CACHE.isCached(self.port, req)
        if(in_cache != False):
            resp = in_cache
            printIt("WORKER:{}".format(self.port), "Using cached request")
        else:
            resp = self.forward(req)
            CACHE.cacheData(self.port, req, resp)

        self.response(resp, cli_sock, cli_addr, cli_port)
        cli_sock.close()

    def response(self, data, cli_sock, cli_addr, cli_port):
        if(data == False):
            return
        try:
            trim_start = data.index(b"Server:")
            trim_end = data.find(b"\r\n", trim_start)
            newData = data[:trim_start] + "Server:{}:{}".format(self.addr, self.port).encode() + data[trim_end:]
            printIt("SOCKET:{}".format(self.port), "Relaying RESPONSE to client {}:{}".format(cli_addr, cli_port))
            cli_sock.send(newData)
        except Exception as err:
            printIt("ERROR:{}".format(self.port), str(err))


    def forward(self, data):
        try:
            global LOAD_BALANCER, RCV_SIZE
            addr = LOAD_BALANCER.getAddress()
            
            printIt("SOCKET:{}".format(self.port), "Relaying REQUEST to server {}:{}".format(addr[0], addr[1]))
            self.sock_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock_out.connect(addr)
            trim_start = data.index(b"Host:")
            trim_end = data.find(b"\r\n", trim_start)
            newData = data[:trim_start] + "Host:{}:{}".format(addr[0],addr[1]).encode() + data[trim_end:] 
            
            self.sock_out.sendall(newData)
            time.sleep(0.1)
            response = self.recv(self.sock_out, RCV_SIZE)
            self.sock_out.close()
            return response
        except Exception as err:
            printIt("ERROR:{}".format(self.port), str(err))
            return False

def sigint_handler(sig, frame):
    global WORKER
    print("\n")
    printIt("INFO", "Termination sequence started")
    printIt("SETUP", "Closing WORKER socket")
    WORKER.sock_in.close()
    printIt("SETUP", "Closing WORKER socket")
    printIt("EXITING", "Sequence terminated. Shutting down")
    os.system("pkill python")


def main():
    global LOAD_BALANCER, CACHE, WORKER
    print("\n")
    LOAD_BALANCER = LoadBalancer(4)
    CACHE = Cache(4)
    time.sleep(1)

    printIt("SETUP", "Initializing worker")
    print("\n")
    WORKER = PortWorker("127.0.0.1", 1414)
    signal.signal(signal.SIGINT, sigint_handler)

    printIt("INFO", "Initilization sequence complete ... <Ctrl+c to STOP>")
    WORKER.start()

if __name__ == "__main__":
    main()
    
    
    