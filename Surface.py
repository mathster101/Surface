import multiprocessing as mp
import time
#new surface needs to create
#1. Datamaster - store all shared variables
#2. Queue to send other queue deets from main 

class Surface:
    def __init__(self):
        ###########################
        ##set up for dmaster
        self.netqdata = {}
        self.man = mp.Manager()
        self.dmaster = mp.Process(target = self.Datamaster)
        #queue to send local tcp queue details of new procs
        self.main2dmaster = self.man.Queue()
        self.dmaster.start()
        ###########################

    def __del__(self):
        self.dmaster.kill()

    def Datamaster(self):
        print("Datamaster is online")
        proc_queues = []
        while True:
            time.sleep(0.001)#remove later!
            #check if main has sent new queues
            while self.main2dmaster.empty() == False:
                new_queue = self.main2dmaster.get(block=True,timeout = 1)
                proc_queues.append(new_queue)
            #print(proc_queues)
            #print("____________________________")
            #service one request from each process
            for incoming,outgoing in proc_queues:
                if incoming.empty():
                    continue
                orderrcvd = incoming.get()
                print(orderrcvd)
                command, netqueueId = orderrcvd                
                if netqueueId not in self.netqdata:
                    self.netqdata[netqueueId] = []

                if command == "GET":
                    if len(self.netqdata[netqueueId]) == 0:
                        retval = None
                    else:
                        retval = self.netqdata[netqueueId].pop(0)                    
                    outgoing.put(retval)
                elif command[0] == "PUT":
                    data = command[1]
                    self.netqdata[netqueueId].append(data)
                print(self.netqdata)



if __name__ == "__main__":
    pass