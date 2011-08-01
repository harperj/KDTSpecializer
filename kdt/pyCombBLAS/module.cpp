#include "/home/harper/Documents/Work/SEJITS/temp/module.h"
#include "/home/harper/Documents/Work/SEJITS/temp/pyOperations.h"
#include "/home/harper/Documents/Work/SEJITS/temp/module.h"
#include "/home/harper/Documents/Work/SEJITS/temp/pyOperations.h"

namespace op
{
  namespace op
  {
    template <typename T>
    struct my_op_s : public ConcreteUnaryFunction<T>
    {
      T operator()(const T& x)
       const
      {
        return x;
      }
    } ;
    UnaryFunction my_op()
    {
      return UnaryFunction(new my_op_s<doubleint>());
    }
  }
}
