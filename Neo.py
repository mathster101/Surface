import socket
import pickle
import time
class Neo:
    def __init__(self):
        self.sock = socket.socket()
        self.conn = None
        self.addr = None
        self.i_am_a = None
        self.remnant = b''

    def start_server(self, PORT=9999):
        self.i_am_a = "server"
        self.sock.bind(('', PORT))
        self.sock.listen(5)
    
    def get_new_conn(self):
        self.conn, self.addr = self.sock.accept()
        return (self.conn, self.addr)

    def connect_client(self, PORT=9999, IP='127.0.0.1'):
        self.i_am_a = "client"
        self.sock.connect((IP, PORT))

    def close_conn(self):
        if self.i_am_a=="server":
            self.conn.close()
        else:
            self.sock.close()
        self.sock = socket.socket()
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
        received = received[:terminate_at]
        self.remnant = received[terminate_at+len("msg-end"):]
        received = pickle.loads(received)
        return received

    def send_data(self,object_to_send):
        data = pickle.dumps(object_to_send)
        data += bytes("msg-end",encoding = 'utf-8')
        if self.i_am_a == "server":
            self.conn.sendall(data)
        else:
            self.sock.sendall(data)
            time.sleep(0.001)#doesnt work without this :/
