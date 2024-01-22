import multiprocessing as mp
import time
import Neo
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
            time.sleep(0.0001)#remove later!
            #check if main has sent new queues
            while self.main2dmaster.empty() == False:
                new_queues = self.main2dmaster.get(block=True,timeout = 1)
                proc_queues.append(new_queues)
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
                #print(self.netqdata)
                

    def Process(self):
        queues = [self.man.Queue(), self.man.Queue()]
        newAgent = mp.Process(target=self.Agent, args = (self.agentPort, queues,))
        self.agentPort += 1
        newAgent.start()
        self.agents.append(newAgent)

    def Agent(self, port, queues):
        print(f"Agent online at port {port}")
        send, recv = queues[0], queues[1]
        local_neo = Neo.Neo()    
        local_neo.start_server(PORT = port)
        local_neo.get_new_conn()
        while True:
            command = local_neo.receive_data()
            print(command)
            if command == "GET":
                send.put(command)
                while recv.empty():
                    pass
                sendback = recv.get()
                local_neo.send_data(sendback)
            elif command == "PUT":
                send.put(command)


if __name__ == "__main__":
    pass