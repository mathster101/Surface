import Neo
import multiprocessing as mp
import os

def new_bookkeeper(free_port):
    new_bookkeeper = mp.Process(target=bookkeeper,args = (free_port,))
    return new_bookkeeper

def bookkeeper(port):
    queue = []
    neo_inst = Neo.Neo()
    neo_inst.start_server(PORT=port)
    neo_inst.get_new_conn()
    while True:
        #neo_inst.get_new_conn()
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

    def __del__(self):
        try:
            self.neo.close_conn()
        except:
            pass

    def register_network_thread(self,IP_ADDR):
        #tell magi about a network system
        try:
            self.neo.connect_client(PORT=6969,IP = IP_ADDR)
            self.neo.send_data('initial_heartbeat_check')
            num_cores = self.neo.receive_data()
            self.network_threads[IP_ADDR] = num_cores
        except:
            print(f"error connecting to {IP_ADDR}")
    
    def listen_for_orders(self):
        #run on network systems
        self.neo.start_server(PORT=6969)
        print("Magi slave online")
        while 1:
            self.neo.get_new_conn()
            order = self.neo.receive_data()
            if order == 'initial_heartbeat_check':
                cores = os.cpu_count()
                self.neo.send_data(cores)
                print("heartbeat sent")
            
            elif order == 'spawn_process':
                function_text = self.neo.receive_data()
                

            #self.neo.close_conn()

    def process(self,target,args):
        proc = mp.Process(target=target, args=args)
        return proc

    def queue(self):
        #generate new queue object, return details(port num, ip addr)
        self.bookkeepers.append(new_bookkeeper(self.free_port))
        self.bookkeepers[-1].start()
        self.free_port += 1
        return [self.free_port - 1, self.neo.get_my_ip()] 

    def queue_put(self,q_details, data):
        #add item to queue
        if not self.connected_to_queue:
            self.neo.connect_client(PORT=q_details[0], IP=q_details[1])
            self.connected_to_queue = True
        self.neo.send_data(["put",data])
        return self.neo.receive_data()

    def queue_get(self,q_details):
        #get and pop item from queue
        if not self.connected_to_queue:
            self.neo.connect_client(PORT=q_details[0], IP=q_details[1])
            self.connected_to_queue = True
        self.neo.send_data("get")
        return self.neo.receive_data()
    
    def kill_queues(self):
        while len(self.bookkeepers) > 0:
            p = self.bookkeepers.pop()
            p.kill()




if __name__ == "__main__":
    m = Magi()