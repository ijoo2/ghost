#!/usr/bin/env python

import socket
import sys
import signal
import select
import json
import time
import struct
# import lobby


# If the server responds with two objects really quickly, we only want to read one at a time.
def recv_one(sock):
    lengthbuf = recv_all(sock, 4)  # Read 4 bytes to get the length.
    length, = struct.unpack('!I', lengthbuf)
    return recv_all(sock, length)  # Read length number of bytes.


def recv_all(sock, size):
    buf = b''
    while size:
        newbuf = sock.recv(size)
        if not newbuf:
            return None
        buf += newbuf
        size -= len(newbuf)
    return buf


def prompt():
    sys.stdout.write('\r[You]: ')
    sys.stdout.flush()


def display_msg(msg, user):
    sys.stdout.write('\r[%s]: %s' % ((user.strip('\n') or 'Unknown User'), msg))
    sys.stdout.flush()


class UnknownCommand(Exception):
    def __init__(self, command):
        self.command = command

    def __str__(self):
        print 'Unknown Command "{}"'.format(self.command)


class Client(object):
    def __init__(self, name, pid=None, sock=None, nm=None):
        self.name = name
        self.pid = pid
        self.nm = nm
        self.gc = None
        signal.signal(signal.SIGINT, self.exit_handler)
        self.queues = {'in': [], 'out': [], 'ex': []}
        self.peer_pid_name_map = {}

    def _run(self):
        self._connect_gc('localhost', 12345)
        print ("Use /help for a list of commands.")
        prompt()
        while True:
            inqueue, outqueue, exqueue = select.select([sys.stdin, self.gc],
                                                       [],
                                                       [], .3)  # This definitely doesn't work on windows.
            for s in inqueue:
                if s == self.gc:
                    # print 'CLIENT: waiting to receive'
                    data = recv_one(s)
                    if data:
                        # print 'CLIENT: received %s' % data
                        self._handle_response(data)
                    else:
                        sys.exit()
                else:
                    self._parse_input(s.readline())
                    prompt()

    def _connect_gc(self, host, port):
        self.gc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gc.settimeout(2)
        server_address = (host, port)
        try:
            self.gc.connect(server_address)
            self.queues['in'].append(self.gc)
        except:
            print "CLIENT: Failed to connect to host=%s port=%i" % (host, port)

        try:
            data = self._get_auth_data()
            self.gc.send(data)
        except:
            pass

    # Close/cleanup network connections
    def _close_gc(self):
        if self.gc:
            data = json.dumps({'type': 'disconnect', 'pid': self.pid, 'timestamp': time.time()})
            # print 'CLIENT: sending disconnect to Game Coordinator...'
            self.gc.send(data)
            self.gc.close()
            sys.stdout.write('Disconnected.\n')
            sys.stdout.flush()

    def disconnect(self):
        self._close_gc()

    def _parse_input(self, string):
        if string[0] == '/':  # /commands!
            args = string[1:].split(' ')
            command = '_command_' + args[0].strip('\n')
            method = getattr(self, command)
            if not method:
                raise UnknownCommand(command)
            return method(self, *args[1:])
        else:
            message = self._get_message_data(string)
            self.gc.send(message)

    def _send_char(self):
        self.nm.push({'pid': self.pid, 'data': self.char})

    def _join_lobby(self, lid=None):
        self.gc.add_client_to_lobby(self.pid, lid)

    def _create_lobby(self):
        pass

    def _get_message_data(self, message):
        return json.dumps({'type': 'msg', 'pid': self.pid, 'message': message, 'timestamp': time.time()})

    def _get_auth_data(self):
        return json.dumps({'type': 'auth', 'pid': self.pid, 'name': self.name, 'timestamp': time.time()})

    def _handle_response(self, data):
        data = json.loads(data)
        if data['type'] == 'auth':
            self._handle_auth(data)
        elif data['type'] == 'notify':
            self._handle_notify(data)
        elif data['type'] == 'msg':
            self._handle_message(data)
        else:
            pass

    def _handle_auth(self, data):
        try:
            pid = data['pid']
            self.pid = pid
            # print 'CLIENT: setting pid to %s' % pid
        except KeyError:
            self._connect_gc()

    def _handle_message(self, data):
        try:
            msg = data['message']
            user = self.peers_pid_name_map[str(data['from'])]
            display_msg(msg, user)
        except KeyError:
            pass
        prompt()

    def _handle_notify(self, data):
        try:
            peers = data['peers']
            self.peers_pid_name_map = peers
            # print 'CLIENT: Recieved updated peer map.'
        except KeyError:
            pass

    def _command_help(self, *args):
        """
        Displays command information.
        """
        for command in filter(lambda c: '_command_' in c, dir(self)):
            print '/' + command.split('_command_')[-1] + getattr(self, command).__doc__

    def _command_w(self, *args):
        """
        Sends a whisper.
        Usage: /w [name] [message]
        """
        target = args[1]
        message = ' '.join(args[2:])
        if not message:
            return
        if target not in self.peer_pid_name_map.keys():  # change this shit later
            for k, v in self.peer_pid_name_map.items():
                if v is target:
                    target = k
                    break
        self.gc.send(json.dumps({'type': 'msg', 'pid': self.pid, 'message': message, 'target': target, 'timestamp': time.time()}))

    def _command_q(self, *args):
        """
        Quit.
        """
        self.exit_handler()

    def exit_handler(self):
        self.disconnect()
        sys.exit(0)

    def __str__(self):
        return '%s (%s)' % (self.name, self.pid)

if __name__ == '__main__':
    print 'Enter username.'
    client = Client(sys.stdin.readline())
    client._run()
