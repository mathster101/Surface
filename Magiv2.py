import Neo
import multiprocessing as mp



def new_bookkeeper(free_port):
    new_bookkeeper = mp.Process(target=bookkeeper,args = (free_port,))
    return new_bookkeeper


def bookkeeper(port):
    queue = []
    neo_inst = Neo.Neo()
    neo_inst.start_server(PORT=port)
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
    
    def Queue(self):
        self.bookkeepers.append(new_bookkeeper(self.free_port))
        self.bookkeepers[-1].start()
        self.free_port += 1
        return self.free_port - 1 



if __name__ == "__main__":
    m = Magi()