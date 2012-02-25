

from libzCFDMeshEULERAIR import VariableAccess

var_access = VariableAccess()

var_list = var_access.get_variable_list()

for v in var_list:
    print 'Variable name: ', v[0], ' - alias:', v[1]
