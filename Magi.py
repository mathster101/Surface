import Neo
import multiprocessing as mp
import os
import importlib
import inspect
import time
import queue

#TO DO
#1.Design Actual process allocation function
#2.Heartbeats need to be sent out as a group
#3.Investigate fixed ports per Neo instance

#spawn new bookkeeper
def new_bookkeeper(free_port):
    new_bookkeeper = mp.Process(target=bookkeeper,args = (free_port,))
    return new_bookkeeper

#bookkeepers are procs running on the master
#there is a bookkeeper for each queue
def bookkeeper(port):
    queue = []
    neo_inst = Neo.Neo()
    neo_inst.start_server(PORT=port)
    #neo_inst.get_new_conn()
    while True:
        neo_inst.get_new_conn()
        rcvd = neo_inst.receive_data()
        if rcvd == "get":
            if len(queue) == 0:
                data = None
            else:
                data = queue.pop()
            neo_inst.send_data(data)

        elif rcvd[0] == "put":
            queue.append(rcvd[1])
            neo_inst.send_data("done")

        elif rcvd == "debug":
            print(queue)
        
        elif rcvd == "kill":
            #print("terminate")
            break
        neo_inst.close_conn()


class Magi():
    
    def __init__(self):
        self.free_port = 1234
        self.new_proc_num = 0
        self.bookkeepers = []
        self.local_procs = []
        self.network_threads = {'127.0.0.1': os.cpu_count()}
        self.neo = Neo.Neo()
        self.my_ip = self.neo.get_my_ip()
        self.master_proc_init = mp.Queue()
        self.heart_thread = mp.Process(target=self.heart,args=(self.master_proc_init,))
        self.heart_thread.start()

    def __del__(self):
        try:
            self.neo.close_conn()
        except:
            pass
    
    #tell magi about a network system
    def register_network_thread(self,IP_ADDR):
        try:
            self.neo.connect_client(PORT=6969,IP = IP_ADDR)
            self.neo.send_data('registration')
            num_cores = self.neo.receive_data()
            self.network_threads[IP_ADDR] = num_cores
            self.neo.close_conn()
        except:
            print(f"error connecting to {IP_ADDR}")
    
    #spawn the process locally and return its details
    def spawn_local_process(self, path_to_file, args, fname):
        func_lib = importlib.import_module(path_to_file)
        func = getattr(func_lib, fname)
        proc = mp.Process(target=func,args=args)
        proc.start()
        return [proc, time.time()]

    #run on network systems
    def listen_for_orders(self):
        self.neo.start_server(PORT=6969)
        print("Magi slave online")
        while 1:
            
            #if no connection received in the timeslot
            #go and check existing connections for any timeouts
            if self.neo.get_new_conn(timeout = True) == "Timeout":
                order = "handle_proc_timers"
            else:    
                order = self.neo.receive_data()

            if order == 'registration':
                cores = os.cpu_count()
                self.neo.send_data(cores)
                self.neo.close_conn()
                print("registration over")
            
            elif order == 'spawn_process':
                fname = self.neo.receive_data()
                function_text = self.neo.receive_data()
                with open(f"tmp_{self.new_proc_num}.py","w") as f:
                    f.write(function_text)
                args = self.neo.receive_data()
                proc = self.spawn_local_process(f"tmp_{self.new_proc_num}", args, fname)
                self.local_procs.append(proc)
                os.remove(f"tmp_{self.new_proc_num}.py")
                self.new_proc_num += 1
                ###############
                self.neo.get_new_conn(timeout = False)
                self.neo.send_data(proc[0].pid)
                print(f"spawn new process {fname}->{args}")
                self.neo.close_conn()
                
            elif order == "handle_proc_timers":
                now = time.time()
                for item in self.local_procs:
                    process_start_time = item[1]
                    if now - process_start_time > 6:
                        print(item, "has timed out")
                        item[0].terminate()#kill the proc
                        self.local_procs.remove(item)
                # TO DO : kill all child procs too

            elif order == "heartbeat":
                PID = self.neo.receive_data()
                print(f"heartbeat for PID:{PID} received ",end='')
                for item in self.local_procs:
                    if str(item[0].pid) == PID:
                        item[1] = time.time()
                        print(item[1])
                self.neo.close_conn()


    #send out heartbeats to slave devices    
    def heart(self, queue):
        procs = []
        local_neo = Neo.Neo()#using a local neo inst is more reliable
        while 1:
            while(queue.empty() == False):
                proc = queue.get(block=False)
                procs.append(proc)
            time.sleep(1)
            if len(procs):
                print("*"*25)
                for p in procs:
                    IP = p.split(":")[0]
                    PID = p.split(":")[1]
                    local_neo.close_conn()#clears remnant connections, need to debug
                    pass_ = False
                    while not pass_:
                        try:
                            local_neo.connect_client(PORT=6969,IP = IP)
                            local_neo.send_data("heartbeat")
                            local_neo.send_data(PID)
                            local_neo.close_conn()
                            pass_ = True
                        except:
                            time.sleep(0.1)
                    print(f"hearbeat sent to {IP} for PID:{PID}")
                print("*"*25)
                
    #actually sends out message to start process
    def process_internal(self,target,args = None, IP='192.168.1.87'):
        print("going to spawn a new proc")
        self.neo.connect_client(PORT=6969,IP = IP)
        self.neo.send_data("spawn_process")
        src = inspect.getsource(target)
        self.neo.send_data(str(target.__name__))
        self.neo.send_data(src)
        if str(type(args)) == "<class 'tuple'>":
            pass
        else:
            args = (args,)
        self.neo.send_data(args)
        self.neo.close_conn()
        #doesn't work without a reconn
        self.neo.connect_client(PORT=6969,IP = IP)
        pid = self.neo.receive_data()
        self.neo.close_conn()
        return f"{IP}:{pid}"
        
    #wrapper to choose destination and spawn process
    def Process(self, target,args = None):
        global master_init_procs
        details = self.process_internal(target, args)
        self.master_proc_init.put(details)
    
    #generate new queue object, return details(port num, ip addr)
    def queue(self):
        self.bookkeepers.append(new_bookkeeper(self.free_port))
        self.bookkeepers[-1].start()
        self.free_port += 1
        return [self.free_port - 1, self.my_ip] 


    #add item to queue
    def queue_put(self,q_details, data):
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
        data =  local_neo.receive_data()
        local_neo.close_conn()
        return data

    #get and pop item from queue
    def queue_get(self,q_details):
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
        return data

    #delete all queues    
    def kill_queues(self):
        while len(self.bookkeepers) > 0:
            p = self.bookkeepers.pop()
            p.kill()




if __name__ == "__main__":
    m = Magi()