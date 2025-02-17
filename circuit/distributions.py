

import numpy as np
from scipy.stats import norm, skewnorm 
from scipy.special import owens_t, erf
from numpy import pi as PI
from gekko import GEKKO
import math
import pdb

AREA_CORRECTION = True
#### MAIN ISSUE with ACCURACY are the boundaries!


class Distribution:
    """ moments is a list of moments """ 
    def __init__(self, mom):
        self.mom = mom
        self.T = None
        self.f_T = None
        self.samples = None
    
    def pdf(self, t):
        raise NotImplementedError()
    
    def cdf(self, t):
        raise NotImplementedError()
    def F_inv(self, low, high, F_target, eps=0.01):
        mid = 0.5*(low+high)
        F_mid = self.cdf(mid)
        
        # print(low, high, mid, self.pdf(low), self.pdf(high), self.pdf(mid), self.cdf(low), self.cdf(high), F_mid, np.abs(F_mid-F_target))

        # print("{:.10f}\t{:.10f}\t{:.10f}\t{:.10f}\t{:.10f}\t".format(
        #     low, high, mid, F_mid, np.abs(F_mid-F_target)))
        # pdb.set_trace()
        if abs(F_mid - F_target) < eps:
            return mid
        elif F_mid > F_target:
            return self.F_inv(low, mid, F_target, eps=eps)
        else:
            return self.F_inv(mid, high, F_target, eps=eps)
    
    def equal_F(self, low, high, count, eps=0.001):
        # print("Function call:\t{:.4f}\t{:.4f}\t{}".format(low, high, count))
        F_mid = (self.cdf(low) + self.cdf(high))/2
        t_mid = self.F_inv(low, high, F_mid, eps=eps)
        if count == 2:
            res = [low, t_mid]
        else:
            left = self.equal_F(low, t_mid, count/2, eps)
            right = self.equal_F(t_mid, high, count/2, eps)
            left.extend(right)
            res = left
        # print("Results are:  \t{:.4f}\t{:.4f}\t-->{}".format(low, high, res))
        return res

    def pmf(self, samples, eps=0.0001):
        # TODO: the description of function should be updated
        """ Generates a smart sample set from the PDF of a Distribution
        Arguments 
        -- samples: number of samples, if margin defined in this distribution, samples are 
            provided within margin, otherwise solid m1+-margin*m2 is margin
        Returns:
        -- A tuple of (T, f_T), both are numpy arrays
        -- T: time value (RV) of each sample
        -- f_T: the prob. value of T, i.e. f_T = f(t=T) """
        
        low, high = self.margin()
        if low == None:
            print("Warning: possible mismatch in margin")
            if self.m1 == None:
                raise NameError("mean is not available")
            else:
                low = self.m1 - margin*self.m2
                high = self.m1 + margin*self.m2
            
        if np.log2(samples)%2 != 0:
            samples = np.power(2, np.ceil(np.log2(samples)))
            print("Changing samples to {}".format(samples))
        
        T = self.equal_F(low, high, samples, eps=eps)
        T.append(high)
        f_T = [self.pdf(t) for t in T]
        # F_T = [d.cdf(t) for t in T]
        return np.asarray(T), np.asarray(f_T)

    def __pmf(self, samples, margin=6):
        """ Generates a uniform sample set from the PDF of a Distribution
        Arguments 
        -- samples: number of samples, if margin defined in this distribution, samples are 
            provided within margin, otherwise solid m1+-margin*m2 is margin
        Returns:
        -- A tuple of (T, f_T), both are numpy arrays
        -- T: time value (RV) of each sample
        -- f_T: the prob. value of T, i.e. f_T = f(t=T) """
        low, high = self.margin()
        if low == None:
            print("Warning: possible mismatch in margin")
            if self.m1 == None:
                raise NameError("mean is not available")
            else:
                low = self.m1 - margin*self.m2
                high = self.m1 + margin*self.m2
            
        T = np.linspace(low, high, samples)
        f_T = np.zeros(T.shape)
        for idx, t in enumerate(T):
            f_T[idx] = self.pdf(t)
        return T, f_T

    def cmf(self, samples):
        """ Generates a uniform sample set from the PDF of a Distribution
        Arguments 
        -- samples: number of samples, if margin defined in this distribution, samples are 
            provided within margin, otherwise solid m1+-margin*m2 is margin
        Returns:
        -- A tuple of (T, f_T), each numpy arrays
        -- T: time value (RV) of each sample
        -- f_T: the prob. value of T, i.e. f_T = f(t=T) """
        T, f_T = self.pmf(samples) 
        F_T = np.zeros(f_T.shape);
        F_T[0] = f_T[0]
        for t in range(1,len(T)):
            dT = T[t] - T[t-1]
            F_T[t] = F_T[t-1] + (f_T[t]*dT)

        return T, F_T
    
    @staticmethod
    def cmf_from_pmf(T, f_T):
        F_T = np.zeros(f_T.shape)
        F_T[0] = f_T[0]
        for t in range(1, len(T)):
            dT = T[t] - T[t-1]
            F_T[t] = F_T[t-1] + (dT * f_T[t])

        return T, F_T

    @staticmethod
    def area_pmf(T, f_T):
        """ This method calculates area of a pmf in the given range 
        -- T: numpy array of sample times
        -- f_T: numpy array, PDF value at sample points
        -- returns a floating point """ 
        area = 0
        for idx in range(len(T)-1):
            area += (T[idx+1] - T[idx])*f_T[idx]
        return area


    def margin(self):
        low, high = None, None
    
    @staticmethod
    def moments_from_pmf(T, f_T, moments=2):

        if moments < 1:
            return None
        
        M  = [0]*(moments+1) # [E_x, E_xx, E_xxx, .. ]
        
        dT = np.zeros(T.shape)
        dT[:-1] = T[1:] - T[:-1]
        dT[-1] = dT[-2]
        
        M[1] = np.sum( T * f_T * dT)
        if moments > 1:
            M[2] = np.sum( (T-M[1])**2 * f_T * dT)
        
        if moments > 2:
            nom = np.sum( (T-M[1])**3 * f_T * dT)
            M[3] = nom / M[2]**1.5 

        return M[1:]


class Normal(Distribution):
    def __init__(self, mu=0, sigma=1):
        super().__init__([mu, sigma*sigma])
        self.mu = mu
        self.sigma = sigma
        self.var = sigma*sigma

    def pdf(self, t):
        return norm.pdf(t, self.mu, self.sigma)

    def cdf(self, t):
        return norm.cdf(t, self.mu, self.sigma)

    def margin(self):
        return self.mu-6*self.sigma, self.mu+6*self.sigma


class SkewNormal(Distribution):
    def __init__(self, zeta, omega, alpha):
        # TODO: double check for omega to be positive!
        self.zeta = zeta
        self.omega = omega
        self.alpha = alpha
        location = zeta
        scale = omega
        shape = alpha

        delta = shape / np.sqrt(1 + shape*shape)
        self.mu = location + scale * delta * np.sqrt(2/PI)
        self.var = scale * scale * (1- (2*delta*delta/PI))
        self.sigma = np.sqrt(self.var) 
        self.gamma = 0.5 * (4-PI) * ((delta * np.sqrt(2/PI))**3) / ((1 - 2*delta*delta/PI)**1.5)

    def pdf(self, t):
        return skewnorm.pdf(t, self.alpha, self.zeta, self.omega)

    def cdf(self, t):
        return skewnorm.cdf(t, self.alpha, self.zeta, self.omega)

    def margin(self, eps=0.0001):
        _t = list(np.linspace(-3, 5, 101))
        _phi = np.asarray([norm.cdf(t) for t in _t])
        _owens_t = np.asarray([owens_t(t, self.alpha) for t in _t])
        _cdf = _phi - 2*_owens_t 
        idx_l = next (x for x in range(len(_cdf)) if _cdf[x] > eps )
        idx_h = next (x for x in range(len(_cdf)) if _cdf[x] > 1-eps )
        low  = _t[max(idx_l-1, 0)]
        high = _t[min(idx_h+1, 100)]
        low = (low*self.omega) + self.zeta
        high = (high*self.omega) + self.zeta
        return low, high
    
    def _margin(self, eps=0.001):
        low = self.mu
        print(low)
        while self.cdf(low) > eps:
            low -= 0.1*np.abs(low)
            print(low, self.cdf(low))
        high = self.mu
        while self.cdf(high) < 1-eps:
            high += 0.1*np.abs(high)

        return (low, high)

    @staticmethod
    def param_from_mom(mom):
        if len(mom) != 3:
            raise ValueError ("Moment dimension should be 3")
        mu, var, gamma = mom

        m = GEKKO() 
        delta = m.Var(value=1.06)
        
        m.Equation([gamma == 
            0.5 * (4-PI) * ( (delta * np.sqrt(2/PI))**3 ) / ( (1 - 2*delta*delta/PI)**1.5)])
        m.solve(disp=False)
        
        # print("result of delta: {}".format(delta.value))
        if len(delta) > 1:
            print("ERROR in delta")
        delta = delta.value[0]
        if np.abs(delta) > 1:
            print("Warning: SkewNormal delta {:.5f} out of range!".format(delta))
            delta = delta/(np.abs(delta) + 0.001)
            print("Changed delta to {:.5f}".format(delta))
        # print("num delta: {:.3f}".format(delta))
        
        alpha = delta / np.sqrt(1-delta**2)
        omega = np.sqrt( var / (1- (2*delta*delta/PI) ) )
        zeta = mu - omega * delta * np.sqrt(2/PI)
        
        return (zeta, omega, alpha)


class LogNormal(Distribution):
    def __init__(self, Mu, Sigma):
        # TODO: Mu and Sigma are not mean and std! but paramters of distribution
        self.Mu = Mu 
        self.Sigma = Sigma
        self.mu = np.exp(Mu + Sigma*Sigma/2) 
        self.var = (np.exp(Sigma**2) - 1) * np.exp(2*Mu + Sigma*Sigma) 
        self.sigma = np.sqrt(self.var) 
        # self.gamma = Not Implemented

    def pdf(self, t):
        nom = np.exp(-(np.log(t) - self.Mu)**2/(2*self.Sigma**2)) 
        den = ( t * self.Sigma * np.sqrt(2*np.pi))
        return nom/den
    
    def cdf(self, t):
        return 0.5*erf( (np.log(t) - self.Mu) / (np.sqrt(2) * self.Sigma) ) + 0.5 

    def margin(self, eps=0.001):
        low = self.mu
        while self.cdf(low) > eps:
            low = low*0.9
        high = self.mu
        while self.cdf(high) < 1-eps:
            high = high*1.1

        return (low, high)

    @staticmethod
    def param_from_mom(mom):
        if len(mom) != 2:
            raise ValueError ("Moment dimension should be 2")
        mu, var = mom

        _r = var/(mu**2)
        
        _Sigma = np.sqrt( np.log(_r+1) )
        _Mu = np.log( mu /  np.sqrt( (var/(mu**2)) + 1)  ) 
        
        return (_Mu, _Sigma)


class NumDist(Distribution):
    #TODO: I need to double check the boundaries
    def __init__(self, T, f_T, clean=False, eps=1e-5, eps2=2e-5):
        if clean:
            self.T = []
            self.f_T = []
            ptr_s = 0
            ptr_f = len(T)-1
            while(f_T[ptr_s] < eps):
                ptr_s += 1
            while(f_T[ptr_f] < eps):
                ptr_f -= 1
            while(ptr_s + 2 < ptr_f):
                if f_T[ptr_s] < eps2 and f_T[ptr_s+1] < eps2 and f_T[ptr_s+2] < eps2:
                    ptr_s += 1
                else:
                    break
            while(ptr_f - 2 > 0):
                if f_T[ptr_f] < eps2 and f_T[ptr_f-1] < eps2 and f_T[ptr_f-2] < eps2:
                    ptr_f -= 1
                else:
                    break

            self.T = T[ptr_s:ptr_f+1]
            self.f_T = f_T[ptr_s:ptr_f+1]
            print(len(T), len(self.T))
        else:
            self.T = T
            self.f_T = f_T

        self.gen_F()

    def pmf(self):
        return self.T, self.f_T
    
    def pdf(self, t):
        idx = np.searchsorted(self.T, t)
        if idx==0:
            return 0
        if idx==len(self.T):
            # extra-polation
            a = (self.f_T[-1] - self.f_T[-2])/(self.T[-1] - self.T[-2])
            res = self.f_T[-1] + a * (t-self.T[-1]) 
            return max(0, res)
        
        a = (t-self.T[idx-1])/(self.T[idx] - self.T[idx-1])
        return (1-a)*self.f_T[idx-1] + a*self.f_T[idx]

    def cdf(self, t):
        idx = np.searchsorted(self.T, t)
        if idx==0: #TODO: tof-maal
            return 0
        if idx==len(self.T): # TODO: tof-maal
            return 1
            # print("Error is here, idx={:.5f} \t t={:.5f}".format(idx, t))
        a = (t-self.T[idx-1])/(self.T[idx] - self.T[idx-1])
        return (1-a)*self.F_T[idx-1] + a*self.F_T[idx]


    def gen_F(self):
        F_T = np.zeros(len(self.T))
        F_T[0] = 0
        for i in range(1, len(self.T)):
            dT = self.T[i] - self.T[i-1]
            # 0.5 added to make better prediction
            F_T[i] = F_T[i-1] + 0.5*dT*(self.f_T[i]+self.f_T[i-1])
        self.F_T = F_T

    def margin(self):
        return (min(self.T), max(self.T))


class Uniform(Distribution):
    def __init__(self, a, b):
        assert a < b, "Uniform distribution, margin is not correct ({} > {})".format(a,b)
        self.a = a
        self.b = b
        self.mu = (a+b)/2
        self.var = (b-a)**2 / 12
        self.sigma = np.sqrt(self.var)

    def pdf(self, t):
        if t >= self.a and t <= self.b:
            return 1/(self.b-self.a)
        return 0

    def cdf(self, t):
        if t < self.a:
            return 0
        elif t < self.b:
            return (t-self.a)/(self.b-self.a)
        return 1

    def margin(self, eps = 0.01):
        return (1-eps)*self.a, (1+eps)*self.b

class MaxOp:
    def __init__(self):
        self.max_alt_map = {
                (Normal, Normal): self._max_NN, (Normal, SkewNormal): self._max_NSN, 
                (SkewNormal, Normal): self._max_SNN, (SkewNormal, SkewNormal): self._max_SNSN
                }
    
    def phi(self, t):
        return norm.pdf(t)

    def Phi(self, t):
        return norm.cdf(t)
    
    def max_alt(self, d1, d2):
        return self.max_alt_map[(type(d1), type(d2))](d1, d2)

    def _max_NSN(self, d1, d2, rho=0):
        pass

    def _max_SNN(self, d1, d2, rho=0):
        pass

    def _max_SNSN(self, d1, d2, rho=0):
        pass

    def _max_NN(self, d1, d2, rho=0):
        ''' does not work if this condition is satisfied: 
        (sig1 == sig2) and (rho == 1)
        '''
        mu1 = d1.mu
        mu2 = d2.mu
        sig1 = d1.sigma
        sig2 = d2.sigma
        a = np.sqrt(sig1**2 + sig2**2 - 2*rho*sig1*sig2)
        alpha = (mu1 - mu2)/a
        mu_max = mu1*self.Phi(alpha) + mu2*self.Phi(-alpha) + a*self.phi(alpha)
        sig_max_2 = (mu1**2 + sig1**2)*self.Phi(alpha) + \
                    (mu2**2 + sig2**2)*self.Phi(-alpha) + \
                    (mu1 + mu2)*a*self.phi(alpha) - mu_max**2
        sig_max = np.sqrt(sig_max_2)

        return Normal(mu_max, sig_max) 

    def max_num(self, d1, d2, samples, rho=0):
        """ if d1 or d2 are raw pmfs, tuple(T, f_T), they will be converted to  NumDist
        o.w. they should be of type Distribution, or similar """ 
        if isinstance(d1, tuple):
            d1 = NumDist(d1[0], d1[1])
        if isinstance(d2, tuple):
            d2 = NumDist(d2[0], d2[1])
        assert isinstance(d1, Distribution), print("Error: d1 is not numerical distribution") 
        assert isinstance(d2, Distribution), print("Error: d2 is not numerical distribution") 
        l1, h1 = d1.margin()
        l2, h2 = d2.margin()
        # print(l1, l2, h1, h2)
        ''' range can be more restricted for max operation '''  
        low = max(l1, l2)
        high = max(h1, h2)

        ex_space = (high-low)*0.02
        domain = np.linspace(low-ex_space, high+ex_space, samples)
        f_max = np.zeros(samples) 
        for idx, t in enumerate(domain):
            f1 = d1.pdf(t)
            F1 = d1.cdf(t)
            f2 = d2.pdf(t)
            F2 = d2.cdf(t)
            f_max[idx] = f1*F2 + F1*f2

        if AREA_CORRECTION:
            a =  Distribution.area_pmf(domain, f_max)
            if a!=1:
                f_max = [f/a for f in f_max]
        res = NumDist(domain, f_max)
        print("Area under pdf: {:.3f}".format(Distribution.area_pmf(res.T, res.f_T)))
        #     Distribution.area_pmf(d1.T, d1.f_T), 
        #     Distribution.area_pmf(d2.T, d2.f_T),
        #     Distribution.area_pmf(temp.T, temp.f_T)))

        # print("Area under pdf: {:.3f} {:.3f} {:.3f}".format(
        #     Distribution.area_pmf(d1.T, d1.f_T), 
        #     Distribution.area_pmf(d2.T, d2.f_T),
        #     Distribution.area_pmf(temp.T, temp.f_T)))
        # 
        # print( "D1  low={:.5f} \t high={:.5f} \t f[0]={:.5f} \t f[-1]={:.5f} \nD2  low={:.5f} \t high={:.5f} \t f[0]={:.5f} \t f[-1]={:.5f} \nMax low={:.5f} \t high={:.5f} \t f[0]={:.5f} \t f[-1]={:.5f}".format(
        #     d1.margin()[0], d1.margin()[1], d1.f_T[0], d1.f_T[-1], 
        #     d2.margin()[0], d2.margin()[1], d2.f_T[0], d2.f_T[-1], 
        #     temp.margin()[0], temp.margin()[1], temp.f_T[0], temp.f_T[-1]))

        return res 

class SumOp:
    def __init__(self):
        self.sum_alt_map = {
                (Normal, Normal): self._sum_NN, (Normal, SkewNormal): self._sum_NSN, 
                (SkewNormal, Normal): self._sum_SNN, (SkewNormal, SkewNormal): self._sum_SNSN
                }
    def sum_alt(self, d1, d2):
        return self.sum_alt_map[(type(d1), type(d2))](d1, d2)

    def _sum_NSN(self, d1, d2, rho=0):
        pass

    def _sum_SNN(self, d1, d2, rho=0):
        pass

    def _sum_SNSN(self, d1, d2, rho=0):
        pass

    def _sum_NN(self, d1, d2, rho=0):
        ''' does not work if this condition is satisfied: 
        (sig1 == sig2) and (rho == 1)
        '''
        return Normal(d1.mu + d2.mu, np.sqrt(d1.sigma**2 + d2.sigma**2)) 

    def sum_num(self, d1, d2, rho=0, samples=200):
        """ if d1 or d2 are raw pmfs, tuple(T, f_T), they will be converted to  NumDist
        o.w. they should be of type Distribution, or similar """ 
        if isinstance(d1, tuple):
            d1 = NumDist(d1[0], d1[1])
        if isinstance(d2, tuple):
            d2 = NumDist(d2[0], d2[1])
        assert isinstance(d1, Distribution), print("Error: d1 is not numerical distribution") 
        assert isinstance(d2, Distribution), print("Error: d2 is not numerical distribution") 
        if isinstance(d1, Distribution):
            T1, f_T_1 = d1.pmf(samples)
        else:
            T1, f_T_1 = d1.pmf()
        l1, h1 = d1.margin()
        l2, h2 = d2.margin()
        ''' range can be more restricted for max operation '''  
        low = l1 + l2
        high = h1 + h2
        domain = np.linspace(low, high, samples)
        # dT = domain[1] - domain[0]
        print("Margin Dist #1:  {:.3f}\t{:.3f}".format(l1, h1))
        print("Margin Dist #2:  {:.3f}\t{:.3f}".format(l2, h2))
        print("Margin Dist Sum: {:.3f}\t{:.3f}".format(low, high))
        f_sum = np.zeros(samples) 
        for sum_idx, t in enumerate(domain):
            # fz(t) = INT fX(k) * fY(t-k) for k in [-inf, +inf]
            # ..... = INT fX(k) * fY(t-k) for k in [X_min, X_max]
            for idx, k in enumerate(T1[:-1]):
                dK = T1[idx+1] - T1[idx]
                f_sum[sum_idx] += (d1.pdf(k) * d2.pdf(t-k) * dK)
        print("Area: ", Distribution.area_pmf(domain, f_sum))
        return NumDist(domain, f_sum, clean=True)


class DistScore:

    @staticmethod
    def KS_score(d_num, d_alt):
        """ Measures the Kolomogrov-Smirnov score between two distributions
        -- T, F_t are pmf of one distribution 
        -- dist_type: type of the 2nd distribution
        -- mom: moments of the 2nd distribution
        """
        T, F_T = d_num
        max_dist = 0
        for idx, t in enumerate(T):
            delta_F = np.abs(F_T[idx] - d_alt.cdf(t))
            max_dist = max(max_dist, delta_F)
        return max_dist
     
    @staticmethod 
    def CVM_score(d_num, d_alt):
        """ Measures the Cram ́er-Von Mises score between two distributions
        -- T, F_t are pmf of one distribution 
        -- dist_type: type of the 2nd distribution
        -- mom: moments of the 2nd distribution
        """
        T, F_T = d_num
        score = 0 
        for idx in range(1, len(T)):
            dT = T[idx] - T[idx-1] 
            t = T[idx]
            if dT * ( (F_T[idx] - d_alt.cdf(t))**2 ) < 0:
                raise NameError("Some issue with CVM")
            score += dT * ( (F_T[idx] - d_alt.cdf(t))**2 )
            
        return np.sqrt(score)
    
    @staticmethod
    def AD_score(T, F_T, dist_type, mom):
        """ Measures the Anderson-Darling score between two distributions
        -- T, F_t are pmf of one distribution 
        -- dist_type: type of the 2nd distribution
        -- mom: moments of the 2nd distribution
        """
        raise NameError("This measurement is not implemented")
    
    @staticmethod
    def score(d_num, meas="KS", dist_type="N"):
        """ Measures the distance score between two empirical and analytical distributions
        d_num: tuple for numerical (empirical) pmf (T, F_T)
        model: distance metric, can be KS (Kolomogrov-Smirnov), CVM (Cramer-Von Mises) 
               or AD (Anderson-Darling - not implemented so far) 
        dist_type: what is the family of this distribution? 
        """
        meas_map = {"KS": DistScore.KS_score, "CVM": DistScore.CVM_score}
 
        T, f_T = d_num
        T, F_T = Distribution.cmf_from_pmf(T, f_T)

        if dist_type == "N":
            mom = Distribution.moments_from_pmf(T, f_T, 2)
            d_alt = Normal(mom[0], np.sqrt(mom[1]))
            # print("Moments: {:.3f}\t{:0.3f}".format(mom[0], mom[1]))

        elif dist_type == "SK":
            mom = Distribution.moments_from_pmf(T, f_T, 3)
            zeta, omega, alpha = SkewNormal.param_from_mom(mom)
            d_alt = SkewNormal(zeta, omega, alpha)
            # print("Moments: {:.3f}\t{:.3f}\t{:.3f}".format(mom[0], mom[1], mom[2]))
            # print("Params:  {:.3f}\t{:.3f}\t{:.3f}".format(zeta, omega, alpha))

        elif dist_type == "LN":
            mom = Distribution.moments_from_pmf(T, f_T, 2)
            Mu, Sigma = LogNormal.param_from_mom(mom)
            d_alt = LogNormal(Mu, Sigma)
            # print("Moments: {:.3f} \t {:.3f}".format(mom[0], mom[1]))
            # print("Params:  {:.3f} \t{:.3f}".format(Mu, Sigma))

        return meas_map[meas]((T, F_T), d_alt)

