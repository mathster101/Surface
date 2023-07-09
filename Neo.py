import socket
import pickle
import time
import base64
import zlib

class Neo:
    def __init__(self):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.conn = None
        self.addr = None
        self.i_am_a = None
        self.remnant = b''

    def __del__(self):
        try:
            self.sock.close_conn()
        except:
            pass

    def start_server(self, PORT=9999):
        self.i_am_a = "server"
        self.sock.bind(('', PORT))
        self.sock.listen(5)
    
    def get_new_conn(self, timeout = False):
        self.i_am_a = "server"
        if timeout == True:
            self.sock.settimeout(1)
            try:
                self.conn, self.addr = self.sock.accept()
                self.sock.settimeout(None)
                return (self.conn, self.addr)
            except:
                self.sock.settimeout(None)
                return "Timeout"
        else:
            self.conn, self.addr = self.sock.accept()
            return (self.conn, self.addr)

    def connect_client(self, PORT=9999, IP='127.0.0.1'):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.i_am_a = "client"
        self.sock.connect((IP, PORT))
        #print(self.sock.getsockname())
        return True

    def close_conn(self):
        if self.i_am_a=="server":
            self.conn.close()
        else:
            self.sock.close()
        self.conn = None
        self.addr = None
        self.i_am_a = None


    def receive_data(self):
        received = self.remnant
        end_char = bytes("msg-end", encoding = 'utf-8')
        if self.i_am_a == "server":
            while 1:
                received += self.conn.recv(1024)
                if end_char in received:
                    break
        else:
            while 1:    
                received += self.sock.recv(1024)
                if end_char in received:
                    break
        terminate_at = received.find(end_char)
        true_received = received[:terminate_at]
        true_received = zlib.decompress(true_received)
        true_received = base64.b64decode(true_received)
        self.remnant = received[terminate_at+len("msg-end"):]
        true_received = pickle.loads(true_received)
        return true_received

    def send_data(self,object_to_send):
        data = pickle.dumps(object_to_send)
        data = base64.b64encode(data)
        data = zlib.compress(data)
        data += bytes("msg-end",encoding = 'utf-8')
        if self.i_am_a == "server":
            self.conn.sendall(data)
        else:
            self.sock.sendall(data)

    def get_my_ip(self):
        return socket.gethostbyname(socket.gethostname())