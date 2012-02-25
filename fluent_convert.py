#!/bin/env python
import sys

import libzCFDIO_INTEL as fluent


converter = fluent.FluentReader();

converter.convert(sys.argv[1],sys.argv[2])
