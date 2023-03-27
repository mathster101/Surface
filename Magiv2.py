import Neo
import multiprocessing as mp

def conn_handler():
    bookkeeper_list = []
    free_port = 1235
    neo_inst = Neo.Neo()
    neo_inst.start_server(PORT=1234)
    print("Front End Online")
    while True:
        neo_inst.get_new_conn()
        neo_inst.send_data(free_port)
        new_bookkeeper = mp.Process(target=bookkeeper,args = (free_port,))
        bookkeeper_list.append(new_bookkeeper)
        bookkeeper_list[-1].start()
        free_port += 1


def bookkeeper(port):
    queue = []
    neo_inst = Neo.Neo()
    neo_inst.start_server(PORT=port)
    neo_inst.get_new_conn()
    while True:
        rcvd = neo_inst.receive_data()
        if rcvd == "get":
            if len(queue) == 0:
                data = None
            else:
                data = queue.pop()
            neo_inst.send_data(data)

        elif rcvd[0] == "put":
            queue.append(rcvd[1])
        
        elif rcvd == "debug":
            print(queue)



class Magi():
    def __init__(self):
        self.conn_handler_proc = mp.Process(target=conn_handler, args=())
        self.conn_handler_proc.start()


if __name__ == "__main__":
    m = Magi()