import Neo
import multiprocessing as mp
import os
import importlib
import inspect
import time

#TO DO
#1.Design Actual process allocation function
#2.Entity to send out heartbeats to slaves


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


class Magi():
    def __init__(self):
        self.free_port = 1234
        self.bookkeepers = []
        self.connected_to_queue = False
        self.neo = Neo.Neo()
        self.network_threads = {'127.0.0.1': os.cpu_count()}
        self.new_proc_num = 0
        self.local_procs = []
        self.master_init_procs = []
   
    def __del__(self):
        try:
            self.neo.close_conn()
        except:
            pass

    def register_network_thread(self,IP_ADDR):
        #tell magi about a network system
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
        print(args)
        proc = mp.Process(target=func,args=args)
        proc.start()
        return [proc, time.time()]


    def listen_for_orders(self):
        #run on network systems
        self.neo.start_server(PORT=6969)
        print("Magi slave online")
        while 1:
            
            #if no connection received in the timeslot
            #go and check existing connections for any timeouts
            if self.neo.get_new_conn(timeout = True) == "Timeout":
                order = "handle_proc_timers"
            else:    
                order = self.neo.receive_data()
                print(order)

            if order == 'registration':
                cores = os.cpu_count()
                self.neo.send_data(cores)
            
            elif order == 'spawn_process':
                fname = self.neo.receive_data()
                function_text = self.neo.receive_data()
                with open(f"tmp_{self.new_proc_num}.py","w") as f:
                    f.write(function_text)
                args = self.neo.receive_data()
                proc = self.spawn_local_process(f"tmp_{self.new_proc_num}", args, fname)
                self.local_procs.append(proc)
            
            elif order == "handle_proc_timers":
                now = time.time()
                for item in self.local_procs:
                    process_start_time = item[1]
                    if now - process_start_time > 3:
                        print(item, "has timed out")
                        item[0].terminate()#kill the proc
                        self.local_procs.remove(item)
                # TO DO : kill all child procs too


    ##CHECK THE IP!!!
    #this needs logic to choose a target ip
    def process(self,target,args = None):
        print("going to spawn a new proc")
        self.neo.connect_client(PORT=6969,IP = '192.168.1.87')
        self.neo.send_data("spawn_process")
        src = inspect.getsource(target)
        self.neo.send_data(str(target.__name__))
        self.neo.send_data(src)
        if type(args) == type((1,)):#wtf is this????
            pass
        else:
            args = (args,)
        self.neo.send_data(args)
        print("args",args)
        self.neo.close_conn()
        #proc = mp.Process(target=target, args=args)
        #return proc
        #TO DO : return something back to the master

    def queue(self):
        #generate new queue object, return details(port num, ip addr)
        self.bookkeepers.append(new_bookkeeper(self.free_port))
        self.bookkeepers[-1].start()
        self.free_port += 1
        return [self.free_port - 1, self.neo.get_my_ip()] 

    def queue_put(self,q_details, data):
        #add item to queue
        self.neo.connect_client(PORT=q_details[0], IP=q_details[1])
        self.neo.send_data(["put",data])
        data =  self.neo.receive_data()
        self.neo.close_conn()
        return data

    def queue_get(self,q_details):
        #get and pop item from queue
        self.neo.connect_client(PORT=q_details[0], IP=q_details[1])
        self.neo.send_data("get")
        data =  self.neo.receive_data()
        self.neo.close_conn()
        return data
    
    def kill_queues(self):
        while len(self.bookkeepers) > 0:
            p = self.bookkeepers.pop()
            p.kill()




if __name__ == "__main__":
    m = Magi()