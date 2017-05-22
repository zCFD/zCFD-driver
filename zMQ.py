""" Message Queue to support communication between client and cloud service

    License:

    Copyright: Zenotech Ltd 2012-2017
"""


import threading
import snakemq
import snakemq.link
import snakemq.packeter
import Queue
from collections import deque
import time

import os
import sys
import termios
import fcntl

def getch():
    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    try:
        while 1:
            try:
                c = sys.stdin.read(1)
                #print 'TEST'
                break
            except IOError: pass
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    return c

class zMQ:
    """A one to many bidirectional Message Queue Relay"""
    def __init__(self, single_port=4000, multiple_port=4001):
        self.single_recv = []
        self.multiple_recv = []
        self.single_pktr = 0
        self.multiple_pktr = 0
        self.q = deque()
        self.single_port = single_port
        self.multiple_port = multiple_port

    def run(self):
        ts = threading.Thread(target=self.create_single_listener)
        ts.setDaemon(True)
        ts.start()
        tm = threading.Thread(target=self.create_multiple_listener)
        tm.setDaemon(True)
        tm.start()
        print('Press q to quit')
        nb = 's'
        while nb != 'q':
            nb = getch()


    def create_single_listener(self):
        s = snakemq.link.Link()
        s.add_listener(("",self.single_port))
        self.single_pktr = snakemq.packeter.Packeter(s)
        self.single_pktr.on_packet_recv.add(self.single_on_recv)
        self.single_pktr.on_disconnect.add(self.single_disconnect)
        s.loop()

    def single_on_recv(self, conn, packet):
        print("received from", conn, packet)
        if packet == 'register':
            print("register single")
            if self.single_recv.__len__() == 1:
                self.single_pktr.send_packet(self.single_recv[0],b"disconnect")
            self.single_recv.append(conn)
            while self.q.__len__():
                self.single_pktr.send_packet(conn, self.q.popleft())
        else:
            for mconn in self.multiple_recv:
                self.multiple_pktr.send_packet(mconn,packet)

    def single_disconnect(self, conn):
        print "disconnect"
        self.single_recv.remove(conn)

    def create_multiple_listener(self):
        s = snakemq.link.Link()
        s.add_listener(("",self.multiple_port))
        self.multiple_pktr = snakemq.packeter.Packeter(s)
        self.multiple_pktr.on_packet_recv.add(self.multiple_on_recv)
        self.multiple_pktr.on_disconnect.add(self.multiple_disconnect)
        s.loop()

    def multiple_on_recv(self, conn, packet):
        print("received from", conn, packet)
        if packet == 'register':
            print("register multiple")
            self.multiple_recv.append(conn)
        else:
            if self.single_recv.__len__() == 0:
                self.q.append(packet)
            else:
                for sconn in self.single_recv:
                    self.single_pktr.send_packet(sconn,packet)

    def multiple_disconnect(self, conn):
        print "disconnect"
        self.multiple_recv.remove(conn)


class Connector:
    """A one to many bidirectional Message Queue Connector"""
    def __init__(self, host, port):
        self.link = 0
        self.listener = 0
        self.host = host
        self.port = port
        self.q = Queue.Queue()
        self.ts = 0 # Thread
        #self.sent_message = False

    def run(self):
        self.ts = threading.Thread(target=self.create_connector) # Create connector on separate thread
        self.ts.setDaemon(True)
        self.ts.start() # Note this thread wont complete - call stop to enable thread to complete

    def create_connector(self):
        self.link = snakemq.link.Link()
        #self.link.on_ready_to_send(self.ready_to_send)
        self.link.add_connector((self.host,self.port))
        self.pktr = snakemq.packeter.Packeter(self.link)
        self.pktr.on_connect.add(self.on_connect)
        self.pktr.on_packet_recv.add(self.on_recv)
        #self.pktr.on_packet_sent.add(self.ready_to_send)
        self.link.loop()

    def on_connect(self, conn):
        # Register with listener
        self.pktr.send_packet(conn, b"register")
        # Keep a reference to listener
        self.listener = conn

    def on_recv(self, conn, packet):
        #print("received from", conn, packet)
        if packet == 'disconnect':
            self.stop() # Not sure if this work needs testing
        else:
            self.q.put(packet) # Store in coming packets in a thread safe queue

    def ready_to_send(self,conn_id, packet):
        self.sent_message = True

    def send_message(self, message):
        # Make sure that connection has been established
        while self.listener == 0:
            time.sleep(1)
        #self.sent_message = False
        self.pktr.send_packet(self.listener, message) # Send a packet to the listener
        #time.sleep(1)

    def stop(self):
        self.link.stop() # Stop the connector

if __name__ == "__main__":
    zmq = zMQ()
    zmq.run()
