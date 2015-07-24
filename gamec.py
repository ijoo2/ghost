#!/usr/bin/env python

import socket
import sys
import signal
## from lobby import Lobby


class GameCoordinator(socket.socket):
    def __init__(self):
        super(GameCoordinator, self).__init__(socket.AF_INET, socket.SOCK_STREAM)
        self._lobbies = {}
        self.start_gc()

    def start_gc(self):
        server_address = ('localhost',12345)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print 'SERVER: Launching server server_address=%s, port=%s' %server_address
        self.bind(server_address) ##localhost for now
        self.listen(1)

        while True:
            conn, addr = self.accept()
            while True:
                print 'SERVER: Waiting for message...'
                data = conn.recv(4096)
                print 'SERVER: received %s bytes from %s' % (len(data), addr)

                if not data:
                    break
                sent = conn.send(data)
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

def exit_handler(sig, frame):
    sys.exit(0)
    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_handler)
    gc = GameCoordinator()
