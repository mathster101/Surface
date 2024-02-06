import Surface
import multiprocessing as mp
import time
import Neo

MASTER_IP = '127.0.0.1'


def test1():
    surf = Surface.Surface_master()
    man = mp.Manager()
    s,r = man.Queue(), man.Queue()
    a,b = man.Queue(), man.Queue()
    surf.main2dmaster.put([s,r])
    surf.main2dmaster.put([a,b])
    s.put([["PUT",69],1234])
    s.put([["PUT",70],1234])
    s.put([["PUT",71],1234])
    s.put([["PUT",72],1234])
    s.put([["PUT",99],1235])
    s.put(["GET",1234])
    #a.put([["PUT",100],1235])
    time.sleep(2)#make this bigger if needed


def test2():
    surf = Surface.Surface_master()
    surf.Process()
    def connect2agent():
        time.sleep(0.3)
        neo = Neo.Neo()
        neo.connect_client(PORT=30303, IP=MASTER_IP)
        neo.send_data([["PUT",69],1234])
        neo.send_data(["GET",1234])
        data = neo.receive_data()
        print(f"got {data} from queue")
        while True:
            pass
    mlemm = mp.Process(target = connect2agent)
    mlemm.start()
    mlemm.join()

def test3():
    surf = Surface.Surface_master()
    surf.Process()
    surf.Process()

    def connect2agent():
        neo = Neo.Neo()
        neo.connect_client(PORT=30303, IP=MASTER_IP)
        while True:
            neo.send_data([["PUT",69],1234])
            neo.send_data(["GET",1234])
            data = neo.receive_data()
            print(f"got {data} from queue")
    def connect2agent2():
        neo = Neo.Neo()
        neo.connect_client(PORT=30304, IP=MASTER_IP)
        while True:
            neo.send_data([["PUT",101],1234])
            neo.send_data(["GET",1234])
            data = neo.receive_data()
            print(f"got {data} from queue")    
    mlemm = mp.Process(target = connect2agent)
    blemm = mp.Process(target = connect2agent2)
    mlemm.start()
    blemm.start()
    mlemm.join()
    blemm.join()    

################################################################
def test4_1():
    surf = Surface.Surface_master()
    surf.Process()
    surf.Process()
    while True:
        pass

def test4_2():
    def connect2agent():
        neo = Neo.Neo()
        neo.connect_client(PORT=30303, IP=MASTER_IP)#queue agent 1
        while True:
            neo.send_data([["PUT",69],1234])
            neo.send_data(["GET",1234])
            data = neo.receive_data()
            print(f"got {data} from queue")
    def connect2agent2():
        neo = Neo.Neo()
        neo.connect_client(PORT=30304, IP=MASTER_IP)#queue agent 2
        while True:
            neo.send_data([["PUT",101],1234])
            neo.send_data(["GET",1234])
            data = neo.receive_data()
            print(f"got {data} from queue")    
    mlemm = mp.Process(target = connect2agent)
    blemm = mp.Process(target = connect2agent2)
    mlemm.start()
    blemm.start()
    mlemm.join()
    blemm.join()    
################################################################
def test5():
    def hello(kappa):
        print(f"hello world {kappa}")
    surf = Surface.Surface_master()
    surf.registerMaster('192.168.0.23')
    surf.registerClient('192.168.0.40')
    surf.Process(target=hello, args = ("mathew"))
    print(surf.netClients)
################################################################
def test6():
    def badFibonacci(x):
        if x <= 1:
            return 1
        localSoln = badFibonacci(x-1) + badFibonacci(x-2)
        print(localSoln)
        return localSoln
    surf = Surface.Surface_master()
    surf.registerMaster('192.168.0.23')
    surf.registerClient('192.168.0.40')   
    surf.Process(target=badFibonacci, args = (10))
    while True:
        pass
################################################################    
def test7():
    def hello():
        from time import sleep
        queue = queueConnect()
        counter = 0
        while True:
            queue.queuePut(f"hello-{counter}", 1234)
            data = queue.queueGet(1234)
            print(data)
            counter += 1
    surf = Surface.Surface_master()
    surf.registerMaster('192.168.0.23')
    surf.registerClient('192.168.0.40')   
    for i in range(10):
        surf.Process(target=hello)
    while True:
        pass
################################################################
def test8():
    def hello():
        import time 
        queueConnect()
        while True:
            pass
    surf = Surface.Surface_master()
    surf.registerMaster('192.168.0.23')
    surf.registerClient('192.168.0.40')   
    for i in range(10):
        surf.Process(target=hello)
    while True:
        pass
################################################################  
def test9():
    dummyArray = (400,40)
    def hello1(dummyArray):
        from time import sleep
        import numpy as np
        from random import randint
        queue = queueConnect()
        counter = 0
        array = np.random.random(dummyArray)
        while True:
            for i in range(12):
                queue.queuePut(array, 1234)
            print("cowly")
            sleep(randint(1,16))
            for i in range(12):
                data = queue.queueGet(1234)
    def hello2(dummyArray):
        from time import sleep
        import numpy as np
        from random import randint
        queue = queueConnect()
        counter = 0
        array = np.random.random(dummyArray)
        while True:
            for i in range(10):
                queue.queuePut(array, 1234)
            sleep(randint(1,16))
            for i in range(10):
                data = queue.queueGet(1234)
    def hello3(dummyArray):
        from time import sleep
        import numpy as np
        queue = queueConnect()
        counter = 0
        array = np.random.random(dummyArray)
        while True:
            for i in range(10):
                queue.queuePut(array, 1234)
            for i in range(10):
                data = queue.queueGet(1234)             
    surf = Surface.Surface_master()
    surf.registerClient('100.117.161.73')
    surf.registerClient('100.111.219.20')
    surf.registerClient('100.78.211.63')
    surf.registerMaster('100.87.169.65')
    nums = 5
    for i in range(nums):
        surf.Process(target=hello1, args = (dummyArray,))
    for i in range(nums):
        surf.Process(target=hello2, args = (dummyArray,))
    for i in range(nums):
        surf.Process(target=hello3, args = (dummyArray,))       
    while True:
        pass
#########################################################
def test8():
    class foo:
        def __init__(self):
            self.a=0
    def hello():
        import time
        class foo:
            def __init__(self):
                self.a = 99
            def __getstate__(self):
                print("I'm being dill-ed")
                return self.__dict__
        queue=queueConnect()
        while True:
            queue.queuePut(foo(),1234)
    surf = Surface.Surface_master()
    surf.registerMaster('192.168.0.23')
    surf.registerClient('192.168.0.40')   
    surf.Process(target=hello)
    while True:
        pass
# test3()
test8()
