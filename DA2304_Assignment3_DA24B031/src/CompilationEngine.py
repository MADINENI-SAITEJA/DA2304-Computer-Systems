import os
from SymbolTable import SymbolEnv
from VMWriter import CodeEmitter

XML_CHARS = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;'}
ARITH_OPS = {'+': 'add', '-': 'sub', '&': 'and', '|': 'or', '<': 'lt', '>': 'gt', '=': 'eq'}
UNARY_OPS = {'-': 'neg', '~': 'not'}
CONSTANTS = {'true', 'false', 'null', 'this'}

class JackParser:
    def __init__(self, tokens, name, output_dir='.'):
        self.tokens = tokens
        self.ptr = 0
        self.name = name
        self.output_dir = output_dir
        self.xml_buffer = []
        self.indent_lvl = 0
        self.env = SymbolEnv()
        self.emitter = CodeEmitter(os.path.join(output_dir, f'{name}.vm'))
        self.label_idx = 0

    def cur_token(self): return self.tokens[self.ptr]
    def next_val(self): return self.tokens[self.ptr][1]
    def advance(self, expected_val=None, expected_type=None):
        tk_type, tk_val = self.tokens[self.ptr]
        self.ptr += 1
        safe = ''.join(XML_CHARS.get(c, c) for c in tk_val)
        self.xml_buffer.append('  ' * self.indent_lvl + f'<{tk_type}> {safe} </{tk_type}>')
        return tk_type, tk_val

    def wrap_start(self, tag):
        self.xml_buffer.append('  ' * self.indent_lvl + f'<{tag}>')
        self.indent_lvl += 1

    def wrap_end(self, tag):
        self.indent_lvl -= 1
        self.xml_buffer.append('  ' * self.indent_lvl + f'</{tag}>')

    def make_label(self):
        lbl = f'L{self.label_idx}'
        self.label_idx += 1
        return lbl

    def map_seg(self, kind): return CodeEmitter.SEGMENTS[kind]

    def parse_class(self):
        self.env.clear_all()
        self.wrap_start('class')
        self.advance('class')
        _, self.name = self.advance(expected_type='identifier')
        self.advance('{')

        while self.next_val() in ('static', 'field'): self.handle_class_var()
        while self.next_val() in ('constructor', 'function', 'method'): self.handle_routine()

        self.advance('}')
        self.wrap_end('class')

        with open(os.path.join(self.output_dir, f'{self.name}.xml'), 'w') as f:
            f.write('\n'.join(self.xml_buffer) + '\n')
        self.emitter.flush()

    def handle_class_var(self):
        self.wrap_start('classVarDec')
        _, var_kind = self.advance() 
        var_kind_up = var_kind.upper()           
        _, var_type = self.advance()    
        _, var_name = self.advance()     
        self.env.register(var_name, var_type, var_kind_up)

        while self.next_val() == ',':
            self.advance(',')
            _, var_name = self.advance()
            self.env.register(var_name, var_type, var_kind_up)
        self.advance(';')
        self.wrap_end('classVarDec')

    def handle_routine(self):
        self.wrap_start('subroutineDec')
        self.env.clear_subroutine()

        _, r_type = self.advance()   
        self.advance()                 
        _, r_name = self.advance()   

        if r_type == 'method':
            self.env.register('this', self.name, 'ARG')

        self.advance('(')
        self.handle_params()
        self.advance(')')
        
        self.wrap_start('subroutineBody')
        self.advance('{')

        while self.next_val() == 'var':
            self.handle_local_var()

        num_locals = self.env.get_count('VAR')
        self.emitter.make_func(f'{self.name}.{r_name}', num_locals)

        if r_type == 'constructor':
            self.emitter.push('constant', self.env.get_count('FIELD'))
            self.emitter.call_func('Memory.alloc', 1)
            self.emitter.pop('pointer', 0)
        elif r_type == 'method':
            self.emitter.push('argument', 0)
            self.emitter.pop('pointer', 0)

        self.handle_statements()
        self.advance('}')
        self.wrap_end('subroutineBody')
        self.wrap_end('subroutineDec')

    def handle_params(self):
        self.wrap_start('parameterList')
        if self.next_val() != ')':
            _, p_type = self.advance()
            _, p_name = self.advance()
            self.env.register(p_name, p_type, 'ARG')
            while self.next_val() == ',':
                self.advance(',')
                _, p_type = self.advance()
                _, p_name = self.advance()
                self.env.register(p_name, p_type, 'ARG')
        self.wrap_end('parameterList')

    def handle_local_var(self):
        self.wrap_start('varDec')
        self.advance('var')
        _, t = self.advance()
        _, n = self.advance()
        self.env.register(n, t, 'VAR')

        while self.next_val() == ',':
            self.advance(',')
            _, n = self.advance()
            self.env.register(n, t, 'VAR')
        self.advance(';')
        self.wrap_end('varDec')

    def handle_statements(self):
        self.wrap_start('statements')
        while self.next_val() in ('let', 'if', 'while', 'do', 'return'):
            nxt = self.next_val()
            if nxt == 'let': self.eval_let()
            elif nxt == 'if': self.eval_if()
            elif nxt == 'while': self.eval_while()
            elif nxt == 'do': self.eval_do()
            elif nxt == 'return': self.eval_return()
        self.wrap_end('statements')

    def eval_let(self):
        self.wrap_start('letStatement')
        self.advance('let')
        _, i_name = self.advance() 
        is_arr = False

        if self.next_val() == '[':
            is_arr = True
            self.advance('[')
            info = self.env.resolve(i_name)
            self.emitter.push(self.map_seg(info[1]), info[2])
            self.handle_expression()
            self.emitter.write_op('add') 
            self.advance(']')

        self.advance('=')
        self.handle_expression() 
        self.advance(';')

        if is_arr:
            self.emitter.pop('temp', 0)       
            self.emitter.pop('pointer', 1)    
            self.emitter.push('temp', 0)
            self.emitter.pop('that', 0)       
        else:
            info = self.env.resolve(i_name)
            self.emitter.pop(self.map_seg(info[1]), info[2])
        self.wrap_end('letStatement')

    def eval_if(self):
        self.wrap_start('ifStatement')
        l_false, l_true = self.make_label(), self.make_label()
        
        self.advance('if')
        self.advance('(')
        self.handle_expression()
        self.advance(')')
        
        self.emitter.write_op('not')
        self.emitter.put_if(l_false)
        
        self.advance('{')
        self.handle_statements()
        self.advance('}')
        self.emitter.put_goto(l_true)
        self.emitter.put_label(l_false)
        
        if self.next_val() == 'else':
            self.advance('else')
            self.advance('{')
            self.handle_statements()
            self.advance('}')
        self.emitter.put_label(l_true)
        self.wrap_end('ifStatement')

    def eval_while(self):
        self.wrap_start('whileStatement')
        l_top, l_bot = self.make_label(), self.make_label()
        
        self.advance('while')
        self.emitter.put_label(l_top)
        self.advance('(')
        self.handle_expression()
        self.advance(')')
        
        self.emitter.write_op('not')
        self.emitter.put_if(l_bot)
        self.advance('{')
        self.handle_statements()
        self.advance('}')
        
        self.emitter.put_goto(l_top)
        self.emitter.put_label(l_bot)
        self.wrap_end('whileStatement')

    def eval_do(self):
        self.wrap_start('doStatement')
        self.advance('do')
        _, obj_name = self.advance()
        self.handle_call(obj_name)
        self.emitter.pop('temp', 0)
        self.advance(';')
        self.wrap_end('doStatement')

    def eval_return(self):
        self.wrap_start('returnStatement')
        self.advance('return')
        if self.next_val() != ';':
            self.handle_expression()
        else:
            self.emitter.push('constant', 0)
        self.advance(';')
        self.emitter.ret()
        self.wrap_end('returnStatement')

    def handle_call(self, root_id):
        if self.next_val() == '(':
            self.emitter.push('pointer', 0)
            self.advance('(')
            num_args = self.handle_expr_list()
            self.advance(')')
            self.emitter.call_func(f'{self.name}.{root_id}', num_args + 1)
        elif self.next_val() == '.':
            self.advance('.')
            _, sub_id = self.advance()
            info = self.env.resolve(root_id)
            if info is not None:
                self.emitter.push(self.map_seg(info[1]), info[2])
                self.advance('(')
                num_args = self.handle_expr_list()
                self.advance(')')
                self.emitter.call_func(f'{info[0]}.{sub_id}', num_args + 1)
            else:
                self.advance('(')
                num_args = self.handle_expr_list()
                self.advance(')')
                self.emitter.call_func(f'{root_id}.{sub_id}', num_args)

    def handle_expression(self):
        self.wrap_start('expression')
        self.handle_term()
        while self.next_val() in ('+', '-', '*', '/', '&', '|', '<', '>', '='):
            _, symb = self.advance()
            self.handle_term()
            if symb == '*': self.emitter.call_func('Math.multiply', 2)
            elif symb == '/': self.emitter.call_func('Math.divide', 2)
            else: self.emitter.write_op(ARITH_OPS[symb])
        self.wrap_end('expression')

    def handle_term(self):
        self.wrap_start('term')
        ttype, tval = self.cur_token()

        if ttype == 'integerConstant':
            self.advance()
            self.emitter.push('constant', int(tval))
        elif ttype == 'stringConstant':
            self.advance()
            self.emitter.push('constant', len(tval))
            self.emitter.call_func('String.new', 1)
            for ch in tval:
                self.emitter.push('constant', ord(ch))
                self.emitter.call_func('String.appendChar', 2)
        elif ttype == 'keyword' and tval in CONSTANTS:
            self.advance()
            if tval == 'true':
                self.emitter.push('constant', 0)
                self.emitter.write_op('not')
            elif tval in ('false', 'null'):
                self.emitter.push('constant', 0)
            elif tval == 'this':
                self.emitter.push('pointer', 0)
        elif tval == '(':
            self.advance('(')
            self.handle_expression()
            self.advance(')')
        elif tval in ('-', '~'):
            _, u_symb = self.advance()
            self.handle_term()
            self.emitter.write_op(UNARY_OPS[u_symb])
        elif ttype == 'identifier':
            _, ident_name = self.advance()
            if self.next_val() == '[':
                self.advance('[')
                info = self.env.resolve(ident_name)
                self.emitter.push(self.map_seg(info[1]), info[2])
                self.handle_expression()
                self.emitter.write_op('add')
                self.emitter.pop('pointer', 1)
                self.emitter.push('that', 0)
                self.advance(']')
            elif self.next_val() in ('(', '.'):
                self.handle_call(ident_name)
            else:
                info = self.env.resolve(ident_name)
                self.emitter.push(self.map_seg(info[1]), info[2])
        self.wrap_end('term')

    def handle_expr_list(self):
        self.wrap_start('expressionList')
        count = 0
        if self.next_val() != ')':
            self.handle_expression()
            count = 1
            while self.next_val() == ',':
                self.advance(',')
                self.handle_expression()
                count += 1
        self.wrap_end('expressionList')
        return count