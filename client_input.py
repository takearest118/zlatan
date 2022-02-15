# -*- coding: utf-8 -*-

import socket
import sys


#HOST, PORT = '35.180.40.190', 8888
DEFAULT_HOST, DEFAULT_PORT = '192.168.41.254', 8888
host = DEFAULT_HOST
port = DEFAULT_PORT
if len(sys.argv) > 1:
    host = sys.argv[1]
if len(sys.argv) > 2:
    port = int(sys.argv[2])

received = ''

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((host, port))

    while received != 'disconnected' and received != 'error':
        try:
            data = input('>>> ')
        except EOFError:
            print("")
            data = ":/quit"

        if data == "":
            continue
        sock.sendall(bytes(data + '\n', 'utf-8'))
        received = str(sock.recv(1024), 'utf-8')
        print('Sent:     {}'.format(data))
        print('Received: {}'.format(received))
            
            

