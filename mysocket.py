import socket

class MySocket:

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    def send(self, msg):
        totalsent = 0
        MSGLEN = len(msg)
        self.sock.send(str(MSGLEN))
        if self.sock.recv(1024)!=".":
            raise RuntimeError("client did not receive length")
        while totalsent < MSGLEN:
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive(self):
        chunks = []
        bytes_received = 0
        MSGLEN = int(self.sock.recv(1024))
        self.sock.send(".")
        while True:
            chunk = self.sock.recv(min(MSGLEN-bytes_received,1024))
            chunks.append(chunk)
            if MSGLEN == (bytes_received + len(chunk)):
                break
            else:
                bytes_received += len(chunk)
        return ''.join(chunks)
