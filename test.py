import Surface
import multiprocessing as mp
import time
import Neo

def test1():
    surf = Surface.Surface()
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
    surf = Surface.Surface()
    surf.Process()
    def connect2agent():
        time.sleep(0.3)
        neo = Neo.Neo()
        neo.connect_client(PORT=30303, IP='127.0.0.1')
        neo.send_data([["PUT",69],1234])
        neo.send_data(["GET",1234])
        data = neo.receive_data()
        print(f"got {data} from queue")
        while True:
            pass
    mlemm = mp.Process(target = connect2agent)
    mlemm.start()
    mlemm.join()



test2()
