import Magi
import multiprocessing as mp
import time
import numpy as np




def slave_test1():
    magi = Magi.Magi()
    while 1:
        magi.listen_for_orders()


if __name__ == "__main__":
    slave_test1()