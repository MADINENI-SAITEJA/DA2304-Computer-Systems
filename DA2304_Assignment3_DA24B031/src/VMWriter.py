import os

class CodeEmitter:
    SEGMENTS = {
        'STATIC': 'static',
        'FIELD':  'this',
        'ARG':    'argument',
        'VAR':    'local',
    }

    def __init__(self, target_file):
        self.target_file = target_file
        self.instructions = []

    def push(self, seg, idx): self.instructions.append(f'push {seg} {idx}')
    def pop(self, seg, idx): self.instructions.append(f'pop {seg} {idx}')
    def write_op(self, cmd): self.instructions.append(cmd)
    def put_label(self, lbl): self.instructions.append(f'label {lbl}')
    def put_goto(self, lbl): self.instructions.append(f'goto {lbl}')
    def put_if(self, lbl): self.instructions.append(f'if-goto {lbl}')
    def call_func(self, name, args_count): self.instructions.append(f'call {name} {args_count}')
    def make_func(self, name, locals_count): self.instructions.append(f'function {name} {locals_count}')
    def ret(self): self.instructions.append('return')

    def flush(self):
        with open(self.target_file, 'w') as f:
            f.write('\n'.join(self.instructions) + '\n')