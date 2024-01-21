import Surface
import multiprocessing as mp



def main():
    surf = Surface.Surface()
    s,r = mp.Queue(), mp.Queue()
    surf.main2dmaster.put([s,r])



main()