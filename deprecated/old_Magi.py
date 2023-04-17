import Neo
import multiprocessing as mp

def inner_magi():
    Neoconn = Neo.Neo()
    Neoconn.start_server(PORT=1234)
    queues = {}
    while True:
        addr = Neoconn.get_new_conn()
        ###('put'/'get', queueId, <opt> data)
        data = Neoconn.receive_data()
        queue_ID = data[1]
        if data[0] == 'put':
            if queue_ID not in queues:
                queues[queue_ID] = [data[2]]
            else:
                queues[queue_ID].append(data[2])
            #print("change!->",queues)
        if data[0] == 'get':
            if queue_ID not in list(queues.keys()):
                Neoconn.send_data(None)
            if len(queues[queue_ID]) == 0:
                Neoconn.send_data(-1)
            else:
                to_send = queues[queue_ID].pop()
                Neoconn.send_data(to_send)



class Magi():
    def __init__(self):
        self.queue_manager_proc = mp.Process(target=inner_magi, args=())
        self.queue_manager_proc.start()
        print("Magi Online")