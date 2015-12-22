#!/usr/bin/env python

import socket
import sys
import signal
import select
import json
import time
import struct
import Queue
# import lobby


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
        self.BUFFER_SIZE = 4096

        self._lobbies = {}
        self._clients = []
        self._pid_client_map = {}
        self._pid_name_map = {}

        self.next_id = {'pid': [0], 'lid': [0], 'gid': [0]}
        self.queues = {'in': [], 'out': [], 'ex': []}
        self.response_map = {}  # A map of response queues by client

    def _start_gc(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print 'GC: Launching server host=%s, port=%s' % (self.host, self.port)
            self.server.bind((self.host, self.port))  # localhost for now
            self.server.listen(5)
        except socket.error, (val, msg):
            if self.server:
                self.server.close()
            print 'Error opening socket: %s' % (msg)
            sys.exit(1)

    def _run(self):
        self._start_gc()
        self.queues['in'] = [self.server]

        while True:
            inqueue, outqueue, exqueue = select.select(self.queues['in'], self.queues['out'], self.queues['ex'])
            for s in inqueue:
                if s == self.server:
                    client = self.server.accept() + (self.BUFFER_SIZE,)
                    conn, addr, size = client
                    self.queues['in'].append(conn)
                    self.response_map[conn] = Queue.Queue()
                else:
                    data = s.recv(size)
                    print 'GC: Received %s bytes from %s' % (len(data), s.getpeername())
                    if data:
                        self._handle_client_data(data, s)
                    else:
                        self._remove_client_from_queues(s)
            for s in outqueue:
                try:
                    resp = self.response_map[s].get_nowait()
                except Queue.Empty:
                    self.queues['out'].remove(s)
                else:
                    print 'GC: Sending %s to %s' % (resp, s.getpeername())
                    s.sendall(struct.pack('!I', len(resp)))
                    s.sendall(resp)

    def get_lobby(self, lid):
        try:
            lobby = self._lobbies[lid]
        except KeyError:
            lobby = None
        return lobby

    def create_lobby(self, pid=None):
        pass

    def add_client_to_lobby(self, lid=None):
        pass
        # lobby = self.get_lobby(lid)

    def _handle_client_data(self, data, client=None):
        data = json.loads(data)
        resp = None
        target = None
        if data['type'] == 'auth':
            resp = json.dumps(self._handle_auth(data, client))
        elif data['type'] in ['msg', 'msg-w']:
            resp = self._handle_message(data, client)
            try:
                target = self._pid_client_map[resp['target']]
                resp = json.dumps(resp)
            except KeyError:
                return
        elif data['type'] == 'disconnect':
            self._handle_disconnect(data, client)
            return
        else:
            pass
        try:
            if (target or client) not in self.queues['out']:
                self.queues['out'].append(target or client)
            self.response_map[target or client].put(resp)
        except KeyError:
            self.response_map[target or client] = Queue.Queue()
            self.response_map[target or client].put(resp)
        return resp

    def _handle_auth(self, data, client):
        try:
            pid = data['pid']
            name = data['name']
            if not pid:
                pid = self._assign_id('pid')
            self._clients.append(pid)
            self._pid_client_map[pid] = client
            self._pid_name_map[pid] = name
            notify_conn_data = self._get_notify_peer_data()
            self._broadcast(notify_conn_data, -1)
            return {'type': 'auth', 'pid': pid, 'timestamp': time.time()}
        except KeyError:
            pass
            # self.queues['ex'].append(json.dumps({'type': 'exception', 'error': InvalidRequest}))

    def _broadcast(self, data, pid):
        for _pid in self._clients:
            if _pid == pid:
                continue
            conn = self._pid_client_map[_pid]
            if conn not in self.queues['out']:
                self.queues['out'].append(conn)
            try:
                self.response_map[conn].put(json.dumps(data))
            except KeyError:
                self.response_map[conn] = Queue.Queue()
                self.response_map[conn].put(json.dumps(data))

    def _handle_message(self, data, client):
        print 'GC: Received - ', data
        try:
            target = data['target']
            print target, self._pid_client_map
        except KeyError:
            target = None
            msg_data = {'type': 'msg', 'message': data['message'], 'from': data['pid'], 'timestamp': time.time()}
            self._broadcast(msg_data, data['pid'])
        return {'type': 'msg-w', 'message': data['message'], 'target': target, 'from': data['pid'], 'timestamp': time.time()}

    def _handle_disconnect(self, data, client):
        try:
            pid = data['pid']
            self._clients.remove(pid)
            self._free_id('pid', pid)
            self._remove_client_from_queues(client)
            del self._pid_name_map[pid]
            msg_data = self._get_notify_peer_data()
            self._broadcast(msg_data, pid)
        except (ValueError, KeyError):
            pass

    def _remove_client_from_queues(self, client):
        if client in self.queues['in']:
            self.queues['in'].remove(client)
        if client in self.queues['out']:
            self.queues['out'].remove(client)
        if client in self.queues['ex']:
            self.queues['ex'].remove(client)
        try:
            del self.response_map[client]
        except KeyError:
            pass

    def _free_id(self, id_type, _id):
        print 'GC: %s %i is now available' % (id_type, _id)
        self.next_id[id_type].append(_id)

    def _assign_id(self, id_type):
        _id = self.next_id[id_type].pop()
        if not self.next_id[id_type]:
            self.next_id[id_type].append(_id + 1)
        return _id

    def _get_notify_peer_data(self):
        return {'type': 'notify', 'peers': self._pid_name_map, 'timestamp': time.time()}


def exit_handler(sig, frame):
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_handler)
    gc = GameCoordinator()
    gc._run()
