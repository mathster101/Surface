import multiprocessing as mp
import time
import Neo
import numpy as np
#new surface needs to create
#1. Datamaster - store all shared variables
#2. Queue to send other queue deets from main 

class Surface:
    def __init__(self):
        ###########################
        ##set up for dmaster
        self.netqdata = {}
        self.man = mp.Manager()
        self.dmaster = mp.Process(target = self.dataMaster)
        #queue to send local tcp queue details of new procs
        self.main2dmaster = self.man.Queue()
        self.dmaster.start()
        ###########################
        ##set up for agents
        self.agentPort = 30303
        self.agents = []
        ###########################

    def __del__(self):
        self.dmaster.kill()

    def registerMaster(self,masterIP):
        self.masterIP = masterIP

    def dataMaster(self):
        print("Datamaster is online")
        proc_queues = []
        while True:
            #time.sleep(0.0001)#remove later!
            #check if main has sent new queues
            while self.main2dmaster.empty() == False:
                new_queues = self.main2dmaster.get()
                proc_queues.append(new_queues)
            #service one request from each process
            for incoming,outgoing in proc_queues:
                if incoming.empty():
                    continue
                orderrcvd = incoming.get()
                #print(f"order at dmaster {orderrcvd}")
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
                #print(self.netqdata)
                

    def Process(self):
        a = self.man.Queue()
        b = self.man.Queue()
        self.main2dmaster.put([a,b])
        self.agentPort += 1
        newAgent = mp.Process(target=self.Agent, args = (self.agentPort-1, [a, b]))
        self.agents.append(newAgent)
        self.agents[-1].start()

    def Agent(self, port, queues):
        print(f"Agent online at port {port}")
        send, recv = queues
        local_neo = Neo.Neo()    
        local_neo.start_server(PORT=port)
        local_neo.get_new_conn()
        while True:
            orderrcvd = local_neo.receive_data()
            #print(f"order at agent {orderrcvd}")
            command, _ = orderrcvd
            if command == "GET":
                send.put(orderrcvd)
                while recv.empty():
                    pass
                sendback = recv.get()
                local_neo.send_data(sendback)
            elif command[0] == "PUT":
                send.put(orderrcvd)
                


if __name__ == "__main__":
    pass