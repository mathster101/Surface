import Magi
import multiprocessing as mp
import Neo
import time
import numpy as np

def test1(PORT):
    iters = 1000
    rcvd_data = []
    neo_inst = Neo.Neo()
    ###################################3
    #transactions
    neo_inst.connect_client(PORT=PORT, IP = "192.168.0.4")
    start = time.time()
    for i in range(iters):
        #neo_inst.connect_client(PORT=PORT, IP = "192.168.0.4")
        data = np.random.random((100,100))
        neo_inst.send_data(['put',data])
        success = neo_inst.receive_data()
        #neo_inst.close_conn()
    mid = time.time()
    rcvd_crap = []
    for i in range(iters):
        #neo_inst.connect_client(PORT=PORT, IP = "192.168.0.4")
        neo_inst.send_data("get")
        data = neo_inst.receive_data()
        rcvd_crap.append(data)
        #neo_inst.close_conn()
    end = time.time()
    #neo_inst.send_data("debug")
    #neo_inst.send_data("kill")
    neo_inst.close_conn()
    p1 = (mid-start)/iters
    p2 = (end - mid)/iters
    print(f"put = {p1*1000}ms/conn get = {p2*1000}ms/conn\nfinished")
    print(len(rcvd_crap))

def test2(queue_deets):
    magi = Magi.Magi()
    for i in range(100):
        magi.Queue_put(queue_deets,f"hello{i}")
    for i in range(100):
        rcvd = magi.Queue_get(queue_deets)
        print(rcvd)



if __name__ == '__main__':
    magi = Magi.Magi()
    queue_deets = magi.Queue()
    test2(queue_deets)
    # ports = []
    # for i in range(8):
    #     ports.append(magi.Queue())