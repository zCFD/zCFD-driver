


class RungeKutta:
    def num_stages(self):
        raise NotImplementedError
    def coeff(self):
        raise NotImplementedError

class SingleStageRungeKutta(RungeKutta):
    """
    """
    NUM_STAGES = 1
    COEFFICIENTS = [1.0]
    
    def num_stages(self):
        return self.NUM_STAGES;
    
    def coeff(self):
        return self.COEFFICIENTS

class FourStageRungeKutta(RungeKutta):
    """
    """
    NUM_STAGES = 4
    COEFFICIENTS = [0.25, 0.5, 0.55, 1.0]
    
    def num_stages(self):
        return self.NUM_STAGES;
    
    def coeff(self):
        return self.COEFFICIENTS


class FiveStageRungeKutta(RungeKutta):
    """
    """
    NUM_STAGES = 5
    COEFFICIENTS = [0.0695, 
                    0.1602,
                    0.2898,
                    0.506,
                    1.0]
    
    def num_stages(self):
        return self.NUM_STAGES;
    
    def coeff(self):
        return self.COEFFICIENTS

class FiveStageRungeKuttaSSP(RungeKutta):
    """
    """
    # SEE STRONG STABILITY-PRESERVING HIGH ORDER TIME DISCRETIZATION METHODS - SIAM REVIEW, Gottlieb et. al
    # Vol. 43, No. 1, 2001
    NUM_STAGES = 5
    COEFFICIENTS = [0.36666667,
                    0.375,
                    0.16666667,
                    0.08333333,
                    0.00833333]
        
    def num_stages(self):
        return self.NUM_STAGES;

    def coeff(self):
        return self.COEFFICIENTS

class FourStageRungeKuttaSSP(RungeKutta):
    """
        """
    # SEE STRONG STABILITY-PRESERVING HIGH ORDER TIME DISCRETIZATION METHODS - SIAM REVIEW, Gottlieb et. al
    # Vol. 43, No. 1, 2001
    NUM_STAGES = 4
    COEFFICIENTS = [0.375,
                    0.33333334,
                    0.25,
                    0.04166667]
        
    def num_stages(self):
        return self.NUM_STAGES;

    def coeff(self):
        return self.COEFFICIENTS
    
    
    
