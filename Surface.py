import multiprocessing as mp
import time
import Neo
import numpy as np
import os
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
        ###misc stuff###################
        self.netClients = {}
        self.totalProcCount = 0

    def __del__(self):
        self.dmaster.kill()

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
        neo = Neo.Neo()    
        neo.start_server(PORT=port)
        neo.get_new_conn()
        while True:
            orderrcvd = neo.receive_data()
            #print(f"order at agent {orderrcvd}")
            command, _ = orderrcvd
            if command == "GET":
                send.put(orderrcvd)
                while recv.empty():
                    pass
                sendback = recv.get()
                neo.send_data(sendback)
            elif command[0] == "PUT":
                send.put(orderrcvd)

    def listenForOrders():
        neo = Neo.Neo()
        neo.start_server(PORT=6969)
        print("Surface client online")
        while True:
            #handle heartbeat timers if no orders
            if neo.get_new_conn(timeout = True) == "Timeout":
                order = "handle_proc_timers"
            else:    
                order = neo.receive_data()   
            #return number of cores to registering entity
            if order == 'registration':
                cores = os.cpu_count()
                neo.send_data(cores)
                neo.close_conn()
                print("registration over")
            
            #receive function body and args and
            #spawn a new process
            elif order == 'spawn_process':
                pass
         
    def registerMaster(self,masterIP):
        self.masterIP = masterIP

    def registerClient(self, IP_ADDR, PORT=6969):
        if IP_ADDR in self.netClients:
            return True
        try:
            neo = Neo.Neo()
            neo.connect_client(PORT=6969,IP = IP_ADDR)
            neo.send_data('registration')
            num_cores = neo.receive_data()
            self.network_threads[IP_ADDR] = [num_cores, 0]#num cores, num procs
            neo.close_conn()
            return True
        except:
            print(f"{IP_ADDR} is offline")
            return False            


if __name__ == "__main__":
    pass