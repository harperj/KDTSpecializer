import kdt.pyCombBLAS as pcb
import time

print "Using built-in, C++ backed op"
d = pcb.pyDenseParVec.range(10, -5)

print "before Apply:"
d.printall()

time1 = time.time()
for i in xrange(1000000):
    d.Apply(pcb.abs())
time2 = time.time()

print "Builtin Time: ", (time2-time1)
print "after Apply:"
d.printall()

########################################

print "\n\nUsing Python op"
d = pcb.pyDenseParVec.range(10, -5)

print "before Apply:"
d.printall()

def pyabs(x):
    if (x < 0):
        return -x
    return x

op = pcb.unary(pyabs)


# We want this to be fast:
time1 = time.time()
for i in xrange(1000000):
    d.Apply(op)
time2 = time.time()

print "Python time: ", (time2-time1)
print "after Apply:"
d.printall()
