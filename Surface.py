import Neo
import multiprocessing as mp
import os
import importlib
import inspect
import time
import gc
import sys

DEBUG = False#True

#TO DO
#1.Design Actual process allocation function
#2.Heartbeats need to be sent out as a group✔️
#3.Investigate fixed ports per Neo instance✔️
#4.Check if child procs get handled naturally
#5.Think of some way to 'join' procs
#6.Let Surface change the neo buffer read size dynamically

#spawn new bookkeeper
def new_bookkeeper(free_port):
    new_bookkeeper = mp.Process(target=bookkeeper,args = (free_port,))
    return new_bookkeeper

#bookkeepers are procs running on the master
#there is a bookkeeper for each queue
def bookkeeper(port):
    queue = []
    local_neo = Neo.Neo()
    local_neo.start_server(PORT=port)
    while True:
        local_neo.get_new_conn()
        rcvd = local_neo.receive_data()
        if rcvd == "get":
            if len(queue) == 0:
                data = None
            else:
                data = queue.pop(0)
            local_neo.send_data(data)

        elif rcvd[0] == "put":
            queue.append(rcvd[1])
            local_neo.send_data(True)

        elif rcvd == "debug":
            print(queue)
        
        elif rcvd == "kill":
            #print("terminate")
            break
        local_neo.close_conn()


class Surface():
    
    def __init__(self):
        self.free_port = 12345
        self.new_proc_num = 0
        self.bookkeepers = []
        self.local_procs = []
        self.network_threads = {}
        self.my_ip = Neo.Neo().get_my_ip()
        self.master_proc_init = mp.Queue()
        self.heart_thread = mp.Process(target=self.heart,args=(self.master_proc_init,))
        self.heart_thread.start()

    def __del__(self):
        try:
            self.heart_thread.terminate()
        except:
            pass
        for bk in self.bookkeepers:
            try:
                bk.terminate()
            except:
                pass

    #tell Surface about a network system
    def register_network_thread(self,IP_ADDR):
        if IP_ADDR in self.network_threads:
            return
        if IP_ADDR == '0.0.0.0' or IP_ADDR == '127.0.0.1':
            self.network_threads[IP_ADDR] = [os.cpu_count(), 0]            
        try:
            local_neo = Neo.Neo()
            local_neo.connect_client(PORT=6969,IP = IP_ADDR)
            local_neo.send_data('registration')
            num_cores = local_neo.receive_data()
            self.network_threads[IP_ADDR] = [num_cores, 0]#num cores, num procs
            local_neo.close_conn()
            return True
        except:
            print(f"error connecting to {IP_ADDR}")
            return False
    
    #spawn the process locally and return its details
    def __spawn_local_process(self, path_to_file, args, fname):
        func_lib = importlib.import_module(path_to_file)
        func = getattr(func_lib, fname)
        proc = mp.Process(target=func,args=args)
        proc.start()
        return [proc, time.time()]

    #run on network systems
    def listen_for_orders(self):
        local_neo = Neo.Neo()
        local_neo.start_server(PORT=6969)
        print("Surface slave online")
        while 1:
            #if no connection received in the timeslot
            #go and check existing connections for any timeouts
            if local_neo.get_new_conn(timeout = True) == "Timeout":
                order = "handle_proc_timers"
            else:    
                order = local_neo.receive_data()
            #return number of cores to registering entity
            if order == 'registration':
                cores = os.cpu_count()
                local_neo.send_data(cores)
                local_neo.close_conn()
                print("registration over")
            
            #receive function body and args and
            #spawn a new process
            elif order == 'spawn_process':
                fname = local_neo.receive_data()
                function_text = local_neo.receive_data()
                with open(f"tmp_{self.new_proc_num}.py","w") as f:
                    f.write(function_text)
                args = local_neo.receive_data()
                proc = self.__spawn_local_process(f"tmp_{self.new_proc_num}", args, fname)
                self.local_procs.append(proc)
                os.remove(f"tmp_{self.new_proc_num}.py")#remove temp file
                self.new_proc_num += 1
                local_neo.send_data(proc[0].pid)
                print(f"spawn new process {fname}->{args}")
                local_neo.close_conn()
            
            #check for timed out procs
            elif order == "handle_proc_timers":
                now = time.time()
                for item in self.local_procs:
                    process_start_time = item[1]
                    if now - process_start_time > 3:
                        print(item, "has timed out")
                        item[0].terminate()#kill the proc
                        self.local_procs.remove(item)

            #refresh proc times using received heartbeats
            elif order == "heartbeat":
                PIDs = local_neo.receive_data()
                now = time.time()
                print(f"heartbeats for PIDs:{PIDs} received {now}")
                for item in self.local_procs:
                    if item[0].pid in PIDs:
                        item[1] = now
                local_neo.close_conn()

    #send out heartbeats to slave devices    
    def heart(self, queue):
        procs = {}
        local_neo = Neo.Neo()#using a local neo inst is more reliable
        while 1:
            time.sleep(1)
            while(queue.empty() == False):
                proc = queue.get(block=False)
                if proc[0] not in procs:
                    procs[proc[0]] = [proc[1]]
                else:
                    procs[proc[0]].append(proc[1])
            if len(procs):
                print("*"*25)
                for IP in procs:
                    PIDs = procs[IP]
                    local_neo.close_conn()#clears remnant connections, need to debug
                    pass_ = False
                    while not pass_:
                        try:
                            local_neo.connect_client(PORT=6969,IP = IP)
                            local_neo.send_data("heartbeat")
                            local_neo.send_data(PIDs)
                            local_neo.close_conn()
                            pass_ = True
                            print(f"heartbeat sent to {IP} for PIDs:{PIDs}")
                        except:
                            time.sleep(0.1)
                print("*"*25)
                
    #actually sends out message to start process
    def __process_internal(self,target,args = None, IP='192.168.1.11'):
        local_neo = Neo.Neo()
        print("going to spawn a new proc")
        local_neo.connect_client(PORT=6969,IP = IP)
        local_neo.send_data("spawn_process")
        src = inspect.getsource(target)
        local_neo.send_data(str(target.__name__))
        local_neo.send_data(src)
        if str(type(args)) == "<class 'tuple'>":
            pass
        else:
            args = (args,)
        local_neo.send_data(args)
        pid = local_neo.receive_data()
        local_neo.close_conn()
        return (IP,pid)
        
    #wrapper to choose destination and spawn process
    def Process(self, target,args = None):
        min_load = float('inf')
        proc_target = None
        for target_machine in self.network_threads:
            print(self.network_threads[target_machine])
            cores = self.network_threads[target_machine][0]
            procs = self.network_threads[target_machine][1]
            load = procs/cores
            if load < min_load:
                proc_target = target_machine
        self.network_threads[proc_target][1] += 1
        details = self.__process_internal(target, args,IP=proc_target)
        self.master_proc_init.put(details)
    
    #generate new queue object, return details(port num, ip addr)
    def queue(self):
        self.bookkeepers.append(new_bookkeeper(self.free_port))
        self.bookkeepers[-1].start()
        self.free_port += 1
        return [self.free_port - 1, self.my_ip] 

    #add item to queue
    def queue_put(self,q_details, data):
        start_time = time.time()
        local_neo = Neo.Neo()
        status = None
        while status == None:
            try:
                local_neo.connect_client(PORT=q_details[0], IP=q_details[1])
                status = "pass"
            except:
                time.sleep(0.001)
                pass
        local_neo.send_data(["put",data])
        success =  local_neo.receive_data()
        local_neo.close_conn()
        end_time = time.time()
        if not success:
            return -1
        if DEBUG:
            with open("queue_logs.csv", 'a') as f:
                f.write(f"put,{end_time-start_time},{get_obj_size(data)}\n")
        return data

    #get and pop item from queue
    def queue_get(self,q_details):
        start_time = time.time()
        local_neo = Neo.Neo()
        status = None
        while status == None:
            try:
                local_neo.connect_client(PORT=q_details[0], IP=q_details[1])
                status = "pass"
            except:
                time.sleep(0.001)
                pass
        local_neo.send_data("get")
        data =  local_neo.receive_data()
        local_neo.close_conn()
        end_time = time.time()
        if DEBUG:
            with open("queue_logs.csv", 'a') as f:
                f.write(f"get,{end_time-start_time},{get_obj_size(data)}\n")        
        return data

    #delete all queues    
    def kill_queues(self):
        while len(self.bookkeepers) > 0:
            p = self.bookkeepers.pop()
            p.kill()

#from https://stackoverflow.com/a/53705610
def get_obj_size(obj):
    marked = {id(obj)}
    obj_q = [obj]
    sz = 0

    while obj_q:
        sz += sum(map(sys.getsizeof, obj_q))

        # Lookup all the object referred to by the object in obj_q.
        # See: https://docs.python.org/3.7/library/gc.html#gc.get_referents
        all_refr = ((id(o), o) for o in gc.get_referents(*obj_q))

        # Filter object that are already marked.
        # Using dict notation will prevent repeated objects.
        new_refr = {o_id: o for o_id, o in all_refr if o_id not in marked and not isinstance(o, type)}

        # The new obj_q will be the ones that were not marked,
        # and we will update marked with their ids so we will
        # not traverse them again.
        obj_q = new_refr.values()
        marked.update(new_refr.keys())
    return sz

if __name__ == "__main__":
    m = Surface()