from operator import gt, lt, eq, ge, le, ne

OPERATORS = {
    '>': gt, '<': lt, '==': eq,
    '>=': ge, '<=': le, '!=': ne
}

LOGIC_OPERATORS = {
    'AND': all,
    'OR': any,
    'NOT': lambda x: not x
}