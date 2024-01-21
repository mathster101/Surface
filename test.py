import Surface
import multiprocessing as mp



def main():
    surf = Surface.Surface()
    man = mp.Manager()
    s,r = man.Queue(), man.Queue()
    surf.main2dmaster.put([s,r])
    while True:
        pass



main()
