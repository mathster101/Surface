import Magiv1
import multiprocessing as mp
import Neo
import time
import numpy as np
import sys
def dummy_proc():
    biggie = np.random.random((20,20))
    #print(sys.getsizeof(biggie),"Bytes")
    conn = Neo.Neo()
    start = time.time()
    for i in range(1000):
        conn.connect_client(PORT=1234)
        conn.send_data(['put',i%12,biggie])
        conn.close_conn()
    mid = time.time()
    for i in range(4):
        conn.connect_client(PORT=1234)
        conn.send_data(['get',1])
        rcvd = conn.receive_data()
        #print("rcvd=",rcvd)
        conn.close_conn()
    end = time.time()

    print(f"put = {(mid-start)/1000}s/conn get = {(end - mid)/4}s/conn")


if __name__ == '__main__':
    mirrh = Magiv1.Magi()
    dummy_proc()
    pass