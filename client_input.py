# -*- coding: utf-8 -*-

import socket
import sys


HOST, PORT = '35.180.40.190', 8888
#HOST, PORT = 'localhost', 8888

received = ''

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((HOST, PORT))

    while received != 'disconnected' and received != 'error':
        data = input('>>> ')
        sock.sendall(bytes(data + '\n', 'utf-8'))
        received = str(sock.recv(1024), 'utf-8')
        print('Sent:     {}'.format(data))
        print('Received: {}'.format(received))

