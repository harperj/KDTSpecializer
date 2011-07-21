from pcb_operator import *

class MyOperator (PcbOperator):
    def op(x):
        return x
    
my_var = 3
MyOperator().op(3)
