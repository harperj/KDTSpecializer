#include <boost/python.hpp>
#include "/home/harper/Documents/Work/SEJITS/pyCombBLAS/trunk/kdt/pyCombBLAS/pyOperations.h"
#include <stdint.h>
#include "test_cpp_file.h"

using namespace boost::python;

namespace op
{

  template <typename T>
  struct my_op_s : public ConcreteUnaryFunction<T>
  {
    T operator()(const T& x) const
    {
		return (x < 0) ? -static_cast<doubleint>(x) : x;
    }
  };

  UnaryFunction my_op()
  {
    return UnaryFunction(new my_op_s<doubleint>());
  }
}

/*
PyObject* my_op_py(object x)
{
  //float val = extract<float>(x.attr("__float__"));
  double f = extract<double>(x);
  if(f < 0) f = -f;
  PyObject* ret = PyFloat_FromDouble(f);
  return ret;
}



BOOST_PYTHON_MODULE(module)
{
  //class_<op::UnaryFunction>("UnaryFunction", init<op::ConcreteUnaryFunction<doubleint>*>());
  //def("my_op", &op::my_op);
  //def("apply_my_op", &apply_my_op);
  def("my_op_py", &my_op_py);
}
*/
