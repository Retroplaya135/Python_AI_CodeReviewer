import ast
import re
import pycodestyle
import io

class CodeReviewer:
    def __init__(self):
        self.issues = []
        self.lines = []
        self.tree = None

    def load_code(self, code):
        self.lines = code.split('\n')

    def parse_code(self, code):
        try:
            self.tree = ast.parse(code)
        except SyntaxError as e:
            self.issues.append(f"SyntaxError: {e}")

    def check_style(self, code):
        style_guide = pycodestyle.StyleGuide()
        f = io.StringIO(code)
        checker = pycodestyle.Checker(lines=f.readlines(), options=style_guide.options)
        checker.check_all()
        if checker.report.total_errors > 0:
            self.issues.append("Style issues found.")

    def check_missing_docstrings(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    self.issues.append(f"Missing docstring in function '{node.name}'.")
            if isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    self.issues.append(f"Missing docstring in class '{node.name}'.")

    def check_class_names(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]+$', node.name):
                    self.issues.append(f"Class '{node.name}' naming style.")

    def check_function_names(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    self.issues.append(f"Function '{node.name}' naming style.")

    def check_variable_names(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                    self.issues.append(f"Variable '{node.id}' naming style.")

    def check_constant_names(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        if t.id.isupper():
                            if not re.match(r'^[A-Z0-9_]+$', t.id):
                                self.issues.append(f"Constant '{t.id}' naming style.")

    def check_unused_imports(self):
        imports = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name.split('.')[0])
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
                else:
                    imports.append('')
        used_imports = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_imports.add(node.id)
        for i in imports:
            if i not in used_imports:
                self.issues.append(f"Unused import '{i}'.")

    def check_redefined_builtins(self):
        builtins = {
            'abs','all','any','ascii','bin','bool','breakpoint','bytearray','bytes',
            'callable','chr','classmethod','compile','complex','delattr','dict','dir',
            'divmod','enumerate','eval','exec','filter','float','format','frozenset',
            'getattr','globals','hasattr','hash','help','hex','id','input','int',
            'isinstance','issubclass','iter','len','list','locals','map','max',
            'memoryview','min','next','object','oct','open','ord','pow','print',
            'property','range','repr','reversed','round','set','setattr','slice',
            'sorted','staticmethod','str','sum','super','tuple','type','vars','zip'
        }
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in builtins:
                    self.issues.append(f"Redefining builtin '{node.name}'.")
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id in builtins:
                    self.issues.append(f"Redefining builtin '{node.id}'.")

    def check_magic_methods(self):
        magic = {
            '__init__','__str__','__repr__','__len__','__getitem__','__setitem__',
            '__delitem__','__iter__','__next__','__call__','__contains__','__enter__',
            '__exit__','__add__','__sub__','__mul__','__truediv__','__floordiv__',
            '__mod__','__pow__','__and__','__or__','__xor__','__lt__','__le__',
            '__gt__','__ge__','__eq__','__ne__'
        }
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('__') and node.name.endswith('__') and node.name not in magic:
                    self.issues.append(f"Unknown magic method '{node.name}'.")

    def check_unreachable_code(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Return):
                parent = node
                while parent:
                    if hasattr(parent, 'body'):
                        index_of_return = parent.body.index(node)
                        for n in parent.body[index_of_return + 1:]:
                            self.issues.append(f"Unreachable code after return in line {n.lineno}.")
                        break
                    parent = getattr(parent, 'parent', None)

    def check_too_many_branches(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                branches = 0
                for subnode in ast.walk(node):
                    if isinstance(subnode, (ast.If, ast.For, ast.While, ast.Try)):
                        branches += 1
                if branches > 10:
                    self.issues.append(f"Too many branches ({branches}) in function '{node.name}'.")

    def check_too_many_arguments(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                argc = len(node.args.args)
                if argc > 5:
                    self.issues.append(f"Function '{node.name}' has too many args ({argc}).")

    def check_nested_functions(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                for inner in node.body:
                    if isinstance(inner, ast.FunctionDef):
                        self.issues.append(f"Nested function '{inner.name}' in '{node.name}'.")

    def check_empty_blocks(self):
        for node in ast.walk(self.tree):
            if hasattr(node, 'body') and isinstance(node.body, list) and len(node.body) == 0:
                self.issues.append(f"Empty block at line {getattr(node, 'lineno', '?')}.")

    def check_break_outside_loop(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Break):
                parents = []
                temp = node
                while temp:
                    parents.append(temp)
                    temp = getattr(temp, 'parent', None)
                found_loop = False
                for p in parents:
                    if isinstance(p, (ast.For, ast.While)):
                        found_loop = True
                        break
                if not found_loop:
                    self.issues.append(f"Break outside loop at line {node.lineno}.")

    def check_continue_outside_loop(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Continue):
                parents = []
                temp = node
                while temp:
                    parents.append(temp)
                    temp = getattr(temp, 'parent', None)
                found_loop = False
                for p in parents:
                    if isinstance(p, (ast.For, ast.While)):
                        found_loop = True
                        break
                if not found_loop:
                    self.issues.append(f"Continue outside loop at line {node.lineno}.")

    def check_raise_without_exception(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Raise):
                if not node.exc:
                    self.issues.append(f"Raise without exception at line {node.lineno}.")

    def check_return_outside_function(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Return):
                parents = []
                temp = node
                while temp:
                    parents.append(temp)
                    temp = getattr(temp, 'parent', None)
                func_parent = False
                for p in parents:
                    if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_parent = True
                        break
                if not func_parent:
                    self.issues.append(f"Return outside function at line {node.lineno}.")

    def check_global_usage(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Global):
                for name in node.names:
                    self.issues.append(f"Global variable usage '{name}' at line {node.lineno}.")

    def check_nonlocal_usage(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Nonlocal):
                for name in node.names:
                    self.issues.append(f"Nonlocal usage '{name}' at line {node.lineno}.")

    def check_mutable_defaults(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in node.args.defaults:
                    if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                        self.issues.append(f"Mutable default argument in '{node.name}'.")

    def check_print_statements(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                self.issues.append(f"Print statement at line {node.lineno}.")

    def check_exec_usage(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'exec':
                self.issues.append(f"Exec usage at line {node.lineno}.")

    def check_eval_usage(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'eval':
                self.issues.append(f"Eval usage at line {node.lineno}.")

    def check_pass_statements(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Pass):
                if isinstance(node.parent, ast.FunctionDef):
                    pass
                elif isinstance(node.parent, ast.ClassDef):
                    pass
                elif isinstance(node.parent, ast.If):
                    pass
                else:
                    self.issues.append(f"Pass statement at line {node.lineno} might be unnecessary.")

    def check_comment_format(self):
        for i, line in enumerate(self.lines, start=1):
            s = line.strip()
            if s.startswith('#'):
                if len(s) == 1:
                    self.issues.append(f"Empty comment at line {i}.")

    def check_magic_number(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value not in (0,1,-1,2,-2,0.0,1.0,-1.0,2.0,-2.0):
                    self.issues.append(f"Magic number '{node.value}' at line {getattr(node, 'lineno', '?')}.")

    def check_boolean_traps(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool):
                    self.issues.append(f"Boolean literal if at line {node.lineno}.")

    def check_todo_comments(self):
        for i, line in enumerate(self.lines, start=1):
            if 'TODO' in line.upper():
                self.issues.append(f"TODO comment at line {i}.")

    def check_long_lines(self):
        for i, line in enumerate(self.lines, start=1):
            if len(line) > 79:
                self.issues.append(f"Long line ({len(line)}) at line {i}.")

    def check_multiple_imports_on_one_line(self):
        for i, line in enumerate(self.lines, start=1):
            if line.strip().startswith('import'):
                if ',' in line:
                    self.issues.append(f"Multiple imports on one line at line {i}.")

    def check_bad_indentation(self):
        for i, line in enumerate(self.lines, start=1):
            leading = len(line) - len(line.lstrip(' '))
            if leading % 4 != 0 and line.strip():
                self.issues.append(f"Bad indentation at line {i}.")

    def check_semicolons(self):
        for i, line in enumerate(self.lines, start=1):
            if ';' in line and not line.strip().startswith('#'):
                self.issues.append(f"Semicolon at line {i}.")

    def check_tabs(self):
        for i, line in enumerate(self.lines, start=1):
            if '\t' in line:
                self.issues.append(f"Tab character at line {i}.")

    def check_trailing_whitespace(self):
        for i, line in enumerate(self.lines, start=1):
            if line.rstrip() != line:
                self.issues.append(f"Trailing whitespace at line {i}.")

    def check_multiple_statements(self):
        for i, line in enumerate(self.lines, start=1):
            if line.strip().count(';') > 1:
                self.issues.append(f"Multiple statements at line {i}.")

    def check_exception_handling(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Try):
                if not node.handlers:
                    self.issues.append(f"Try without except at line {node.lineno}.")

    def check_empty_exceptions(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues.append(f"Catch-all except at line {node.lineno}.")

    def check_useless_else_on_loop(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.For) or isinstance(node, ast.While):
                if node.orelse:
                    self.issues.append(f"Else on loop at line {node.lineno}.")

    def check_direct_exit_calls(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ('exit','quit'):
                    self.issues.append(f"Direct {node.func.id} call at line {node.lineno}.")

    def check_recursion_limit(self):
        pass

    def check_lambda_usage(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Lambda):
                self.issues.append(f"Lambda usage at line {node.lineno}.")

    def check_format_vs_fstring(self):
        for i, line in enumerate(self.lines, start=1):
            if '.format(' in line and 'print' in line:
                self.issues.append(f"Consider f-string at line {i}.")

    def check_mutable_class_vars(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                for b in node.body:
                    if isinstance(b, ast.Assign):
                        for t in b.targets:
                            if isinstance(t, ast.Name):
                                if isinstance(b.value, (ast.List, ast.Dict, ast.Set)):
                                    self.issues.append(f"Mutable class var '{t.id}' at line {b.lineno}.")

    def check_inconsistent_return(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                returns = []
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Return):
                        if sub.value is not None:
                            returns.append(True)
                        else:
                            returns.append(False)
                if len(set(returns)) > 1:
                    self.issues.append(f"Inconsistent return in '{node.name}'.")

    def check_wildcard_imports(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        self.issues.append(f"Wildcard import from '{node.module}' at line {node.lineno}.")

    def check_multiple_consecutive_blank_lines(self):
        blank_count = 0
        for i, line in enumerate(self.lines, start=1):
            if not line.strip():
                blank_count += 1
            else:
                if blank_count > 2:
                    self.issues.append(f"Multiple blank lines before line {i}.")
                blank_count = 0

    def check_very_large_functions(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 50:
                    self.issues.append(f"Large function '{node.name}' with {len(node.body)} lines.")

    def check_line_numbers(self):
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node

    def analyze(self, code):
        self.load_code(code)
        self.parse_code(code)
        if not self.tree:
            return
        self.check_line_numbers()
        self.check_style(code)
        self.check_missing_docstrings()
        self.check_class_names()
        self.check_function_names()
        self.check_variable_names()
        self.check_constant_names()
        self.check_unused_imports()
        self.check_redefined_builtins()
        self.check_magic_methods()
        self.check_unreachable_code()
        self.check_too_many_branches()
        self.check_too_many_arguments()
        self.check_nested_functions()
        self.check_empty_blocks()
        self.check_break_outside_loop()
        self.check_continue_outside_loop()
        self.check_raise_without_exception()
        self.check_return_outside_function()
        self.check_global_usage()
        self.check_nonlocal_usage()
        self.check_mutable_defaults()
        self.check_print_statements()
        self.check_exec_usage()
        self.check_eval_usage()
        self.check_pass_statements()
        self.check_comment_format()
        self.check_magic_number()
        self.check_boolean_traps()
        self.check_todo_comments()
        self.check_long_lines()
        self.check_multiple_imports_on_one_line()
        self.check_bad_indentation()
        self.check_semicolons()
        self.check_tabs()
        self.check_trailing_whitespace()
        self.check_multiple_statements()
        self.check_exception_handling()
        self.check_empty_exceptions()
        self.check_useless_else_on_loop()
        self.check_direct_exit_calls()
        self.check_recursion_limit()
        self.check_lambda_usage()
        self.check_format_vs_fstring()
        self.check_mutable_class_vars()
        self.check_inconsistent_return()
        self.check_wildcard_imports()
        self.check_multiple_consecutive_blank_lines()
        self.check_very_large_functions()

    def get_issues(self):
        return self.issues


if __name__ == "__main__":
    sample_code = r'''
import math, os

class testClass:
    def __init__(self):
        pass

def foo():
  print("hello");print("world")
  eval("1+1")
  try:
    return
    print("unreachable")
  except:
    pass

def BAR():
    TODO = 42
    pass

def bigFunc(a, b, c, d, e, f):
    if True:
        pass

'''

    reviewer = CodeReviewer()
    reviewer.analyze(sample_code)
    for i in reviewer.get_issues():
        print(i)
