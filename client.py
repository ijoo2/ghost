from socket import socket

class Client(object):
    def __init__(self, pid, name, sock=None, nm=None):
        self.pid = pid
        self.name = name
        self.char = ''
        self.nm = nm
        self.gc = self._connect_gc('localhost', 12345) ##localhost for now

    def _connect_gc(self, host, port):
        self.gc = socket()
        self.gc.connect((host, port))

    def _close_gc(self):
        if self.sock:
            self.sock.close()

    ## Close/cleanup network connections
    def disconnect(self):
        self._close_gc()
        
    def _send_char(self):
        self.nm.push({'pid': self.pid, 'data': self.char})

    def _join_lobby(self, lid=None):
        self.gc.add_client_to_lobby(self.pid, lid)

    def _create_lobby(self):
        pass

    def __str__(self):
        return '%s (%s)' %(self.name, self.pid)
