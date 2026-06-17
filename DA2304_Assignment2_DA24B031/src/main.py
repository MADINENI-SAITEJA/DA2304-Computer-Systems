import sys
import os
from HackVM import Parser, CodeWriter

def process_file(file_path, writer):
    print(f"Translating {os.path.basename(file_path)}...")
    parser = Parser(file_path)
    writer.set_file_name(file_path)
    while parser.has_more_commands():
        parser.advance()
        cmd_type = parser.command_type()
        if cmd_type == Parser.C_ARITHMETIC:
            writer.write_arithmetic(parser.arg1())
        elif cmd_type in [Parser.C_PUSH, Parser.C_POP]:
            writer.write_push_pop(cmd_type, parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_LABEL:
            writer.write_label(parser.arg1())
        elif cmd_type == Parser.C_GOTO:
            writer.write_goto(parser.arg1())
        elif cmd_type == Parser.C_IF:
            writer.write_if(parser.arg1())
        elif cmd_type == Parser.C_FUNCTION:
            writer.write_function(parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_CALL:
            writer.write_call(parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_RETURN:
            writer.write_return()

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <file.vm or directory_path>")
        sys.exit(1)
    input_path = os.path.abspath(sys.argv[1])
    if os.path.isdir(input_path):
        dir_name = os.path.basename(input_path.rstrip(os.sep))
        output_file = os.path.join(input_path, f"{dir_name}.asm")
        vm_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.vm')]
        writer = CodeWriter(output_file)
        writer.write_init()
        for vm_file in vm_files:
            process_file(vm_file, writer)     
    elif os.path.isfile(input_path) and input_path.endswith('.vm'):
        output_file = input_path.replace('.vm', '.asm')
        writer = CodeWriter(output_file)
        process_file(input_path, writer)  
    else:
        print("Error: Input must be a .vm file or a directory containing .vm files.")
        sys.exit(1)
    writer.close()
    print(f"Translation successful. Output written to {output_file}")

if __name__ == "__main__":
    main()