#!/bin/env python
import sys
import os

import libzCFDIO_INTEL as fluent


if len(sys.argv) != 3:
    print 'Usage: fluent.{msh | cas}  zcfd.h5'
    sys.exit()
    
fluent_mesh = sys.argv[1]
zcfd_mesh = sys.argv[2]

# Check if fluent files exist
if os.path.isfile(fluent_mesh) == False:
    print 'Fluent mesh file does not exist, check location of file to be converted'
    sys.exit()
    
if os.path.isfile(zcfd_mesh):
    print 'zCFD mesh file already exists please delete before converting'
    sys.exit()

converter = fluent.FluentReader();

print 'Converting '+fluent_mesh+' to '+zcfd_mesh

converter.convert(fluent_mesh,zcfd_mesh)
