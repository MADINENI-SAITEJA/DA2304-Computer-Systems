import sys
import os
import glob
from JackTokenizer import Scanner
from CompilationEngine import JackParser

def build_target(src_path, dest_dir):
    file_prefix = os.path.splitext(os.path.basename(src_path))[0]
    print(f"[Build] Compiling {src_path} -> {file_prefix}T.xml, {file_prefix}.xml, {file_prefix}.vm")
    tokenizer = Scanner(src_path)
    token_list = tokenizer.process()
    tokenizer.save_xml(dest_dir)
    parser = JackParser(token_list, file_prefix, dest_dir)
    parser.parse_class()

def execute():
    if len(sys.argv) < 2:
        print("Usage: python JackCompiler.py <file.jack | directory>")
        sys.exit(1)
    target_entry = sys.argv[1]
    out_folder = sys.argv[2] if len(sys.argv) > 2 else '.'
    os.makedirs(out_folder, exist_ok=True)
    
    if os.path.isdir(target_entry):
        for jack_f in sorted(glob.glob(os.path.join(target_entry, '*.jack'))):
            build_target(jack_f, out_folder)
    elif os.path.isfile(target_entry) and target_entry.endswith('.jack'):
        build_target(target_entry, out_folder)
    else:
        print("Error: Target is not a .jack file or directory")

if __name__ == '__main__':
    execute()