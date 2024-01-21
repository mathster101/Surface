import Surface
import multiprocessing as mp
import time


def main():
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
    s.put([["PUT",72],1235])
    a.put([["PUT",100],1235])
    time.sleep(4)#make this bigger if needed


main()
