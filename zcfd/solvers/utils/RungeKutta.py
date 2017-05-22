

class RungeKutta:

    def num_stages(self):
        raise NotImplementedError

    def coeff(self):
        raise NotImplementedError

    def time_leveln_scaling(self):
        raise NotImplementedError

    def rkstage_scaling(self):
        raise NotImplementedError


class SingleStageRungeKutta(RungeKutta):
    """
    """
    NUM_STAGES = 1
    COEFFICIENTS = [1.0]
    LEVELN_COEFFICIENTS = [1.0]
    LEVELK_COEFFICIENTS = [0.0]

    def num_stages(self):
        return self.NUM_STAGES

    def coeff(self):
        return self.COEFFICIENTS

    def time_leveln_scaling(self):
        return self.LEVELN_COEFFICIENTS

    def rkstage_scaling(self):
        return self.LEVELK_COEFFICIENTS


class FourStageRungeKutta(RungeKutta):
    """
    """
    NUM_STAGES = 4
    COEFFICIENTS = [0.25, 0.5, 0.55, 1.0]
    LEVELN_COEFFICIENTS = [1.0, 1.0, 1.0, 1.0]
    LEVELK_COEFFICIENTS = [0.0, 0.0, 0.0, 0.0]

    def num_stages(self):
        return self.NUM_STAGES

    def coeff(self):
        return self.COEFFICIENTS

    def time_leveln_scaling(self):
        return self.LEVELN_COEFFICIENTS

    def rkstage_scaling(self):
        return self.LEVELK_COEFFICIENTS


class FiveStageRungeKutta(RungeKutta):
    """
    """
    NUM_STAGES = 5
    COEFFICIENTS = [0.0695, 0.1602, 0.2898, 0.506, 1.0]
    LEVELN_COEFFICIENTS = [1.0, 1.0, 1.0, 1.0, 1.0]
    LEVELK_COEFFICIENTS = [0.0, 0.0, 0.0, 0.0, 0.0]

    def num_stages(self):
        return self.NUM_STAGES

    def coeff(self):
        return self.COEFFICIENTS

    def time_leveln_scaling(self):
        return self.LEVELN_COEFFICIENTS

    def rkstage_scaling(self):
        return self.LEVELK_COEFFICIENTS


class ThreeStageThirdOrderTVDRungeKutta(RungeKutta):
    """
    """
    NUM_STAGES = 3
    COEFFICIENTS = [1.0, 0.25, 0.6666667]
    LEVELN_COEFFICIENTS = [1.0, 0.75, 0.3333333]
    LEVELK_COEFFICIENTS = [0.0, 0.25, 0.6666667]

    def num_stages(self):
        return self.NUM_STAGES

    def coeff(self):
        return self.COEFFICIENTS

    def time_leveln_scaling(self):
        return self.LEVELN_COEFFICIENTS

    def rkstage_scaling(self):
        return self.LEVELK_COEFFICIENTS
