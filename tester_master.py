import Magi
import multiprocessing as mp
import time
import numpy as np

def dummy():
    import time
    index = 0
    with open("dummy.txt","w") as f:
        while 1:
            f.write(f"index \n")
            index += 0
            time.sleep(secs=1)

def test1(queue_deets):
    iters = 1000
    magi = Magi.Magi()
    start = time.time()
    data = np.random.random((10,10))
    for i in range(iters):
        magi.queue_put(queue_deets, data)
    mid = time.time()
    for i in range(iters):
        rcvd = magi.queue_get(queue_deets)
    end = time.time()
    p1 = (mid-start)/iters
    p2 = (end - mid)/iters
    print(f"put = {p1*1000}ms/conn get = {p2*1000}ms/conn\nfinished")        

def master_test1():
    magi = Magi.Magi()
    magi.register_network_thread('192.168.0.6')
    print(magi.network_threads) 

def master_test2():
    magi = Magi.Magi()
    magi.register_network_thread('192.168.0.6')    
    magi.process(target = dummy)

if __name__ == '__main__':
    # magi = Magi.Magi()
    # queue_deets = magi.queue()
    # test1(queue_deets)
    # magi.kill_queues()
    # ports = []
    # for i in range(8):
    #     ports.append(magi.Queue())
    
    master_test2()