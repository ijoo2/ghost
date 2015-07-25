#!/usr/bin/env python

import socket
import sys
import signal
import threading
import select
import json
import time
##import lobby
##json.dumps({'data':{'type': 'message_to_player', 'content': 'hello'}})

class Client(object):
    def __init__(self, name, pid=None, sock=None, nm=None):
        self.name = name
        self.pid = pid
        self.char = ''
        self.nm = nm
        self._connect_gc('localhost', 12345) # localhost for now

    def _connect_gc(self, host, port):
        self.gc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', 12345)
        try:
            self.gc.connect((host, port))
        except:
            print "CLIENT: Failed to connect to host=%s port=%i" %(host, port)

        print 'CLIENT: Client name=%s' %(self.name)

        try:
            # Send data
            print 'CLIENT: sending hello'
            data = self._get_auth_data()
            sent = self.gc.send(data)

            # Receive response
            print 'CLIENT: waiting to receive'
            data = self.gc.recv(4096)
            print 'CLIENT: received %s' % data

        finally:
            print 'CLIENT: closing socket'
            self._close_gc()

    def _close_gc(self):
        if self.gc:
            self.gc.close()

    # Close/cleanup network connections
    def disconnect(self):
        self._close_gc()
        
    def _send_char(self):
        self.nm.push({'pid': self.pid, 'data': self.char})

    def _join_lobby(self, lid=None):
        self.gc.add_client_to_lobby(self.pid, lid)

    def _create_lobby(self):
        pass

    def _get_auth_data(self):
        return json.dumps({'type': 'auth', 'pid': self.pid, 'timestamp': time.time()})
    
    def __str__(self):
        return '%s (%s)' %(self.name, self.pid)

if __name__ == '__main__':
    client = Client('Test')
