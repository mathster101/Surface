import multiprocessing as mp
import time
import Neo
import os
import importlib
import inspect


class Surface_master:
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

    def __del__(self):
        self.dmaster.kill()
        for agent in self.agents:
            agent.kill()

    def dataMaster(self):
        print("Datamaster is online")
        proc_queues = []
        count = 0
        while True:
            #check if main has sent new queues
            while self.main2dmaster.empty() == False:
                new_queues = self.main2dmaster.get()
                proc_queues.append(new_queues)
            puts = []
            gets = []
            #service one request from each process
            for incoming,outgoing in proc_queues:
                if incoming.empty():
                    continue
                orderrcvd = incoming.get()
                command, netqueueId = orderrcvd                
                if netqueueId not in self.netqdata:
                    self.netqdata[netqueueId] = []

                if command == "GET":
                    if len(self.netqdata[netqueueId]) == 0:
                        retval = None
                    else:
                        retval = self.netqdata[netqueueId].pop(0)               
                    outgoing.put(retval)
                    count += 1
                elif command[0] == "PUT":
                    #print(count, "put")
                    data = command[1]
                    self.netqdata[netqueueId].append(data)
                    #count += 1

    def Agent(self, port, queues):
        print(f"Agent online at port:{port}")
        send, recv = queues
        neo = Neo.Neo()    
        neo.start_server(PORT=port)
        neo.get_new_conn()
        print(f"Remote process connected to port:{port}")
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
                
    def Process(self, target = None, args = None):
        a = self.man.Queue()
        b = self.man.Queue()
        self.main2dmaster.put([a,b])
        self.agentPort += 1
        newAgent = mp.Process(target=self.Agent, args = (self.agentPort-1, [a, b]))
        self.agents.append(newAgent)
        self.agents[-1].start()

        if target != None:
            min_load = float('inf')
            proc_target = None
            for targetClient in self.netClients:
                cores = self.netClients[targetClient][0]
                procs = self.netClients[targetClient][1]
                load = procs/cores
                if load < min_load:
                    proc_target = targetClient
                    min_load = load
            print(proc_target, "chosen")
            self.netClients[proc_target][1] += 1
            details = self.__process_internal(target, args,IP=proc_target)

    def registerMaster(self,masterIP):
        self.masterIP = masterIP

    def registerClient(self, IP_ADDR, PORT=6969):
        if IP_ADDR in self.netClients:
            return True
        try:
            neo = Neo.Neo()
            neo.connect_client(PORT=PORT,IP = IP_ADDR)
            neo.send_data('registration')
            num_cores = neo.receive_data()
            self.netClients[IP_ADDR] = [num_cores, 0]#num cores, num procs
            neo.close_conn()
            return True
        except:
            print(f"{IP_ADDR} is offline")
            return False            

    def __process_internal(self,target,args = None, IP='192.168.1.11'):
        neo = Neo.Neo()
        print("going to spawn a new proc")
        neo.connect_client(PORT=6969,IP = IP)
        neo.send_data("spawn_process")
        src = inspect.getsource(target)
        neo.send_data(str(target.__name__))
        neo.send_data(src)
        if str(type(args)) == "<class 'tuple'>":
            pass
        else:
            args = (args,)
        neo.send_data(args)
        pid = neo.receive_data()
        neo.close_conn()
        return (IP,pid)
    

class Surface_slave:
    def __init__(self):
        self.procsRcvd = 0
        self.listenPort = -1
        self.localProcs = []
    
    def startListener(self, PORT = 6969):
        neo = Neo.Neo()
        neo.start_server(PORT=PORT)
        print("Surface slave online")
        self.listenPort = PORT
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
                functionName = neo.receive_data()
                functionText = neo.receive_data()
                with open(f"tmp_{self.procsRcvd}.py","w") as f:
                    f.write(functionText)
                args = neo.receive_data()
                proc = self.__spawn_local_process(f"tmp_{self.procsRcvd}", args, functionName)
                self.local_procs.append(proc)
                # os.remove(f"tmp_{self.procsRcvd}.py")#remove temp file
                # self.procsRcvd += 1
                # neo.send_data(proc[0].pid)
                print(f"spawn new process {functionName}->{args}")
                neo.close_conn()                        

    #spawn the process locally and return its details
    def __spawn_local_process(self, path_to_file, args, functionName):
        func_lib = importlib.import_module(path_to_file)
        func = getattr(func_lib, functionName)
        proc = mp.Process(target=func, args=args)
        proc.start()
        return [proc, time.time()]
    

if __name__ == "__main__":
    pass