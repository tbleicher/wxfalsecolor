import math

def prime_factors(n):
    factors = []
    d = 2
    while n > 1:
        while n % d == 0:
            factors.append(d)
            n = n/d
        d = d + 1
    return factors


def find_fractional_ratio(x, y):
    """find fractional ratio of x and y"""
    rratio = y/float(x)     # reverse ratio - always smaller than 1
    new_l = x
    new_s = y
    for i in xrange(1,x+1):
        if i*rratio == round(i*rratio, 0):
            new_l = i
            new_s = i*rratio
            break
    return (new_l, new_s)


def scale_by_increment(l, s, maxpixels):
    """use aspect ratio and stepped increment to scale""" 
    
    ratio_sqrt = math.sqrt(l/float(s))
    new_l = math.sqrt(maxpixels)*ratio_sqrt
    step =  5 if new_l >   50 else 1
    step = 20 if new_l >  200 else step
    step = 50 if new_l > 1000 else step
    new_l = new_l - (new_l % step)
    new_s = (new_l * s) / l
    return (new_l, new_s)


def scale_to_maxpixels(new_l, new_s, maxpixels):
    """increase new_l, new_s by multiples of 10"""

    m = math.sqrt(maxpixels / (new_l*new_s))
    n = 1
    for j in xrange(0,int(m+11),10):
        if j*j*new_l*new_s <= maxpixels: n = j
    new_l *= n
    new_s *= n
    return (new_l, new_s)


def beautyscale(w, h, maxpixels):
    """find new w, h in multiples of 10 for w and h"""
    
    # don't scale if images is exactly the right size
    if w*h == maxpixels:
        return (w,h)
    
    # replace 'width' and 'height' with 'long' and 'short'
    (l,s) = (w,h) if w > h else (h,w)
    
    # try fractional ratios first 
    new_l, new_s = find_fractional_ratio(l, s)
    if new_l != l:
        new_l, new_s = scale_to_maxpixels(new_l, new_s, maxpixels)
    else:
        new_l, new_s = scale_by_increment(l, s, maxpixels)
    
    # convert (l,s) back to (w,h)
    new = (int(new_l), int(new_s)) if w > h else (int(new_s), int(new_l))
    return new
    


if __name__ == "__main__":
    print "scale up: 2400,1350 ->", beautyscale(2400,1350, 2880000)
    print " 823,619 ->", beautyscale(823,619,509437)
