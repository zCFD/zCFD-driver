from unittest import TestCase
from zcfd.solvers.cfl import CFL


class TestCFL(TestCase):

    def setUp(self):
        self.cfl = CFL(1.0)

    def test_updatecfl(self):
        solve_cycle = 0
        real_time_step = 0
        self.cfl.max_cfl = 10.0
        self.cfl.min_cfl = 1.0
        self.cfl.cfl_ramp = 1.1
        self.cfl.update(solve_cycle, real_time_step, None)
        assert self.cfl.cfl == 1.0
        solve_cycle = 500
        self.cfl.update(solve_cycle, real_time_step, None)
        assert self.cfl.cfl == 10.0
        solve_cycle = 100000
        self.cfl.update(solve_cycle, real_time_step, None)
        assert self.cfl.cfl == 10.0

    def test_norampfunc(self):
        self.cfl.update(0, 0, None)

    def test_constfunc(self):
        self.cfl.update(0, 0, lambda solve_cycle, real_time_step, cfl: 1.0)
        assert self.cfl.cfl == 1.0
