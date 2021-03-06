#include <boost/python.hpp>

namespace op
{

  template <typename T>
  struct my_function_s : public ConcreteUnaryFunction<T>
  {
    T operator()(const T& x) const
    {
      operation_on_x();
    }
  }

  UnaryFunction my_function()
  {
    return UnaryFunction(new my_function_s<doubleint>());
  }
}

BOOST_PYTHON_MODULE(module)
{
  boost::python::def("step", &op::step);
}
