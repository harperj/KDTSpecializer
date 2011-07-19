from pcb_operator import *

class MyOperator (PcbOperator):
    def op(x):
        x = x + 1
        return x
    
my_var = 3
MyOperator().op(3)
