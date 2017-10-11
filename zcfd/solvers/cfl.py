"""
Copyright (c) 2012-2017, Zenotech Ltd
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Zenotech Ltd nor the
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


def exp_ramp(solve_cycle, real_time_cycle, cfl):
    if cfl.cfl_ramp > 1.0 and real_time_cycle == 0 and solve_cycle < 500:
        return min(cfl.min_cfl * cfl.cfl_ramp ** (max(0, solve_cycle - 1)), cfl.max_cfl)
    else:
        return cfl.max_cfl


class CFL:

    def __init__(self, cfl):
        self.min_cfl = cfl
        self.max_cfl = cfl
        self.current_cfl = cfl
        self.coarse_cfl = cfl
        self.transport_cfl = cfl
        self.cfl_ramp = 1.0
        self.cfl_pmg = []
        self.transport_cfl_pmg = []

    @property
    def cfl(self):
        return self.current_cfl

    def pmg_cfl(self,pmg_level):
        if len(self.cfl_pmg) > pmg_level:
            return self._scale_factor * self.cfl_pmg[pmg_level]
        else:
            return self.cfl        

    def pmg_transport(self,pmg_level):
        if len(self.transport_cfl_pmg) > pmg_level:
            return self._scale_factor * self.transport_cfl_pmg[pmg_level]
        else:
            return self.transport

    @property
    def coarse(self):
        return self.coarse_cfl * self._scale_factor

    @property
    def transport(self):
        return self.transport_cfl * self._scale_factor

    @property
    def _scale_factor(self):
        return self.current_cfl / self.max_cfl

    def update(self, solve_cycle, real_time_cycle, ramp_func):
        if ramp_func is None:
            ramp_func = exp_ramp
        self.current_cfl = ramp_func(solve_cycle, real_time_cycle, self)
