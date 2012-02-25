#!/usr/bin/env python

"""
Copyright (C) 2011 Cameron Hayne (macdev@hayne.net)
This is published under the MIT Licence:
----------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from __future__ import division
import time

class Stopwatch(object):
    """
    The Stopwatch class provides a timer that can be started and stopped
    multiple times and which records the accumulated elapsed time.
    It is most conveniently used via the TimeSpent class which automatically
    creates Stopwatch instances and associates user-supplied names with them.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0
        self.startTime = None
        self.elapsedMillis = 0

    def start(self):
        if self.isRunning():
            return # calling 'start' on a running Stopwatch has no effect
        self.startTime = time.time()
        self.count += 1

    def stop(self):
        self.elapsedMillis = self.getElapsedMillis()
        self.startTime = None # indicates that it isn't running

    def isRunning(self):
        return (self.startTime is not None)

    def getElapsedMillis(self):
        elapsedMillis = self.elapsedMillis
        if self.startTime is not None: # it's running
            elapsedMillis += ((time.time() - self.startTime) * 1000)
        return elapsedMillis

    def getAvgElapsedMillis(self):
        if self.count == 0:
            return 0.0
        return self.getElapsedMillis() / self.count
# -----------------------------------------------------------------------------

class TimeSpent(object):
    """
    The TimeSpent class provides a simple way of intrumenting Python code
    to find out how much (wallclock) time is used by various parts of the code.
    To use it, you first create an instance of this class and then bracket the
    sections of code you want to measure with calls to the 'start' and 'stop'
    methods, supplying a name of your choice as the argument to these methods.
    For each distinct name, a Stopwatch instance is automatically created and it
    keeps track of the accumulated time between the calls to 'start' and 'stop'.
    At some suitable point in your program, call the 'generateReport' or
    'generateReportAndReset' method to get a string with a report of the times
    for each of the stopwatches. Each stopwatch also keeps track of how many
    times it was started and this count is part of the report.
    Example of use:
        timeSpent = TimeSpent()
        timeSpent.start("A")
        func1()
        func2()
        timeSpent.stop("A")
        boringFunc()
        timeSpent.start("B")
        func3()
        timeSpent.stop("B")
        timeSpent.start("A")
        func4()
        func5()
        timeSpent.stop("A")
        print timeSpent.generateReportAndReset()
    """

    _globalInstance = None

    @staticmethod
    def getGlobalInstance():
        """
        This method can be used to obtain a global instance of TimeSpent
        that is shared across all parts of your program.
        It is an alternative to creating your own TimeSpent instances as needed.
        Example of use:
            timeSpent = TimeSpent.getGlobalInstance()
            timeSpent.start("A")
            ... etc
        """
        if TimeSpent._globalInstance is None:
            TimeSpent._globalInstance = TimeSpent()
        return TimeSpent._globalInstance

    def __init__(self):
        self.stopwatches = dict() # indexed by name
        self.reportStopwatch = Stopwatch()
        self.reportStopwatch.start()

    def _getStopwatch(self, name, createIfNeeded=True):
        """
        Return the stopwatch with the specified name.
        If there is no stopwatch with that name and 'createIfNeeded' is True,
        a new stopwatch with that name is created (and returned).
        NB: this is intended only for internal use.
        """
        if createIfNeeded and name not in self.stopwatches:
            self.stopwatches[name] = Stopwatch()
        return self.stopwatches.get(name, None)

    def start(self, name):
        """
        Start the stopwatch with the specified name.
        If there is no stopwatch with that name, one is created (and started).
        """
        stopwatch = self._getStopwatch(name)
        if stopwatch.isRunning():
            print "WARNING: start(%s) called when stopwatch is already running" % name
        stopwatch.start()

    def stop(self, name):
        stopwatch = self._getStopwatch(name, False)
        if stopwatch is not None:
            stopwatch.stop()
        else:
            print "WARNING: unknown stopwatch name passed to 'stop' (%s)" % name

    def getElapsedMillis(self, name):
        stopwatch = self._getStopwatch(name)
        return stopwatch.getElapsedMillis()

    def getAvgElapsedMillis(self, name):
        stopwatch = self._getStopwatch(name)
        return stopwatch.getAvgElapsedMillis()

    def getCount(self, name):
        stopwatch = self._getStopwatch(name)
        return stopwatch.count

    def reset(self, name):
        # remove the stopwatch since it will get recreated if needed
        if name in self.stopwatches:
            del self.stopwatches[name]

    def resetAll(self):
        # remove the stopwatches since they will get recreated if needed
        self.stopwatches.clear()

    def generateReport(self):
        self.reportStopwatch.stop()
        secondsSinceReport = self.reportStopwatch.getElapsedMillis() / 1000.0
        self.reportStopwatch.reset()
        self.reportStopwatch.start()

        report = ""
        report += ("Elapsed seconds: %.1f\n" % secondsSinceReport)
        report += "Breakdown of time spent (in milliseconds):\n"
        for name in sorted(self.stopwatches.keys()):
            stopwatch = self.stopwatches[name]
            report += ("%s: %.0f (count: %d avg: %.1f)\n"
                       % (name,
                          stopwatch.getElapsedMillis(),
                          stopwatch.count,
                          stopwatch.getAvgElapsedMillis()))
        return report

    def generateReportAndReset(self):
        report = self.generateReport()
        self.resetAll()
        return report
# -----------------------------------------------------------------------------
