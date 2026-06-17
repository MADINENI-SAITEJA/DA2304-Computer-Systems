# Jack Compiler Frontend (Assignment 3)

This module handles the frontend translation from Jack code to VM instructions.

## Included Components
* `JackCompiler.py`: Main entry point that handles file parsing logic.
* `JackTokenizer.py`: Reads raw text files, removes formatting and comments, and returns the token sequence.
* `CompilationEngine.py`: Processes the sequence via recursive descent and outputs VM operations.
* `SymbolTable.py`: Local and global scope manager.
* `VMWriter.py`: Command writer for final VM generation.

## Execution Requirements
* Built for standard Python 3 execution environments.
* No pip installs required.

## Terminal Commands
```bash
python3 src/JackCompiler.py <input_target> <output_location>

python3 src/JackCompiler.py jack/ out/

python3 src/JackCompiler.py jack/Conv.jack out/