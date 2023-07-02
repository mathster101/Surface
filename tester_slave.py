import Magi
import multiprocessing as mp
import time
import numpy as np
import os, glob



def slave_test1():
    for filename in glob.glob("./tmp_*"):
        os.remove(filename) 
    magi = Magi.Magi()
    while 1:
        magi.listen_for_orders()


if __name__ == "__main__":
    slave_test1()