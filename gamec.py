from socket import socket
## from lobby import Lobby

class GameCoordinator(socket):
    def __init__(self):
        super(GameCoordinator, self).__init__()
        self._lobbies = {}
        self.start_gc()

    def start_gc(self):
        self.bind('localhost', 12345) ##localhost for now

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
