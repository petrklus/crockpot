import datetime, time
import collections
import logging
import sys
import yaml
import Queue
import time
import pickle
import threading
import json
logging.basicConfig(level=logging.DEBUG)


sensor_data = collections.deque(maxlen=50000)
lines = collections.deque(maxlen=100)

record_number = 0
def command_reader():
    global record_number
    while True:
        try:
            a = dataQ.get()
            if len(a) > 1:
                d_time = datetime.datetime.fromtimestamp(a[0])
                time_formatted = d_time.strftime('%H:%M:%S')
                lines.append("{}: {}".format(time_formatted, str(a[1]).strip()))                
                # now parse the command:                
                text_contents = a[1].strip()
                logging.debug("Processing packet: {}".format(text_contents))                
                if text_contents[:4] != "[[DP" or text_contents[-2:] != "]]":
                    raise Exception(
                        "Invalid packet start {}".format(text_contents))
                readings = text_contents[4:-2].split(",")
                
                digi_temp, resistor_val, dimming_val = map(lambda x: x.strip(), readings)

                timestamp = int(a[0])                
                sensor_data.append({
                    "time" : timestamp,
                    "digi_temp" : digi_temp,
                    "resistor_val" : resistor_val,
                    "dimming_val" : dimming_val,
                })

                if record_number%50000:
                    with open("logs/log_{}.pckl".format( d_time.strftime('%Y%m%d-%H_%M_%S')), "w") as fp:
                        pickle.dump(list(sensor_data), fp)
                    record_number = 0
                record_number += 1
                
                logging.debug("T{}, R{}, D{}".format(digi_temp, resistor_val, dimming_val))
                                
        except Exception as e:
            logging.info("Unable to parse packet: {}, {}".format(a, e))


##### command sending dispatcher
command_q = collections.deque(maxlen=2)

class GenericCommandWrapper(object):   
    
    def __init__(self, num, *args, **kwargs):
        self.button_number = num
    
    def run_action(self):
        s = self.button_number
        if s == "0":
            text = "0"            
        elif s == "1":
            text = "1"
        elif s == "2":
            text = "2"
        elif s == "3":
            text = "3"
        elif s == "4":
            text = "4"
        else:
            raise Exception("Unknown command")
        
        ser.write(text)
        logging.debug("Command sent {}".format(text))   
 

def command_sender():
    while True:        
        # queue fetching 
        while True:
            try:
                item = command_q.pop() #non-blocking call                       
                break # break out of the fetching loop, we have item
            except IndexError:
                # wait for tiny bit between checking
                time.sleep(0.1)
                # continue
                continue
        # TODO try twice/check confirmation?
        try:
            logging.info(item.run_action())
            logging.debug("Command sent")
        except Exception as e:
            msg = "Error send: {}".format(e)
            logging.warn(msg)
            logging.exception(e)
        # wait between issuing commands
        time.sleep(5)





from bottle import route, run, template, view, static_file

@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='static')

@route('/static/css/<filename>')
def server_static(filename):
    return static_file(filename, root='static/css')
from bottle import static_file

@route('/static/js/<filename>')
def server_static(filename):
    return static_file(filename, root='static/js')

from bottle import static_file
@route('/static/fonts/<filename>')
def server_static(filename):
    return static_file(filename, root='static/fonts')


output_template = """<html>
    <head>
        <meta name="author" content="Petr">
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="2">
    </head>
    <body>
        <pre>{}</pre>
    </body>
</html>
"""

@route('/read')
def read_out():
    # trigger_read()
    return output_template.format("\n".join(list(lines)[::-1]))

@route('/read_sensor_data')
def read_sensor_data():
    # get latest 100 values
    return json.dumps(list(sensor_data)[::-1][:100])



@route('/button/<num>')
def button(num):
    logging.info("Button {} pressed".format(num))
    command = GenericCommandWrapper(num)
    command_q.append(command)      
    return hello()


@route('/hello')
@route('/hello/<name>')
@view('templates/index.tmpl')
def hello(name='World'):
    return dict(name=name)


from serialreader import SerialCommunicator

if __name__ == "__main__":
    
    try: 
        # load up config
        with open("config.yaml") as fp:
            CONFIG = yaml.safe_load(fp)
    except Exception, e:
        logging.exception("Unable to read config, please create config.yaml following a sample")
        sys.exit(1)
    
    # command and error queues
    dataQ = Queue.Queue(maxsize=100)
    errQ = Queue.Queue(maxsize=100)

    # serial port monitoring
    mock_serial = False
    if mock_serial:
        import os, pty, serial
        master, slave = pty.openpty()
        s_name = os.ttyname(slave)
        ser = SerialCommunicator(dataQ, errQ, port=s_name, baudrate=9600)
    else:
        ser = SerialCommunicator(
            dataQ, errQ, 
            port=CONFIG["arduino_port"], baudrate=CONFIG["arduino_baudrate"])
    ser.daemon = True
    ser.start()
    
        
    # start command reader
    num_worker_threads = 1
    for i in range(num_worker_threads):
         t = threading.Thread(target=command_reader)
         t.daemon = True
         t.start()
    
    # start command dispatcher    
    sender = threading.Thread(target=command_sender)
    sender.daemon = True
    sender.start()
    
    
    run(host='0.0.0.0', port=CONFIG["webserver_port"])

