#!/usr/bin/env python

import sys
import os
from zcfd import zCFDSolver


def RequiredModuleCheck():
    try:
        """import mpi4py
        import snakemq
        import numpy
        import cgen
        import jinja2
        import codepy
        import yaml
        import json
        import boto
        import starcluster"""
    except ImportError:
        print 'Please install mpi4py'
        sys.exit(1)


class launcher:
    """Simple Launcher"""

    def main(self):
        RequiredModuleCheck()
        # print libzCFDVersion.get_project_version()
        zcfd = zCFDSolver.zCFDSolver()
        zcfd.main()

# def launch():
#    launcher = launcher()
#    launcher.main()
#
# try:
#    import tau
#    tau.run('launch()')
# except ImportError:

if __name__ == "__main__":
    launcher = launcher()
    launcher.main()
