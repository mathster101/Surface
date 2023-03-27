import Magiv2
import multiprocessing as mp
import Neo
import time
import numpy as np

def test1():
    iters = 100
    rcvd_data = []
    neo_inst = Neo.Neo()
    ###################################3
    #registration
    neo_inst.connect_client(PORT=1234, IP='192.168.0.4')
    port = neo_inst.receive_data()
    print("queue is at",port)
    neo_inst.close_conn()
    #####################################3
    #transactions
    neo_inst.connect_client(PORT=port)
    start = time.time()
    for i in range(iters):
        data = ['put',i]
        neo_inst.send_data(data)
    mid = time.time()
    for i in range(iters):
        neo_inst.send_data("get")
        data = neo_inst.receive_data()
    end = time.time()
    #neo_inst.send_data("debug")
    print(f"put = {(mid-start)/iters}s/conn get = {(end - mid)/iters}s/conn\nfinished")

if __name__ == '__main__':
    mirrh = Magiv2.Magi()
    test1()