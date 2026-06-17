import re
import os

KEYWORDS_LIST = {
    'class', 'constructor', 'function', 'method', 'field', 'static',
    'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null',
    'this', 'let', 'do', 'if', 'else', 'while', 'return'
}

XML_CHARS = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;'}

class Scanner:
    def __init__(self, src_path):
        self.file_name = os.path.splitext(os.path.basename(src_path))[0]
        with open(src_path, 'r') as f:
            self.content = f.read()
        self.scanned_tokens = []

    def remove_comments(self, text):
        out = []
        pos = 0
        sz = len(text)
        NORMAL, LINE_COMM, BLK_COMM, STR_LIT = 0, 1, 2, 3
        mode = NORMAL

        while pos < sz:
            if mode == NORMAL:
                if text[pos] == '"':
                    mode = STR_LIT
                    out.append(text[pos])
                    pos += 1
                elif pos + 1 < sz and text[pos] == '/' and text[pos + 1] == '/':
                    mode = LINE_COMM
                    pos += 2
                elif pos + 1 < sz and text[pos] == '/' and text[pos + 1] == '*':
                    mode = BLK_COMM
                    pos += 2
                else:
                    out.append(text[pos])
                    pos += 1
            elif mode == LINE_COMM:
                if text[pos] == '\n':
                    mode = NORMAL
                    out.append('\n')
                pos += 1
            elif mode == BLK_COMM:
                if pos + 1 < sz and text[pos] == '*' and text[pos + 1] == '/':
                    mode = NORMAL
                    pos += 2
                else:
                    if text[pos] == '\n':
                        out.append('\n')
                    pos += 1
            elif mode == STR_LIT:
                out.append(text[pos])
                if text[pos] == '"':
                    mode = NORMAL
                pos += 1
        return ''.join(out)

    PATT = re.compile(
        r'(\d+)'                        
        r'|(".*?")'                     
        r'|([a-zA-Z_]\w*)'              
        r'|([{}()\[\].,;+\-*/&|<>=~])'  
    )

    def process(self):
        purified = self.remove_comments(self.content)
        for match in self.PATT.finditer(purified):
            digits, string_val, ident, symb = match.groups()
            if digits is not None:
                self.scanned_tokens.append(('integerConstant', digits))
            elif string_val is not None:
                self.scanned_tokens.append(('stringConstant', string_val[1:-1])) 
            elif ident is not None:
                if ident in KEYWORDS_LIST:
                    self.scanned_tokens.append(('keyword', ident))
                else:
                    self.scanned_tokens.append(('identifier', ident))
            elif symb is not None:
                self.scanned_tokens.append(('symbol', symb))
        return self.scanned_tokens

    def save_xml(self, dest='.'):
        lines = ['<tokens>']
        for tk_type, tk_val in self.scanned_tokens:
            safe = ''.join(XML_CHARS.get(c, c) for c in tk_val)
            lines.append(f'<{tk_type}> {safe} </{tk_type}>')
        lines.append('</tokens>')
        final_path = os.path.join(dest, f'{self.file_name}T.xml')
        with open(final_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        return final_path