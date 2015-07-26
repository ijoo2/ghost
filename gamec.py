#!/usr/bin/env python

import socket
import sys
import signal
import threading
import select
import json
import time
##import lobby

class UnknownDataType(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return 'Unknown data type in request.'

class InvalidRequest(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return 'Invalid request: Incorrect format for data type'

class GameCoordinator(object):
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server = None
        self.BUFFER_SIZE = 1024

        self._threads = []
        self._lobbies = {}
        self._clients = []
        self._client_thread_map = {}

        self.next_id = {'pid': [0], 'lid': [0], 'gid': [0]}
        
    def _start_gc(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print 'SERVER: Launching server host=%s, port=%s' %(self.host, self.port)
            self.server.bind((self.host, self.port)) ##localhost for now
            self.server.listen(5)
        except socket.error, (val, msg):
            if self.server:
                self.server.close()
            print 'Error opening socket: %s' %(msg)
            sys.exit(1)

    def _run(self):
        self._start_gc()
        inp = [self.server]
        while True:
            inqueue, outqueue, exqueue = select.select(inp, [], [])
                                                       
            for s in inqueue:
                if s == self.server:
                    t = threading.Thread()
                    client = self.server.accept() + (self.BUFFER_SIZE,)
                    self._client_thread_map[client] = t

                    t.start()
                    self._threads.append(t)

                    conn, addr, size = client

                    print 'SERVER: Waiting for message...'
                    data = conn.recv(size)
                    print 'SERVER: received %s bytes from %s' % (len(data), addr)

                if not data:
                    break
                resp = self._handle_client_data(data)
                if not resp:
                    break
                sent = conn.send(resp)
                print 'SERVER: sent %s bytes back to %s' % (sent, addr)
            

    def get_lobby(self, lid):
        try:
            lobby = self._lobbies[lid]
        except KeyError:
            lobby = None
        return lobby

    def create_lobby(self, pid=None):
        pass

    def add_client_to_lobby(self, lid=None):
        lobby = self.get_lobby(lid)

    def _handle_client_data(self, data):
        data = json.loads(data)
        if data['type'] == 'auth':
            resp = self._handle_auth(data)
        elif data['type'] == 'message':
            resp = self._handle_message(data)
        elif data['type'] == 'disconnect':
            self._handle_disconnect(data)
        else:
            raise UnknownDataType
        return resp

    def _handle_auth(self, data):
        try:
            pid = data['pid']
            if not pid:
                pid = self._assign_id('pid')
            self._clients.append(pid)
            return json.dumps({'type': 'auth', 'pid': pid, 'timestamp': time.time()})
        except KeyError:
            raise InvalidRequest
            
    def _handle_message(self, data):
        pass

    def _handle_disconnect(self, data):
        

    def _assign_id(self, id_type):
        _id = self.next_id[id_type].pop()
        self.next_id[id_type].append(_id + 1)
        return _id
            
                
def exit_handler(sig, frame):
    sys.exit(0)
    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_handler)
    gc = GameCoordinator()
    gc._run()
