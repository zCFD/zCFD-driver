import sys
from time import sleep
import zMQ

if __name__ == "__main__":
    host = sys.argv[1]
    port = int(sys.argv[2])
    zmq = zMQ.Connector(host,port)
    zmq.run()
    sleep(2)
    while True:
        zmq.send_message(b"LOG:Test")
        sleep(10)
        
    zmq.stop()
    print "Completed"
