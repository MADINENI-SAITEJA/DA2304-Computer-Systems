class SymbolEnv:
    def __init__(self):
        self.class_symbols = {}
        self.method_symbols = {}
        self.indexes = {'STATIC': 0, 'FIELD': 0, 'ARG': 0, 'VAR': 0}

    def clear_subroutine(self):
        self.method_symbols = {}
        self.indexes['ARG'] = 0
        self.indexes['VAR'] = 0

    def clear_all(self):
        self.class_symbols = {}
        self.method_symbols = {}
        self.indexes = {'STATIC': 0, 'FIELD': 0, 'ARG': 0, 'VAR': 0}

    def register(self, name, data_type, kind):
        curr = self.indexes[kind]
        info = (data_type, kind, curr)
        if kind in ('STATIC', 'FIELD'):
            self.class_symbols[name] = info
        else:
            self.method_symbols[name] = info
        self.indexes[kind] += 1

    def resolve(self, name):
        if name in self.method_symbols:
            return self.method_symbols[name]
        if name in self.class_symbols:
            return self.class_symbols[name]
        return None

    def get_count(self, kind):
        return self.indexes.get(kind, 0)