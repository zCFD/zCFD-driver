

from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log


class MQplugin(ClusterSetup):
    #def __init__(self):
        
        
    def run(self, nodes, master, user, user_shell, volumes):
        
        # install snakemq on master
        log.info("Installing snakemq on master")
        master.ssh.execute('easy_install snakemq')
        
        # Copy code to master
        log.info("Copying zMQ to master")
        master.ssh.put('/tmp/zMQ.py','zMQ.py')
        
        # Start MQ
        log.info("Starting zMQ on master")
        master.ssh.execute('python zMQ.py >&zMQ.log&</dev/null')
        
        # Install prerequisites on compute nodes
        log.info("Installing python prerequisites")
        for node in nodes:
            self.pool.simple_job(node.ssh.put, '/tmp/requirements.txt','requirements.txt', jobid=node.alias)
        self.pool.wait(len(nodes))
        for node in nodes:
            self.pool.simple_job(node.ssh.execute, 'easy_install requirements.txt', jobid=node.alias)
        self.pool.wait(len(nodes))
        
        

