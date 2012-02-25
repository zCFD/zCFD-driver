"""
Copyright (c) 2012, Zenotech Ltd
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL ZENOTECH LTD BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
#import json
import sys
import os
import yaml
from zcfd.utils import config

# Timestamp of parameter file when file was last read
last_timestamp = 0

class Parameters:
        
    default = '''
import zutil
    

parameters = { 

 # units for dimensional quantities
'units' : 'SI',

# reference state
'reference' : 'IC_1',

# restart from previous solution
'restart' : 'false',

'partitioner' : 'metis',

# time marching properties
'time marching' : { 
                   'unsteady' : {
                                 'total time' : 1.0,
                                 'time step' : 1.0,
                                 'order' : 'second',
                                 'start' : 3000,
                                },
                   'scheme' : {
                               'name' : 'runge kutta',
                               'stage': 5,
                               'kind' : 'local timestep',
                               },
                   # multigrid levels including fine mesh
                   'multigrid' : 4,            
                   'cfl': 2.0,
                   'cycles' : 1000,
                  },

'equations' : 'euler',

'euler' : {
      'order' : 'second',
      'limiter' : 'vanalbada',
      'precondition' : 'true',                                          
     },
'viscous' : {
        'order' : 'second',
        'limiter' : 'vanalbada',
       'precondition' : 'true',                                          
      },
'RANS' : {
               'order' : 'second',
               'limiter' : 'vanalbada',
               'precondition' : 'true',                                          
               'turbulence' : {
                               'model' : 'sst',
                              },
               },
'DES' : {
              'order' : 'second',
              'limiter' : 'vk',
              'precondition' : 'true',                                          
              'turbulence' : {
                              'model' : 'sst',
                              },
              },
'LES' : {
                  'order' : 'second',
                  'limiter' : 'vk',
                  'precondition' : 'true',                                          
                   'turbulence' : {
                                  'model' : 'sst',
                                  },
                  },
'material' : 'air',
'air' : {
        'gamma' : 1.4,
        'gas constant' : 287.0,
        'Sutherlands const': 110.4,
        'Prandtl No' : 0.72,
        'Turbulent Prandtl No' : 0.9,
        },
'IC_1' : {
          'temperature':273.15,
          'pressure':101325.0,
          'V': {
                'vector' : [1.0,0.0,0.0],
                # Used to define velocity mag if specified
                'Mach' : 0.5,
                },
           #'viscosity' : 0.0,
           'Reynolds No' : 1.0e6,
           'Reference Length' : 1.0, 
          'turbulence intensity': 0.01,
          'eddy viscosity ratio': 0.1,
          },
'IC_2' : {
          'reference' : 'IC_1',
          # total pressure/reference static pressure
          'total pressure ratio' : 1.0,
          # total temperature/reference static temperature
          'total temperature ratio' : 1.0,
          },
'IC_3' : {
          'reference' : 'IC_1',
          # static pressure/reference static pressure
          'static pressure ratio' : 1.0,
          },
'BC_1' : {
          'ref' : 7,
          'type' : 'symmetry',
         },
'BC_2' : {
          'ref' : 3,
          'type' : 'wall',
          'kind' : 'slip',
         },
'BC_3' : {
          'ref' : 9,
          'type' : 'farfield',
          'condition' : 'IC_1',
          'kind' : 'riemann',
         },
'BC_4' : {
          'ref' : 4,
          'type' : 'inflow',
          'kind' : 'default',
          'condition' : 'IC_2',
         },
'BC_5' : {
          'ref' : 5,
          'type' : 'outflow',
          'kind' : 'default',
          'condition' : 'IC_3',
         },
'write output' : {
                  'format' : 'vtk',
                  'surface variables': ['V','p','T','rho','cp','yplus'],
                  'volume variables': ['V','p','T','rho','eddy'],
                  'frequency' : 100,
                 },         
'report' : {
            'frequency' : 10,
          },                   
}

############################
#
# Variable list
#
# var_1 to var_n
# p,pressure
# T, temperature
#
############################

'''    
       
    def create_defaults(self):

        # Populate default parameters
        exec(self.default)
        
        config.parameters = locals()["parameters"]
        
        #config.logger.debug("Default Parameters: \n "+'\n '.join(['%s: %s' % (key, value) for (key, value) in config.parameters.items()]))
        
    def read(self,configfile):
        config.logger.debug(__file__+" "+__name__+":read")
        sys.path.insert(0,os.getcwd())
        configmodule = __import__(configfile)
        
        old_dict = configmodule.__dict__.copy()
        try:
            configmodule = reload(configmodule)
        except:
            configmodule.__dict__.update(old_dict)
                
        parameters = getattr(sys.modules[configfile],'parameters')
        # TODO Need to improve this
        config.parameters = dict(config.parameters, **parameters)
        
        props = os.stat(config.controlfile)
        global last_timestamp
        last_timestamp = props.st_mtime
        
        config.logger.debug("Parameters: \n "+'\n '.join(['%s: %s' % (key, value) for (key, value) in config.parameters.items()]))
        
    def read_if_changed(self,casename,configfile):
        global last_timestamp 
        props = os.stat(configfile)
        if props.st_mtime > last_timestamp:
            self.read(casename)
            return True
        return False
    
    def write(self,configfile):
        if config.logger != 0:
            config.logger.debug(__file__+" "+__name__+":write")
        # Open control file for writing
        fp = open(config.controlfile,"w")
        # Write control file in yaml format
        fp.write(self.default)

    def read_yaml(self):
        config.logger.debug(__file__+" "+__name__+":read_yaml")
        # Open control file for reading
        fp = open(config.controlfile,"r")
        # Merge control file with defaults
        config.parameters.update(yaml.load(fp))
        #print config.parameters['velocity'][0]
        
    def write_yaml(self):
        if config.logger != 0:
            config.logger.debug(__file__+" "+__name__+":write_yaml")
        # Open control file for writing
        fp = open(config.controlfile,"w")
        # Write control file in yaml format
        yaml.dump(config.parameters,fp,indent=2);
        
    def create_native(self):
        from cgen import (
            ArrayOf, POD,
            Block, \
            For, Statement, Struct)
        #=======================================================================
        # Line Comment Constant Pointer
        #=======================================================================
        from cgen import dtype_to_ctype
        import numpy

        members=[]
        code=[]

        for pk,pv in config.parameters.iteritems():
            if isinstance(pv, int):
                members.append(POD(numpy.int,pk))
                code.append(Statement("params.%s = extract<%s>(cppdict[\"%s\"])" % (pk,dtype_to_ctype(numpy.int), pk)))
            elif isinstance(pv, float):
                members.append(POD(numpy.float64,pk))
                code.append(Statement("params.%s = extract<%s>(cppdict[\"%s\"])" % (pk,dtype_to_ctype(numpy.float64), pk)))
            elif isinstance(pv, list):
                if isinstance(pv[0], int):
                    members.append(ArrayOf(POD(numpy.int,pk),len(pv)))
                    code.append(Block([Statement("list v = extract<%s>(cppdict[\"%s\"])" % (list.__name__,pk)),
                                       For("unsigned int i  = 0",
                                           "i<len(v)",
                                           "++i",
                                           Statement("params.%s[i] = extract<%s>(v[i])" % (pk,dtype_to_ctype(numpy.int)))
                                           ),
                                       ]))
                elif isinstance(pv[0], float):
                    members.append(ArrayOf(POD(numpy.float64,pk),len(pv)))
                    code.append(Block([Statement("list v = extract<%s>(cppdict[\"%s\"])" % (list.__name__,pk)),
                                       For("unsigned int i  = 0",
                                           "i < len(v)",
                                           "++i",
                                           Block([Statement("params.%s[i] = extract<%s>(v[i])" % (pk,dtype_to_ctype(numpy.float64))),
                                                  Statement("//std::cout << params.%s[i] << std::endl" % (pk))
                                                  ])
                                           ),
                                       ]))

        mystruct = Struct('Parameters',members)
        mycode = Block(code)

        #print mystruct
        #print mycode

        from jinja2 import Template

        tpl = Template("""
#include <boost/python.hpp>
#include <boost/python/object.hpp>
#include <boost/python/extract.hpp>
#include <boost/python/list.hpp>
#include <boost/python/dict.hpp>
#include <boost/python/str.hpp>
#include <stdexcept>
#include <iostream> 

{{my_struct}}

Parameters params;

void CopyDictionary(boost::python::object pydict) 
{
    using namespace boost::python;
    
    extract< dict > cppdict_ext(pydict);
    if(!cppdict_ext.check()){
        throw std::runtime_error(
                    "PassObj::pass_dict: type error: not a python dict.");
    }

    dict cppdict = cppdict_ext();
    list keylist = cppdict.keys();

    {{my_extractor}}


}

BOOST_PYTHON_MODULE({{my_module}})
{
   boost::python::def("copy_dict", &CopyDictionary);
}
        """)
        rendered_tpl = tpl.render(my_module="NativeParameters",my_extractor=mycode,my_struct=mystruct)
        
        #print rendered_tpl

        from codepy.toolchain import NVCCToolchain
        import codepy.toolchain

        kwargs = codepy.toolchain._guess_toolchain_kwargs_from_python_config()
        #print kwargs
        kwargs["cc"]="nvcc"
        #kwargs["cflags"]=["-m64","-x","cu","-Xcompiler","-fPIC","-ccbin","/opt/local/bin/g++-mp-4.4"]
        kwargs["cflags"]=["-m64","-x","cu","-Xcompiler","-fPIC"]
        kwargs["include_dirs"].append("/usr/local/cuda/include")
        kwargs["defines"]=[]
        kwargs["ldflags"]=["-shared"]
        #kwargs["libraries"]=["python2.7"]
        kwargs["libraries"]=["python2.6"]
        print kwargs
        toolchain=NVCCToolchain(**kwargs)

        from codepy.libraries import add_boost_python
        add_boost_python(toolchain)


        from codepy.jit import extension_from_string
        mymod = extension_from_string(toolchain, "NativeParameters", rendered_tpl)

        mymod.copy_dict(config.parameters)
