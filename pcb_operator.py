import inspect
import asplib.asp.codegen.python_ast as ast
import asplib.asp.codegen.cpp_ast as cpp_ast
import asplib.asp.codegen.ast_tools as ast_tools
import codepy.cgen
import asplib.asp.jit.asp_module as asp_module

def struct_prototype(struct):
    return "struct %s;" % struct.tpname

class IfNotDefined(cpp_ast.Generable):
    def __init__(self, symbol):
        self.symbol = symbol

    def generate(self):
        yield "#ifndef %s" % self.symbol

class EndIf(cpp_ast.Generable):
    def generate(self):
        yield "#endif"

class Namespace(cpp_ast.Generable):
    def __init__(self, name, body):
        self.name = name
        self.body = body
        self._fields = ['name', 'body']

    def generate(self, with_semicolon=False):
        yield 'namespace %s' % self.name
        assert isinstance(self.body, cpp_ast.Block)
        for line in self.body.generate(with_semicolon):
            yield line

class ConstFunctionDeclaration(cpp_ast.FunctionDeclaration):
    def generate(self, with_semicolon=True):
        for item in super(ConstFunctionDeclaration, self).generate(with_semicolon):
            yield item
        yield ' const'
                
class New(cpp_ast.Generable):
    def __init__(self, typename):
        self.typename = typename
    def generate(self, with_semicolon=False):
        gen_str = 'new ' + str(self.typename)
        if with_semicolon:
            gen_str += ';'
            
        yield gen_str


class CMakeModule(object):
    def __init__(self, temp_dir, makefile_dir, name="module", namespace=None, include_files=[]):
        self.name = name
        self.preamble = []
        self.mod_body = []
        self.header_body = []
        self.namespace = namespace
        self.temp_dir = temp_dir
        self.makefile_dir = makefile_dir
        self.include_files = include_files

    def include_file(self, filepath):
        self.include_files.append(filepath)

    def add_to_preamble(self, pa):
        self.preamble.extend(pa)

    def add_to_module(self, body):
        self.mod_body.extend(body)

    def add_function(self, func):
        """*func* is a :class:`cgen.FunctionBody`."""

        self.mod_body.append(func)

        # Want the prototype for the function added to the header.
        self.header_body.append(func.fdecl)

    def add_struct(self, struct):
        self.mod_body.append(struct)

    def generate(self):
        source = []
        if self.namespace is not None:
            self.mod_body = [Namespace(self.namespace, cpp_ast.Block(self.mod_body))]

        self.preamble += [cpp_ast.Include(self.temp_dir+self.name+".h", system=False)]
        for include in self.include_files:
            self.preamble += [cpp_ast.Include(include, system=False)]
        
        source += self.preamble + [codepy.cgen.Line()] + self.mod_body
        return codepy.cgen.Module(source)

    def generate_header(self):
        header = []
            
        if self.namespace is not None:
            self.header_body = [Namespace(self.namespace, cpp_ast.Block(self.header_body))]

        header_top = [IfNotDefined(self.name+"_H"), cpp_ast.Define(self.name+"_H", "")]
        for include in self.include_files:
            header_top += [cpp_ast.Include(include, system=False)]
        
        header += header_top + self.header_body + [EndIf()]
        return codepy.cgen.Module(header)

    def generate_swig_interface(self):
        interface_string = "%module " + self.name + "\n"
        interface_string += "%{\n"
        interface_string += str(cpp_ast.Include(self.temp_dir+self.name+".h", system=False))
        interface_string += "\n"
        interface_string += "%}\n"
        interface_string += "".join([str(line) for line in self.header_body])
        return interface_string

    def compile(self):
        from os import getcwd, chdir
        from subprocess import call
        original_dir = getcwd()
        chdir(self.temp_dir)

        header_file = open(self.name + ".h", 'w')
        print >>header_file, self.generate_header()
        header_file.close()

        cpp_file = open(self.name + ".cpp", 'w')
        print >>cpp_file, self.generate()
        cpp_file.close()

        i_file = open(self.name + ".i", 'w')
        print >>i_file, self.generate_swig_interface()
        i_file.close()

        chdir(self.makefile_dir)
        args = ["make", "DYNFILE="+self.temp_dir+self.name]
        call(args)

        chdir(original_dir)
        
        
class PcbOperator(object):
    def __init__(self):
        # check for 'op' method
        try:
            dir(self).index('op')
        except ValueError:
            raise Exception('No op method defined.')


        self.op_src = inspect.getsource(self.op)
        self.op_ast = ast.parse(self.op_src.lstrip())
        self.pure_python = False
        self.pure_python_op = self.op
        self.op = self.specialized_op

        
    def specialized_op(self, *args):
        self.explore_ast(self.op_ast, 0)
        if self.pure_python:
            return self.pure_python_op(*args)

        temp_path = "/home/harper/Documents/Work/SEJITS/temp/"
        makefile_path = "/home/harper/Documents/Work/SEJITS/pyCombBLAS/trunk/kdt/pyCombBLAS"
        include_files = ["/home/harper/Documents/Work/SEJITS/pyCombBLAS/trunk/kdt/pyCombBLAS/pyOperations.h"]
        mod = CMakeModule(temp_path, makefile_path, namespace="op", include_files=include_files)
        
        phase2 = PcbOperator.ProcessAST().visit(self.op_ast)
        print "-- Before ConvertAST -- "
        converted = PcbOperator.ConvertAST().visit(phase2)
        print converted
        mod.add_struct(converted.contents[0])
        mod.add_function(converted.contents[1])
        mod.compile()

    class UnaryFunctionNode(ast.AST):
        def __init__(self, name, args, body):
            self.name = name
            self.args = args
            self.body = body
            self._fields = ['name', 'args', 'body']
            super(PcbOperator.UnaryFunctionNode, self).__init__()
        
    class ProcessAST(ast_tools.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == "op":
                print "Found op, time to replace"
                new_node = PcbOperator.UnaryFunctionNode(node.name, node.args, node.body)
                return new_node
            else:
                return node
            
    class ConvertAST(ast_tools.ConvertAST):
        def visit_UnaryFunctionNode(self, node):

            # Create the new function that does the same thing as 'op'
            new_function_decl = ConstFunctionDeclaration(
                cpp_ast.Value("T", "operator()"),
                [cpp_ast.Value("const T&", "x")])

            # Add all of the contends of the old function to the new
            new_function_contents = cpp_ast.Block([self.visit(subnode) for subnode in node.body])

            new_function_body = cpp_ast.FunctionBody(new_function_decl, new_function_contents)
            operator_struct = cpp_ast.Template(
                "typename T",
                cpp_ast.Struct("my_op_s : public ConcreteUnaryFunction<T>", [new_function_body])
                )

            # Finally, generate a function for constructing one of these operators
            new_constructor_decl = cpp_ast.FunctionDeclaration(
                cpp_ast.Value("UnaryFunction", "my_op"),
                [] )
            new_constructor_body = cpp_ast.ReturnStatement(
                cpp_ast.FunctionCall("UnaryFunction", [
                        New("my_op_s<doubleint>()")])
                )
            new_constructor_function = cpp_ast.FunctionBody(new_constructor_decl, cpp_ast.Block([new_constructor_body]))
            
            # Block for the module contents.
            main_block = cpp_ast.Block()
            main_block.append(operator_struct)
            main_block.append(new_constructor_function)

            return main_block
            


    def explore_ast(self, node, depth):
        print '  '*depth, node
        for n in ast.iter_child_nodes(node):
            self.explore_ast(n, depth+1) 
