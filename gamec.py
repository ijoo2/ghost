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

        self._lobbies = {}
        self._clients = []
        self._pid_client_map = {}

        self.next_id = {'pid': [0], 'lid': [0], 'gid': [0]}
        self.queues = {'in': [], 'out': [], 'ex': []}
        
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
        self.queues['in'] = [self.server]
        while True:
            inqueue, outqueue, exqueue = select.select(self.queues['in'], 
                                                       self.queues['out'], 
                                                       self.queues['ex'])
                                                       
            for s in inqueue:
                if s == self.server:
                    client = self.server.accept() + (self.BUFFER_SIZE,)
                    conn, addr, size = client
                    self.queues['in'].append(conn)

                    print 'SERVER: Waiting for message...'
                    data = conn.recv(size)
                    print 'SERVER: received %s bytes from %s' % (len(data), addr)
                    if not data:
                        break
                    resp = self._handle_client_data(data, conn)
                    if not resp:
                        break
                    sent = conn.send(resp)
                    print 'SERVER: sent %s bytes back to %s' % (sent, addr)
                else:
                    data = s.recv(size)
                    if not data:
                        break
                    resp = self._handle_client_data(data, conn)
                    if not resp:
                        break
                    s.send(resp)
            

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

    def _handle_client_data(self, data, client=None):
        data = json.loads(data)
        resp = None
        if data['type'] == 'auth':
            resp = self._handle_auth(data, client)
        elif data['type'] == 'message':
            resp = self._handle_message(data, client)
        elif data['type'] == 'disconnect':
            self._handle_disconnect(data, client)
        else:
            self.queues['ex'].append(json.dumps({'type': 'exception', 'error': UnknownDataType}))
        return resp

    def _handle_auth(self, data, client):
        try:
            pid = data['pid']
            if not pid:
                pid = self._assign_id('pid')
            self._clients.append(pid)
            self._pid_client_map[pid] = client
            return json.dumps({'type': 'auth', 'pid': pid, 'timestamp': time.time()})
        except KeyError:
            self.queues['ex'].append(json.dumps({'type': 'exception', 'error': InvalidRequest}))
            
    def _handle_message(self, data, client):
        pass

    def _handle_disconnect(self, data, client):
        try:
            pid = data['pid']
            self._clients.remove(pid)
            self._free_id('pid', pid)
            self.queues['in'].remove(client)
            self.queues['out'].remove(client)
            self.queues['ex'].remove(client)
        except ValueError:
            pass
            
    def _free_id(self, id_type, _id):
        print 'SERVER: %s %i is now available' %(id_type, _id)
        self.next_id[id_type].append(_id)

    def _assign_id(self, id_type):
        _id = self.next_id[id_type].pop()
        if not self.next_id[id_type]: 
            self.next_id[id_type].append(_id + 1)
        return _id
            
                
def exit_handler(sig, frame):
    sys.exit(0)
    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_handler)
    gc = GameCoordinator()
    gc._run()
