from pcb_operator import *

class MyOperator (PcbOperator):
    def my_op(x):
        return x
    def test_op(x):
        return x
    def bin_op(x, y):
        return x+y
    
my_var = 3
MyOperator(
    [Operator("my_op"), Operator("test_op"), Operator("bin_op", assoc=True, comm=True)]
    )
