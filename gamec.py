from socket import socket
import sys
## from lobby import Lobby


class GameCoordinator(socket):
    def __init__(self):
        super(GameCoordinator, self).__init__()
        self._lobbies = {}
        self.start_gc()

    def start_gc(self):
        server_address = ('localhost',12345)
        print ('SERVER: Launching server server_address=localhost, port=12345')
        self.bind(server_address) ##localhost for now

        while True:
            print 'SERVER: Waiting for message...'
            data, server_address = self.recvfrom(4096)
            print 'SERVER: received %s bytes from %s' % (len(data), server_address)

            if data:
                sent = socket.sendto(data, server_address)
                print 'SERVER: sent %s bytes back to %s' % (sent, server_address)

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
