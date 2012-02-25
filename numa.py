import os
import sys
import subprocess

def whereis(program):
    for path in os.environ.get('PATH', '').split(':'):
        if os.path.exists(os.path.join(path, program)) and \
               not os.path.isdir(os.path.join(path, program)):
            return os.path.join(path, program)
    return None

class NumaNode:
    def __init__(self,node_number,cpu_list,memorysize,memoryfree,processcount):
        self.node_number = node_number
        self.cpu_list = cpu_list
        self.memorysize = memorysize
        self.memoryfree = memoryfree
        self.processcount = processcount

class VMprocessInfo:
    def __init__(self,vm_name,processid,vcpu_num):
        self.vm_name = vm_name
        self.processid = processid
        self.vcpu_num = vcpu_num

#Python numactl output parsing

def parsenumactl():
    process = subprocess.Popen(['numactl --hardware | grep cpu'], shell=True, stdout=subprocess.PIPE)
    cpu_list = process.communicate()
    process = subprocess.Popen(['numactl --hardware | grep size'], shell=True, stdout=subprocess.PIPE)
    mem_list = process.communicate()
    process = subprocess.Popen(['numactl --hardware | grep free'], shell=True, stdout=subprocess.PIPE)
    memfree_list = process.communicate()
    cpu_list = str.splitlines(cpu_list[0])
    mem_list = str.splitlines(mem_list[0])
    memfree_list = str.splitlines(memfree_list[0])
    node_list = {}
    for index in range(len(cpu_list)):
        node_list[index]=NumaNode(str.split(cpu_list[index])[1], str.split(cpu_list[index])[3:], str.split(mem_list[index])[3], str.split(memfree_list[index])[3], 0)
    return node_list

def numa_capable():
    numa_capable = 0
    
    if whereis('numactl') == None:
        return numa_capable
    
    process = subprocess.Popen(['numactl --hardware | grep available'], shell=True, stdout=subprocess.PIPE)
    test_available = process.communicate()
    test_available = str.splitlines(test_available[0])
    if int(str.split(test_available[0])[1]) > 1:
        numa_capable = 1
    return numa_capable
