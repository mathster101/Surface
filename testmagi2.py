import Magiv2
import multiprocessing as mp
import Neo
import time
import numpy as np

def test1(PORT):
    iters = 100
    rcvd_data = []
    neo_inst = Neo.Neo()
    ###################################3
    #transactions
    start = time.time()
    for i in range(iters):
        neo_inst.connect_client(PORT=PORT, IP = "192.168.0.4")
        data = ['put',i]
        neo_inst.send_data(data)
        success = neo_inst.receive_data()
        neo_inst.close_conn()
    mid = time.time()
    for i in range(iters):
        neo_inst.connect_client(PORT=PORT, IP = "192.168.0.4")
        neo_inst.send_data("get")
        data = neo_inst.receive_data()
        neo_inst.close_conn()
    end = time.time()
    #neo_inst.send_data("debug")
    #neo_inst.send_data("kill")
    #neo_inst.close_conn()
    p1 = (mid-start)/iters
    p2 = (end - mid)/iters
    print(f"put = {p1*1000}ms/conn get = {p2*1000}ms/conn\nfinished")

if __name__ == '__main__':
    magi = Magiv2.Magi()
    #qport = magi.Queue()
    #test1(qport)
    ports = []
    for i in range(8):
        ports.append(magi.Queue())