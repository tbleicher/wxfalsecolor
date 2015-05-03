import unittest
from rad_utils import prime_factors, beautyscale

class Test_Prime_Factors(unittest.TestCase):

    def test_prime_factors(self):
        for n,primes in [(2,[2]), (3,[3]),(5,[5]),
                (10,[2,5]),(12,[2,2,3]),(63,[3,3,7])]:
            self.assertEqual(prime_factors(n), primes)



class Test_BeautyScale(unittest.TestCase):

    def test_16_to_9(self):
        """it should scale images maintaining the orientation"""
        for w,h,m,nw,nh in [(1600,900,1000000, 1280, 720)]:
            self._test_orientations(w,h, m, nw,nh)

    def test_prime(self):
        """it should scale prime numbers"""
        for w,h,m,nw,nh in [(823,619,480000, 780, 586)]:
            self._test_orientations(w,h, m, nw,nh)

    def test_small(self):
        """it should not scale very small images"""
        for w,h,m,nw,nh in [(16,9, 160, 16, 9),(17,9, 165, 17, 9)]:
            self._test_orientations(w,h, m, nw,nh)
    
    def test_equal_size(self):
        """it should not scale when maxpixels is of equal size to w*h"""
        for w,h,m,nw,nh in [(1600,900, 1440000, 1600, 900),
                (823,619, 509437, 823, 619)]:
            self._test_orientations(w,h, m, nw,nh)

    def test_scale_up(self):
        """it should enlarge (w,h) when possible"""
        for w,h,m,nw,nh in [(1600,900, 2400*1350, 2400, 1350),
                (823,619, 823*619*4, 1600, 1203)]:
            self._test_orientations(w,h, m, nw,nh)

    def test_orientations(self):
        """it scales images regardless of orientation"""
        self._test_orientations(1600,900, 2400*1350, 2400, 1350)


    def _test_orientations(self, w,h,m, nw,nh):
        self.assertEqual(beautyscale(w,h,m), (nw,nh))
        self.assertEqual(beautyscale(h,w,m), (nh,nw))
