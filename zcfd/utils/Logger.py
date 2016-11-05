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
import libzCFDLogger
from zMessage import Message

class Logger:
    """Wrapper for C++ based logger"""

    def __init__(self,rank,filename='BLANK',connector=0):
        self.logger = libzCFDLogger.getLogger()
        self.connector = connector

        try:
            fh = libzCFDLogger.FileLogger(filename);
        except Exception, e:
            print e
            raise

        self.logger.addHandler(fh)

        self.filelogger = fh
        if rank == 0 and connector == 0:
            ch = libzCFDLogger.StdOutLogger()
            self.logger.addHandler(ch)
            self.streamlogger = ch

        self.debug('Initialised Logging for rank %s' % (rank))

    def info(self,message):
        self.logger.info(message)
        if self.connector != 0:
            self.connector.send_message(Message.log(message))

    def debug(self,message):
        self.logger.debug(message)

    def error(self,message):
        self.logger.error(message)
        if self.connector != 0:
            self.connector.send_message(Message.log(message))