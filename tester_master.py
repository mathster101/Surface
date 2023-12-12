import Surface
import multiprocessing as mp
import time
import numpy as np


NETWORK_IP = '192.168.1.11'


def dummy(text = "None"):
    import time
    index = 0
    print("this is the dummy function")
    with open("dummy.txt","w") as f:
        for i in range(10):
            f.write(f"{text} {index}\n")
            index += 1
            time.sleep(1)

def dummy2(surface_queue):
    import os
    import time
    import Surface
    import numpy as np
    surface = Surface.Surface()
    arr = np.random.random((100,100))
    for i in range(20000):
        #print(i)
        surface.queue_put(surface_queue, [f"{os.getpid()}:message from remote system {i}",arr])
        #time.sleep(0.1)

def local_test1():
    iters = 1000
    surface = Surface.Surface('100.87.169.65')
    queue_deets = surface.queue()
    start = time.time()
    data = np.random.random((10,10))
    for i in range(iters):
        surface.queue_put(queue_deets, data)
    mid = time.time()
    for i in range(iters):
        rcvd = surface.queue_get(queue_deets)
    end = time.time()
    p1 = (mid-start)/iters
    p2 = (end - mid)/iters
    print(f"put = {p1*1000}ms/conn\nget = {p2*1000}ms/conn\nfinished")        

def master_test1():
    surface = Surface.Surface()
    surface.register_network_thread(NETWORK_IP)
    surface.register_network_thread(NETWORK_IP)
    surface.register_network_thread(NETWORK_IP)
    print(surface.network_threads) 

def master_test2():
    surface = Surface.Surface()
    surface.register_network_thread(NETWORK_IP)    
    surface.process(target = dummy, args = ("hey there!"))

def master_test3():
    surface = Surface.Surface('100.87.169.65')
    surface_queue = surface.queue()
    surface.register_network_thread(NETWORK_IP)   
    surface.Process(target = dummy2, args=(surface_queue,))
    while 1:
        data = surface.queue_get(surface_queue)
        if data != None:
            #continue
            print(data[0])
        #time.sleep(0.001)

def master_test4():
    surface = Surface.Surface()
    surface_queue = surface.queue()
    surface.register_network_thread(NETWORK_IP)
    for i in range(6):
        surface.Process(target = dummy2, args=(surface_queue,))
    while 1:
        data = surface.queue_get(surface_queue)
        #continue
        if data != None:
            print(data[0])

def master_test5():
    surface = Surface.Surface()
    surface_queue1 = surface.queue()
    surface_queue2 = surface.queue()
    surface.register_network_thread(NETWORK_IP)
    #surface.register_network_thread('0.0.0.0')
    for i in range(2):
        surface.Process(target = dummy2, args=(surface_queue1,))
        surface.Process(target = dummy2, args=(surface_queue2,))
    print(surface.network_threads)
    while 1:
        data1 = surface.queue_get(surface_queue1)
        data2 = surface.queue_get(surface_queue2)
        #continue
        if data1 != None:
            print(data1[0])
        if data2 != None:
            print(data2[0])            

if __name__ == '__main__':
    # surface = Surface.Surface()
    # queue_deets = surface.queue()
    # test1(queue_deets)
    # surface.kill_queues()
    # ports = []
    # for i in range(8):
    #     ports.append(surface.Queue())
    local_test1()
    #master_test5()
    print("done")
