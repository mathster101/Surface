import Magi
import multiprocessing as mp
import time
import numpy as np




def slave_test1():
    magi = Magi.Magi()
    magi.listen_for_orders()