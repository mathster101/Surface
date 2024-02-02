import multiprocessing as mp
import time
import Neo
import os
import importlib
import inspect
import textwrap

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
        ###heart stuff###################
        self.netClients = {}
        self.netProcs = []
        self.process2heart = self.man.Queue()
        self.heartProc = mp.Process(target = self.heart)
        self.heartProc.start()

    def __del__(self):
        self.dmaster.kill()
        for agent in self.agents:
            agent.kill()

    def dataMaster(self):
        print("DATAMASTER -> ONLINE")
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
        print(f"AGENT -> ONLINE PORT:{port}")
        send, recv = queues
        neo = Neo.Neo()    
        neo.start_server(PORT=port)
        neo.get_new_conn()
        print(f"Remote process connected to port: {port}")
        while True:
            orderrcvd = neo.receive_data()
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
        agentPort = self.agentPort - 1
        newAgent = mp.Process(target=self.Agent, args = (agentPort, [a, b]))
        self.agents.append(newAgent)
        self.agents[-1].start()

        if len(self.netClients) == 0:
            print("[ERROR]: NO SLAVES REGISTERED")
            return -1
        
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
            #print(proc_target, "chosen")
            self.netClients[proc_target][1] += 1
            details = self.__process_internal(target, args, IP=proc_target, agentPort = agentPort)
            self.netProcs.append(details)#store IP and PID on slave
            self.process2heart.put(details)

    def __process_internal(self, target, args = None, IP = None, agentPort = None):
        neo = Neo.Neo()
        neo.connect_client(PORT=6969,IP = IP)
        neo.send_data("spawn_process")
        src = inspect.getsource(target)
        src = textwrap.dedent(src)
        neo.send_data(str(target.__name__))
        neo.send_data(generateSlaveQCode(IP = self.masterIP, PORT = agentPort)
                       + src)
        if str(type(args)) == "<class 'tuple'>":
            pass
        else:
            args = (args,)
        neo.send_data(args)
        PID = neo.receive_data()#PID on slave
        neo.close_conn()
        return (IP,PID)

    def registerMaster(self,masterIP):
        self.masterIP = masterIP

    def registerClient(self, IP_ADDR):
        if IP_ADDR in self.netClients:
            return True
        try:
            neo = Neo.Neo()
            neo.connect_client(PORT=6969,IP = IP_ADDR)
            neo.send_data('registration')
            num_cores = neo.receive_data()
            self.netClients[IP_ADDR] = [num_cores, 0]#num cores, num procs
            neo.close_conn()
            return True
        except:
            print(f"{IP_ADDR} is offline")
            return False            

    def heart(self):
        processes = []
        IP2PIDmap = {}
        neo = Neo.Neo()
        print("HEART -> ONLINE")
        while True:
            while not self.process2heart.empty():
                proc = self.process2heart.get()
                processes.append(proc)
            for proc in processes:
                IP, PID = proc
                if IP not in IP2PIDmap:
                    IP2PIDmap[IP] = []
                if PID not in IP2PIDmap[IP]:
                    IP2PIDmap[IP].append(PID)
            for IP in IP2PIDmap:#send PIDs to correct slave IPs
                neo.connect_client(PORT=6969,IP = IP)
                neo.send_data("heartbeat")
                neo.send_data(IP2PIDmap[IP])
                neo.close_conn()
            time.sleep(0.250)

################################################################  
    
class Surface_slave:
    def __init__(self):
        self.procsRcvd = 0
        self.localProcs = []
    
    def startListener(self):
        neo = Neo.Neo()
        neo.start_server(PORT=6969)
        print("Surface slave online")
        while True:
            #handle heartbeat timers if no orders
            if neo.get_new_conn(timeout = True) == "Timeout":
                order = "handle_proc_timers"
            else:    
                order = neo.receive_data()   

            #return number of cores to master
            if order == 'registration':
                cores = os.cpu_count()
                neo.send_data(cores)
                neo.close_conn()
                print(f"[Order]: Registration request")
            
            #receive function body and args and
            #spawn a new process
            elif order == 'spawn_process':
                functionName = neo.receive_data()
                functionText = neo.receive_data()
                with open(f"tmp_{self.procsRcvd}.py","w") as f:
                    f.write(functionText)
                args = neo.receive_data()
                proc = self.__spawn_local_process(f"tmp_{self.procsRcvd}", args, functionName)
                self.localProcs.append(proc)
                os.remove(f"tmp_{self.procsRcvd}.py")#remove temp file
                self.procsRcvd += 1
                neo.send_data(proc[0].pid)
                neo.close_conn()                 
                print(f"[Order]: Function spawn --> {functionName}")       

            #receive heartbeat and PIDs to keep alive
            elif order == "heartbeat":
                now = time.time()
                rcvdPIDs = neo.receive_data()
                print(f"[heartbeat]: {rcvdPIDs} : {now}")
                for proc in self.localProcs:
                    PID = proc[0].pid
                    time_ = proc[1]
                    if PID in rcvdPIDs:
                        proc[1] = now
                neo.close_conn()
            
            elif order == "handle_proc_timers":
                now = time.time()
                for proc in self.localProcs:
                    lastHeartbeat = proc[1]
                    if now - lastHeartbeat > 1.5:
                        proc[0].terminate()
                        self.localProcs.remove(proc)
                        print(f"[timeout]: {proc[0].pid}")

    #spawn the process locally and return its details
    def __spawn_local_process(self, path_to_file, args, functionName):
        func_lib = importlib.import_module(path_to_file)
        func = getattr(func_lib, functionName)
        if args == (None,):
            proc = mp.Process(target=func)
        else:
            proc = mp.Process(target=func, args=args)
        proc.start()
        return [proc, time.time()]

################################################################  

def generateSlaveQCode(IP, PORT):
    text = f"""class queueConnect:
    def __init__(self):
        import time
        time.sleep(0.2)
        self.IP = "{IP}"
        self.port = {PORT}
        self.neo = Neo.Neo()
        self.neo.connect_client(PORT=self.port, IP=self.IP)
    
    def queuePut(self, data, queueId):
        self.neo.send_data([["PUT", data], queueId])    
    
    def queueGet(self, queueId):
        self.neo.send_data(["GET", queueId])
        data = self.neo.receive_data()
        return data\n#####################\n"""
    return "import Neo\n" + textwrap.dedent(text)

if __name__ == "__main__":
    pass
