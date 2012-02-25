
import threading
import zMQ
from zMQ import Connector
import argparse
import yaml
import zMessage

class zClient:
    """ Client to talk to a service using zMQ Messaging system"""
    def __init__(self):
        
        parser = argparse.ArgumentParser(description="zClient command line arguments")
        group = parser.add_mutually_exclusive_group()
        parser.add_argument('--host', help='Service host',required=True)
        parser.add_argument('--viewlog', dest='viewlog', action='store_const', const=True, default=False, help='View log')
        group.add_argument('--start', dest='start', action='store_const', const=True, default=False, help='Start solver')
        group.add_argument('--stop', dest='stop', action='store_const', const=True, default=False, help='Stop solver')
        group.add_argument('--dump', dest='dump', action='store_const', const=True, default=False, help='Force a solution dump from solver')
        parser.add_argument('--config', dest='configfile', default='BLANK', help='Configuration file name')
        self.args = parser.parse_args()
        
        self.interrupt = False
        # Set the signal handler
        #signal.signal(signal.SIGTERM, self.handler)
        # start the connector
        print('Connecting to Message Q at',self.args.host,4000) 
        self.conn = Connector(self.args.host,4000)
        self.conn.run()
 

    def handler(self,signum, frame):
        print 'Signal handler called with signal', signum
        self.interrupt = True

    def getLog(self):
        """Blocking function gets the logger output from the service"""        
        while not self.interrupt:
            item = self.conn.q.get()  # This will block if queue empty
            if zMessage.Message.is_log(item):  # Check contents of message
                print zMessage.Message.get_log(item) # TODO would be best to send output to consumer rather than print
            self.conn.q.task_done()   # Mark task as processed
            
    def stop(self):
        self.conn.stop()

    def run(self):
        """Runs the client"""
        if self.args.configfile != 'BLANK':  # Send config file if defined
            fp = open(self.args.configfile,"r") # Open control file for reading
            params = yaml.load(fp)  # Get config file as a dictionary
            params['case_name'] = self.args.configfile[:self.args.configfile.rfind('.ctl.yaml')] # Take case name from the name of config file
            if 'problem_name' not in params:  # Check if problem name defined
                params['problem_name'] = params['case_name']
            if 'solver' not in params: # Check if solver type defined
                print 'Error: Solver not defined in control file'
                exit(-1)           
            self.conn.send_message(zMessage.Message.config(yaml.dump(params)))  # Send configuration message to service
         
        if self.args.start: # Send start message - Do we need this? Sending config file is an implicit start
            self.conn.send_message(zMessage.Message.start())
        
        if self.args.stop: # Send stop message 
            self.conn.send_message(zMessage.Message.stop())
        
        if self.args.dump: # Send a dump (checkpoint) message
            self.conn.send_message(zMessage.Message.dump())
        
        # This needs to be last as it is a blocking call
        if self.args.viewlog: # View logger output
            print("Press any key to terminate")
            ts = threading.Thread(target=self.getLog) # Create connector on separate thread
            ts.setDaemon(True)
            ts.start() # Note this thread wont complete - call stop to enable thread to complete
            zMQ.getch()
            self.interrupt = True
                
            

if __name__ == "__main__":
    client = zClient()
    client.run()
    client.stop()
    print "Completed..."