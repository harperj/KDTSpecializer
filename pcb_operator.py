import inspect
import asplib.asp.codegen.python_ast as ast
import asplib.asp.codegen.cpp_ast as cpp_ast
import asplib.asp.codegen.ast_tools as ast_tools
import codepy.cgen

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

        from asplib.asp.jit import asp_module
        mod = asp_module.ASPModule()
        
        phase2 = PcbOperator.ProcessAST().visit(self.op_ast)
        print "-- Before ConvertAST -- "
        converted = PcbOperator.ConvertAST().visit(phase2)
        print converted
        #mod.add_function(converted.body.contents[0], 'op')
        #print "--- Before mod.generate() ---"
        #print mod.generate()

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
            new_function_decl = self.ConstFunctionDeclaration(
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
                        self.New("my_op_s<doubleint>()")])
                )
            new_constructor_function = cpp_ast.FunctionBody(new_constructor_decl, cpp_ast.Block([new_constructor_body]))
            
            # Building the block for  namespace "op"
            ns_block = cpp_ast.Block()
            ns_block.append(operator_struct)
            ns_block.append(new_constructor_function)
            op_namespace = self.Namespace("op", ns_block)

            return op_namespace
            
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
                for item in super(PcbOperator.ConvertAST.ConstFunctionDeclaration, self).generate(with_semicolon):
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


    def explore_ast(self, node, depth):
        print '  '*depth, node
        for n in ast.iter_child_nodes(node):
            self.explore_ast(n, depth+1) 
