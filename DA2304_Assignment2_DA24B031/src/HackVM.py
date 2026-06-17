import os
class Parser:
    C_ARITHMETIC = 1
    C_PUSH = 2
    C_POP = 3
    C_LABEL = 4
    C_GOTO = 5
    C_IF = 6
    C_FUNCTION = 7
    C_RETURN = 8
    C_CALL = 9
    def __init__(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        self.commands = []
        for line in lines:
            cleaned = line.split('//')[0].strip()
            if cleaned:
                self.commands.append(cleaned)
        self.current_command = None
        self.current_idx = -1
        self.total_commands = len(self.commands)
    def has_more_commands(self):
        return self.current_idx < self.total_commands - 1
    def advance(self):
        self.current_idx += 1
        self.current_command = self.commands[self.current_idx]
    def command_type(self):
        cmd = self.current_command.split()[0]
        if cmd in ['add','sub','neg','eq','gt','lt','and','or','not']:
            return self.C_ARITHMETIC
        elif cmd == 'push': return self.C_PUSH
        elif cmd == 'pop': return self.C_POP
        elif cmd == 'label': return self.C_LABEL
        elif cmd == 'goto': return self.C_GOTO
        elif cmd == 'if-goto': return self.C_IF
        elif cmd == 'function': return self.C_FUNCTION
        elif cmd == 'call': return self.C_CALL
        elif cmd == 'return': return self.C_RETURN
    def arg1(self):
        if self.command_type() == self.C_ARITHMETIC:
            return self.current_command.split()[0]
        return self.current_command.split()[1]
    def arg2(self):
        return int(self.current_command.split()[2])
class CodeWriter: 
    def __init__(self, output_file):
        self.file = open(output_file, 'w')
        self.file_name = ""
        self.label_count = 0
        self.call_count = 0
        self.segments = {
            'local':'LCL','argument':'ARG','this':'THIS','that':'THAT'
        }
    def set_file_name(self, file_name):
        self.file_name = os.path.basename(file_name).replace('.vm','')
    def write_init(self):
        self.file.write("@256\nD=A\n@SP\nM=D\n")
        self.write_call("Sys.init",0)
    def write_arithmetic(self, command):
        if command in ['add','sub','and','or']:
            self.file.write("@SP\nAM=M-1\nD=M\nA=A-1\n")
            if command == 'add': self.file.write("M=D+M\n")
            elif command == 'sub': self.file.write("M=M-D\n")
            elif command == 'and': self.file.write("M=D&M\n")
            elif command == 'or': self.file.write("M=D|M\n")
        elif command in ['neg','not']:
            self.file.write("@SP\nA=M-1\n")
            if command == 'neg': self.file.write("M=-M\n")
            elif command == 'not': self.file.write("M=!M\n")
        elif command in ['eq','gt','lt']:
            self.file.write("@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n")
            label_true = f"TRUE_{self.label_count}"
            label_end = f"END_{self.label_count}"
            self.label_count += 1
            jump = "JEQ" if command == 'eq' else "JGT" if command == 'gt' else "JLT"
            self.file.write(f"@{label_true}\nD;{jump}\n")
            self.file.write("@SP\nA=M-1\nM=0\n")
            self.file.write(f"@{label_end}\n0;JMP\n")
            self.file.write(f"({label_true})\n@SP\nA=M-1\nM=-1\n")
            self.file.write(f"({label_end})\n")
    def write_push_pop(self, command, segment, index):
        if command == Parser.C_PUSH:
            if segment == 'constant':
                self.file.write(f"@{index}\nD=A\n")
            elif segment in self.segments:
                self.file.write(f"@{index}\nD=A\n@{self.segments[segment]}\nA=D+M\nD=M\n")
            elif segment == 'temp':
                self.file.write(f"@{5+int(index)}\nD=M\n")
            elif segment == 'pointer':
                self.file.write(f"@{'THIS' if index==0 else 'THAT'}\nD=M\n")
            elif segment == 'static':
                self.file.write(f"@{self.file_name}.{index}\nD=M\n")
            self.file.write("@SP\nA=M\nM=D\n@SP\nM=M+1\n")
        elif command == Parser.C_POP:
            if segment in self.segments:
                self.file.write(f"@{index}\nD=A\n@{self.segments[segment]}\nD=D+M\n")
            elif segment == 'temp':
                self.file.write(f"@{5+int(index)}\nD=A\n")
            elif segment == 'pointer':
                self.file.write(f"@{'THIS' if index==0 else 'THAT'}\nD=A\n")
            elif segment == 'static':
                self.file.write(f"@{self.file_name}.{index}\nD=A\n")
            self.file.write("@R13\nM=D\n")
            self.file.write("@SP\nAM=M-1\nD=M\n")
            self.file.write("@R13\nA=M\nM=D\n")
    def write_label(self, label):
        self.file.write(f"({label})\n")
    def write_goto(self, label):
        self.file.write(f"@{label}\n0;JMP\n")
    def write_if(self, label):
        self.file.write("@SP\nAM=M-1\nD=M\n")
        self.file.write(f"@{label}\nD;JNE\n")
    def write_call(self, function_name, num_args):
        return_label = f"RETURN_{function_name}_{self.call_count}"
        self.call_count += 1
        self.file.write(f"@{return_label}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
        for seg in ['LCL','ARG','THIS','THAT']:
            self.file.write(f"@{seg}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
        self.file.write(f"@SP\nD=M\n@{num_args}\nD=D-A\n@5\nD=D-A\n@ARG\nM=D\n")
        self.file.write("@SP\nD=M\n@LCL\nM=D\n")
        self.write_goto(function_name)
        self.write_label(return_label)
    def write_return(self):
        self.file.write("@LCL\nD=M\n@R14\nM=D\n")
        self.file.write("@5\nA=D-A\nD=M\n@R15\nM=D\n")
        self.file.write("@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D\n")
        self.file.write("@ARG\nD=M+1\n@SP\nM=D\n")
        for i,seg in enumerate(['THAT','THIS','ARG','LCL'],1):
            self.file.write(f"@R14\nD=M\n@{i}\nA=D-A\nD=M\n@{seg}\nM=D\n")
        self.file.write("@R15\nA=M\n0;JMP\n")
    def write_function(self, function_name, num_locals):
        self.write_label(function_name)
        for _ in range(num_locals):
            self.write_push_pop(Parser.C_PUSH,'constant',0)
    def close(self):
        self.file.close()