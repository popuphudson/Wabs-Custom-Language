import time
import importlib.util
import os

filesrunning = []

####################
#       LEXER      #
####################

def Lex(text) -> tuple:
    typ = ''
    col = ''
    tokens = []
    i = 0
    comment = False
    extra = []
    while i < len(text):
        l = text[i]
        if comment:
            if l == '\n':
                comment = False
            i += 1
            continue
        if l == '#':
            comment = True
        elif col in ('sleep', 'break', 'continue', 'print', 'nlprint', 'pop', 'lengthto', 'add', 'sub', 'set', 'mul', 'div', 'run', 'opento', 'if', 'then', 'return', 'end', 'for', 'while', 'inputstr', 'inputint', 'func', 'ncall', 'rcall', 'get', 'index', 'size', 'append', 'toint', 'tostr', 'writeto', 'else', 'update', 'access', 'at', 'remove', 'getkeys', 'getvalues', 'import') and typ == '' and l in " \n\t\r":
            tokens.append({'type': 'KEYWORD', 'value': col})
            col = ''
        elif col in ('true', 'false') and typ == '' and l in " \n\r\t":
            tokens.append({'type': 'BOOL', 'value':col=="true"})
            col = ''
        elif col in ('from', 'to') and typ == '' and l == " ":
            tokens.append({'type': 'OP', 'value':col})
            col = ''
        elif col in ('==', '!=', '<', '>', '<=', '>=') and typ == '' and l not in '=<>!':
            tokens.append({'type': 'OP', 'value':col})
            col = ''
        elif l in '-0123456789' and typ == '' and col == '':
            col += l
            typ = 'int'
            i += 1
        elif l in '1234567890' and typ == 'int':
            col += l
            i += 1
        elif l == '.' and typ == 'int':
            typ = "float"
            col += l
            i += 1
        elif l == '(' and typ == '':
            if col != '':
                tokens.append({'type': 'UNKNOWN', 'value': col})
                col = ''
            tokens.append({'type': 'KEYWORD', 'value':'openp'})
            i += 1
        elif l == ')' and typ == '':
            if col != '':
                tokens.append({'type': 'UNKNOWN', 'value': col})
                col = ''
            tokens.append({'type': 'KEYWORD', 'value':'closep'})
            i += 1
        elif l == '[':
            extra.append([len(tokens), 'list'])
            i += 1
        elif l == '{':
            extra.append([len(tokens), 'dict'])
            i += 1
        elif l == '"' and typ == '':
            typ = 'str'
            i += 1
        elif l == '"' and typ == 'str':
            tokens.append({'type': 'STRING', 'value':col})
            col = ''
            typ = ''
            i += 1
        elif typ == 'int' and l not in '1234567890' and col != '':
            tokens.append({'type': 'INT', 'value': int(col)})
            typ = ''
            col = ''
        elif typ == 'float' and l not in '1234567890' and col != '':
            tokens.append({'type': 'FLOAT', 'value': float(col)})
            typ = ''
            col = ''
        elif l == ',':
            if col != '' and typ == '':
                tokens.append({'type': 'UNKNOWN', 'value': col})
                col = ''
            tokens.append({'type': 'KEYWORD', 'value':'comma'})
            i += 1
        elif l == ':':
            if col != '' and typ == '':
                tokens.append({'type': 'UNKNOWN', 'value': col})
                col = ''
            tokens.append({'type': 'KEYWORD', 'value':'colon'})
            i += 1
        elif l == '}' and len(extra) > 0:
            if col != '' and typ == '':
                tokens.append({'type': 'UNKNOWN', 'value': col})
                col = ''
            dictionary = {}
            temp = []
            stage = "key"
            for ext in tokens[extra[-1][0]:]:
                if stage == "key":
                    temp.append((ext['type'], ext['value']))
                    stage = "colon"
                elif stage == "colon" and ext['type'] == "KEYWORD" and ext['value'] == "colon":
                    stage = "value"
                elif stage == "value":
                    temp.append((ext['type'], ext['value']))
                    stage = "seperate"
                elif stage == "seperate":
                    dictionary.update({temp[0]:temp[1]})
                    temp = []
                    stage = "key"
            if stage == "seperate":
                dictionary.update({temp[0]:temp[1]})
            tokens.append({'type': 'DICT', 'value':dictionary})
            tokens = tokens[:extra[-1][0]]+[tokens[-1]]
            extra.pop()
            if len(extra) == 0:
                typ = ''
            else:
                typ = extra[-1][1]
            i += 1
        elif l == ']' and len(extra) > 0:
            if col != '' and typ == '':
                tokens.append({'type': 'UNKNOWN', 'value': col})
                col = ''
            extract = []
            seperator = True
            for ext in tokens[extra[-1][0]:]:
                if seperator:
                    extract.append((ext['type'], ext['value']))
                    seperator = False
                elif ext['type'] == "KEYWORD" and ext['value'] == 'comma':
                    seperator = True
                else:
                    raise(SyntaxError("Items in a list need to be seperated by a comma!"))
            tokens.append({'type': 'LIST', 'value':extract})
            tokens = tokens[:extra[-1][0]]+[tokens[-1]]
            extra.pop()
            if len(extra) == 0:
                typ = ''
            else:
                typ = extra[-1][1]
            i += 1
        elif col != '' and l in ' \r\t' and typ != 'str':
            tokens.append({'type': 'UNKNOWN', 'value': col})
            col = ''
            i += 1
        elif l == '\n':
            if col != '' and typ != 'str':
                tokens.append({'type': 'UNKNOWN', 'value': col})
                col = ''
            tokens.append({'type': 'NEWLINE'})
            i += 1
        elif typ == 'str':
            col += l
            i += 1
        elif l not in ' \n\r\t':
            col += l
            i += 1
        else:
            i += 1
    if col != '':
        print('Hey something didn\'t work while lexing must be you not me')
        return (tokens, True)
    return (tokens, False)
   
####################
#      PARSER      #
####################

def CompressTogether(tokens) -> tuple:
    typ = ''
    col = []
    coll = []
    comp = []
    ind = -1
    i = 0
    line = 0
    while i < len(tokens):
        t = tokens[i]
        if t['type'] == 'KEYWORD':
            if t['value'] == "update":
                typ = "update"
            elif t['value'] == 'append':
                typ = 'append'
            elif t['value'] == 'access':
                typ = 'access'
            elif t['value'] == 'getkeys':
                typ = 'getkeys'
            elif t['value'] == 'getvalues':
                typ = 'getvalues'
            elif t['value'] == 'import':
                typ = 'import'
            elif t['value'] == 'remove':
                typ = 'remove'
            elif t['value'] == 'at' and typ == 'access':
                typ = 'access_at'
            elif t['value'] == 'set' and typ == 'index':
                typ = 'index_set'
            elif t['value'] == 'set':
                typ = 'set'
            elif t['value'] == 'writeto':
                typ = 'writeto'
            elif t['value'] == 'add':
                typ = 'add'
            elif t['value'] == 'toint':
                typ = 'toint'
            elif t['value'] == 'tostr':
                typ = 'tostr'
            elif t['value'] == 'lengthto':
                typ = 'lengthto'
            elif t['value'] == 'mul':
                typ = 'mul'
            elif t['value'] == 'break':
                comp.append({'type':'break'})
            elif t['value'] == 'continue':
               comp.append({'type':'continue'})
            elif t['value'] == 'div':
                typ = 'div'
            elif t['value'] == 'get':
                typ = 'get'
            elif t['value'] == 'sub':
                typ = 'sub'
            elif t['value'] == 'pop':
                typ = 'pop'
            elif t['value'] == 'return':
                typ = 'return'
            elif t['value'] == 'if':
                typ = 'if'
            elif t['value'] == 'nlprint':
                typ = 'nlprint'
            elif t['value'] == 'for':
                typ = 'for'
            elif t['value'] == 'run':
                typ = 'run'
            elif t['value'] == 'opento':
                typ = 'opento'
            elif t['value'] == 'while':
                typ = 'while'
            elif t['value'] == 'func':
                typ = 'func'
            elif t['value'] == 'ncall':
                typ = 'ncall'
            elif t['value'] == 'inputstr':
                typ = 'inputstr'
            elif t['value'] == 'inputint':
                typ = 'inputint'
            elif t['value'] == 'print':
                typ = 'print'
            elif t['value'] == 'sleep':
                typ = 'sleep'
            elif t['value'] == 'index' and typ == 'get':
                typ = 'get_index'
            elif t['value'] == 'index':
                typ = 'index'
            elif t['value'] == 'comma' and typ in ('call_getparam_next', 'callto_getparam_next', 'func_getparam_next'):
                typ = typ[:len(typ)-5]
            elif t['value'] == 'openp' and typ == 'ncall':
                typ = 'call_getparam_start'
                col.append('(')
            elif t['value'] == 'closep' and typ in ('call_getparam_next', 'call_getparam_start'):
                typ = ''
                col.reverse()
                temp = col.copy()
                overall = []
                col.reverse()
                for t in temp:
                    if t == '(':
                        col.remove(t)
                        break
                    else:
                        overall.append(t)
                        col.remove(t)
                overall.reverse()
                comp.append({'type': 'ncall', 'value': [col[0], overall]})
                col = []
            elif t['value'] == 'rcall':
                typ = 'callto'
            elif t['value'] == 'openp' and typ == 'callto':
                typ = 'callto_getparam_start'
                col.append('(')
            elif t['value'] == 'closep' and typ in ('callto_getparam_next', 'callto_getparam_start'):
                typ = 'callto_final'
                col.reverse()
                temp = col.copy()
                overall = []
                col.reverse()
                for t in temp:
                    if t == '(':
                        col.remove(t)
                        break
                    else:
                        overall.append(t)
                        col.remove(t)
                overall.reverse()
                col.append(overall)
            elif t['value'] == 'openp' and typ == 'func':
                typ = 'func_getparam_start'
                col.append('(')
            elif t['value'] == 'closep' and typ in ('func_getparam_next', 'func_getparam_start'):
                typ = 'func'
                col.reverse()
                temp = col.copy()
                overall = []
                col.reverse()
                for t in temp:
                    if t == '(':
                        col.remove(t)
                        break
                    else:
                        overall.append(t)
                        col.remove(t)
                overall.reverse()
                col.append(overall)
            elif t['value'] == 'then' and typ == 'if':
                precoll = col
                precoll.insert(0, len(comp)-1)
                precoll.insert(1, 'if')
                coll.append(precoll)
                ind += 1
                col = []
                typ = ''
            elif t['value'] == 'then' and typ == 'func':
                precoll = col
                precoll.insert(0, len(comp)-1)
                precoll.insert(1, 'func')
                coll.append(precoll)
                ind += 1
                col = []
                typ = ''
            elif t['value'] == 'then' and typ == 'for':
                precoll = col
                precoll.insert(0, len(comp)-1)
                precoll.insert(1, 'for')
                coll.append(precoll)
                ind += 1
                col = []
                typ = ''
            elif t['value'] == 'then' and typ == 'while':
                precoll = col
                precoll.insert(0, len(comp)-1)
                precoll.insert(1, 'while')
                coll.append(precoll)
                ind += 1
                col = []
                typ = ''
            elif t['value'] == 'end':
                if len(coll[ind]) == 0:
                    raise(SyntaxError('There is an end endding nothing somewhere'))
                if len(coll[ind]) != 5 and coll[ind][1] == 'while':
                    raise(SyntaxError(f'There is an uncomplete while statment dummy'))
                if len(coll[ind]) != 5 and coll[ind][1] == 'if':
                    raise(SyntaxError(f'There is an uncomplete if statment dummy'))
                if len(coll[ind]) != 6 and coll[ind][1] == 'ifelse':
                    raise(SyntaxError(f'There is an uncomplete if else statment dummy'))
                if len(coll[ind]) != 4 and coll[ind][1] == 'func':
                    print(len(coll[ind]))
                    raise(SyntaxError(f'There is an uncomplete function statment dummy'))
                if len(coll[ind]) != 7 and coll[ind][1] == 'for': 
                    raise(SyntaxError(f'There is an uncomplete for statment dummy'))

                if coll[ind][1] == "ifelse":
                    ifcompen = comp[coll[ind][0]+1:coll[ind][2]+1]
                    elsecompen = comp[coll[ind][2]+1:]
                    comp = comp[:coll[ind][0]+1]
                    colltad = coll[ind][3:]
                    comp.append({'type': "if_else", 'value': [colltad, ifcompen, elsecompen]})
                else:
                    compen = comp[coll[ind][0]+1:]
                    comp = comp[:coll[ind][0]+1]
                    colltad = coll[ind][2:]
                    comp.append({'type': coll[ind][1], 'value': [colltad, compen]})
                coll.pop()
                ind -= 1
            elif t['value'] == "else":
                coll[ind][1] = "ifelse"
                coll[ind].insert(2, len(comp)-1)

            i += 1
        elif t['type'] == 'UNKNOWN':
            if typ in ('inputstr', 'inputint', 'print', 'return', 'run', 'pop', 'nlprint', 'tostr', 'toint', 'import'):
                comp.append({'type': typ, 'value':[("UNKNOWN", t['value'])]})
                typ = ''
            elif typ == 'index_set':
                comp.append({'type': 'setindex', 'value':[col[0], col[1], ("UNKNOWN", t['value'])]})
                col = []
                typ = ''
            elif typ == 'callto_final':
                comp.append({'type': 'rcall', 'value':[col[0], col[1], ("UNKNOWN", t['value'])]})
                col = []
                typ = ''
            elif typ == 'get_index':
                comp.append({'type': 'getindex', 'value':[col[0], col[1], ("UNKNOWN", t['value'])]})
                col = []
                typ = ''
            elif typ == 'access':
                col.append(("UNKNOWN", t['value']))
            elif typ == 'access_at':
                comp.append({'type': 'access', 'value':[col[0], col[1], ("UNKNOWN", t['value'])]})
                typ = ''
                col = []
            elif typ in ('set', 'add', 'sub', 'mul', 'div', 'append', 'opento', 'lengthto', 'writeto', 'getkeys', 'getvalues', 'remove'):
                comp.append({'type': typ, 'value':[col[0], ("UNKNOWN", t['value'])]})
                col = []
                typ = ''
            elif typ in ('call_getparam', 'callto_getparam', 'func_getparam'):
                typ = typ + '_next'
                col.append(("UNKNOWN", t['value']))
            elif typ in ('call_getparam_start', 'callto_getparam_start', 'func_getparam_start'):
                typ = typ[:len(typ)-6] + '_next'
                col.append(("UNKNOWN", t['value']))
            else:
                col.append(("UNKNOWN", t['value']))
            i += 1
        elif t['type'] == 'INT':
            if typ in ('set', 'add', 'sub', 'mul', 'div', 'append', 'remove'):
                comp.append({'type': typ, 'value':[col[0], ("INT", t['value'])]})
                col = []
                typ = ''
            elif typ == 'index_set':
                comp.append({'type': 'setindex', 'value':[col[0], col[1], ("INT", t['value'])]})
                col = []
                typ = ''
            elif typ == 'get_index':
                comp.append({'type': 'getindex', 'value':[col[0], col[1], ("INT", t['value'])]})
                col = []
                typ = ''
            elif typ in ('sleep', 'print', 'return', 'nlprint'):
                comp.append({'type': typ, 'value':[("INT", t['value'])]})
                typ = ''
            elif typ == 'access_at':
                comp.append({'type': 'access', 'value':[col[0], col[1], ("INT", t['value'])]})
                typ = ''
                col = []
            elif typ in ('call_getparam', 'callto_getparam', 'func_getparam'):
                typ = typ + '_next'
                col.append(("INT", t['value']))
            elif typ in ('call_getparam_start', 'callto_getparam_start', 'func_getparam_start'):
                typ = typ[:len(typ)-6] + '_next'
                col.append(("INT", t['value']))
            else:
                col.append(("INT", t['value']))
            i += 1
        elif t['type'] == 'STRING':
            if typ in ('add', 'set', 'append', 'remove'):
                comp.append({'type': typ, 'value':[col[0], ("STR", t['value'])]})
                col = []
                typ = ''
            elif typ == 'index_set':
                comp.append({'type': 'setindex', 'value':[col[0], col[1], ("STR", t['value'])]})
                col = []
                typ = ''
            elif typ in ('print', 'return', 'nlprint'):
                comp.append({'type': typ, 'value':[("STR", t['value'])]})
                typ = ''
            elif typ == 'access_at':
                comp.append({'type': 'access', 'value':[col[0], col[1], ("STR", t['value'])]})
                typ = ''
                col = []
            elif typ in ('call_getparam', 'callto_getparam', 'func_getparam'):
                typ = typ + '_next'
                col.append(("STR", t['value']))
            elif typ in ('call_getparam_start', 'callto_getparam_start', 'func_getparam_start'):
                typ = typ[:len(typ)-6] + '_next'
                col.append(("STR", t['value']))
            else:
                col.append(("STR", t['value']))
            i += 1
        elif t['type'] == 'OP':
            col.append(t['value'])
            i += 1
        elif t['type'] == 'NEWLINE':
            comp.append({'type':'NEWLINE', 'value':line})
            line += 1
            i += 1
        elif t['type'] == "BOOL":
            if typ in ('set', 'append', 'remove'):
                comp.append({'type': typ, 'value':[col[0], ("BOOL", t['value'])]})
                col = []
                typ = ''
            elif typ == 'index_set':
                comp.append({'type': 'setindex', 'value':[col[0], col[1], ("BOOL", t['value'])]})
                col = []
                typ = ''
            elif typ in ('print', 'return', 'nlprint'):
                comp.append({'type': typ, 'value':[("BOOL", t['value'])]})
                typ = ''
            elif typ == 'access_at':
                comp.append({'type': 'access', 'value':[col[0], col[1], ("BOOL", t['value'])]})
                typ = ''
                col = []
            elif typ in ('call_getparam', 'callto_getparam', 'func_getparam'):
                typ = typ + '_next'
                col.append(("BOOL", t['value']))
            elif typ in ('call_getparam_start', 'callto_getparam_start', 'func_getparam_start'):
                typ = typ[:len(typ)-6] + '_next'
                col.append(("BOOL", t['value']))
            else:
                col.append(("BOOL", t['value']))
            i += 1
        elif t['type'] == "LIST":
            if typ in ("set", 'append'):
                comp.append({'type': typ, 'value':[col[0], ("LIST", t['value'])]})
                col = []
                typ = ''
            elif typ in ('print', 'return', 'nlprint'):
                comp.append({'type': typ, 'value':[("LIST", t['value'])]})
                typ = ''
            elif typ == 'updatevalue':
                comp.append({'type': 'update', 'value':[col[0], col[1], ("LIST", t['value'])]})
                typ = ''
                col = []
            elif typ in ('call_getparam', 'callto_getparam', 'func_getparam'):
                typ = typ + '_next'
                col.append(("LIST", t['value']))
            elif typ in ('call_getparam_start', 'callto_getparam_start', 'func_getparam_start'):
                typ = typ[:len(typ)-6] + '_next'
                col.append(("LIST", t['value']))
            i += 1
        elif t['type'] == "DICT":
            if typ in ("set", 'append', 'update'):
                comp.append({'type': typ, 'value':[col[0], ("DICT", t['value'])]})
                col = []
                typ = ''
            elif typ in ('print', 'return', 'nlprint'):
                comp.append({'type': typ, 'value':[("DICT", t['value'])]})
                typ = ''
            elif typ in ('call_getparam', 'callto_getparam', 'func_getparam'):
                typ = typ + '_next'
                col.append(("DICT", t['value']))
            elif typ in ('call_getparam_start', 'callto_getparam_start', 'func_getparam_start'):
                typ = typ[:len(typ)-6] + '_next'
                col.append(("DICT", t['value']))
            else:
                col.append(("DICT", t['value']))
            i += 1
        elif t['type'] == 'FLOAT':
            if typ in ('set', 'add', 'sub', 'mul', 'div', 'append', 'remove'):
                comp.append({'type': typ, 'value':[col[0], ("FLOAT", t['value'])]})
                col = []
                typ = ''
            elif typ in ('sleep', 'print', 'return', 'nlprint'):
                comp.append({'type': typ, 'value':[("FLOAT", t['value'])]})
                typ = ''
            elif typ == 'access_at':
                comp.append({'type': 'access', 'value':[col[0], col[1], ("FLOAT", t['value'])]})
                typ = ''
                col = []
            elif typ in ('call_getparam', 'callto_getparam', 'func_getparam'):
                typ = typ + '_next'
                col.append(("FLOAT", t['value']))
            elif typ in ('call_getparam_start', 'callto_getparam_start', 'func_getparam_start'):
                typ = typ[:len(typ)-6] + '_next'
                col.append(("FLOAT", t['value']))
            else:
                col.append(("FLOAT", t['value']))
            i += 1
        else:
            i += 1
    if col != []:
        print('The parsing proccess went wrong must be you not me')
        print(col)
        print(comp)
        return (comp, True)
    return (comp, False)

####################
#     Evaluator    #
####################

line = 1

def If(c, vars):
    value = None
    if c['value'][0][0][0] == "UNKNOWN":
        if c['value'][0][0][1] not in vars:
            raise(ReferenceError(f"{c['value'][0][0][1]} is not a active variable"))
        else:
            value = vars[c['value'][0][0][1]]
    else:
        value = c['value'][0][0][1]
    if value == None:
        raise(SyntaxError("IDK WHAT HAPPENED"))

    compare = None
    if c['value'][0][2][0] == "UNKNOWN":
        if c['value'][0][2][1] not in vars:
            raise(ReferenceError(f"{c['value'][0][2][1]} is not a active variable"))
        else:
            compare = vars[c['value'][0][2][1]]
    else:
        compare = c['value'][0][2][1]
    if compare == None:
        raise(SyntaxError("IDK WHAT HAPPENED"))

    if type(compare) is not type(value):
        raise(TypeError(f"Can't compare {type(value)} and {type(compare)}"))
    do = False
    if c['value'][0][1] not in ('==', '!=', '<', '>', '<=', '>='):
        raise(SyntaxError("You need to format an if as VALUE OP VALUE"))
    if c['value'][0][1] == '==':
        if value == compare:
            do = True

    if c['value'][0][1] == '!=':
        if value != compare:
            do = True

    if c['value'][0][1] == '<':
        if value < compare:
            do = True

    if c['value'][0][1] == '>':
        if value > compare:
            do = True

    if c['value'][0][1] == '<=':
        if value <= compare:
            do = True

    if c['value'][0][1] == '>=':
        if value >= compare:
            do = True

    return do

def VariableIsDict(i, vars, notvar, notdict):
    global line
    if i[0] != "UNKNOWN":
        raise(TypeError(notvar + f" at line {line}"))
    if i[1] not in vars:
        raise(ReferenceError(f"{i[1]} is not a active variable" + f" at line {line}"))
    if isinstance(vars[i[1]], dict) is False:
        raise(TypeError(notdict + f" at line {line}"))

def VariableNotAListOrDict(i,vars, notvar, islist, isdict):
    VariableNotAList(i, vars, notvar, islist)
    VariableNotADict(i, vars, notvar, isdict)

def VariableNotADict(i,vars, notvar, isdict):
    global line
    if i[0] != "UNKNOWN":
        raise(TypeError(notvar + f" at line {line}"))
    if i[1] not in vars:
        raise(ReferenceError(f"{i[1]} is not a active variable at line {line}"))
    if isinstance(vars[i[1]], list):
        raise(TypeError(isdict + f" at line {line}"))

def VariableNotAList(i, vars, notvar, islist):
    global line
    if i[0] != "UNKNOWN":
        raise(TypeError(notvar + f" at line {line}"))
    if i[1] not in vars:
        raise(ReferenceError(f"{i[1]} is not a active variable at line {line}"))
    if isinstance(vars[i[1]], list):
        raise(TypeError(islist + f" at line {line}"))

def VariableIsList(i, vars, notvar, notlist):
    global line
    if i[0] != "UNKNOWN":
        raise(TypeError(notvar + f" at line {line}"))
    if i[1] not in vars:
        raise(ReferenceError(f"{i[1]} is not a active variable" + f" at line {line}"))
    if isinstance(vars[i[1]], list) is False:
        raise(TypeError(notlist + f" at line {line}"))

def IsVariable(i, vars, notvar):
    global line
    if i[0] != "UNKNOWN":
        raise(TypeError(notvar + f" at line {line}"))
    if i[1] not in vars:
        raise(ReferenceError(f"{i[1]} is not a active variable" + f" at line {line}"))

def GetValueAll(i, vars):
    value = None
    if i[0] == "UNKNOWN":
        if i[1] not in vars:
            raise(ReferenceError(f"{i[1]} is not a active variable" + f" at line {line}"))
        else:
            value = vars[i[1]]
    elif i[0] == "DICT":
        value = {}
        for k, v in i[1].items():
            value.update({GetValueAll(k, vars):GetValueAll(v, vars)})
    elif i[0] == "LIST":
        value = []
        for val in i[1]:
            value.append(GetValueAll(val, vars))
    else:
        value = i[1]
    if value == None:
        raise(SyntaxError("IDK WHAT HAPPENED"))
    return value

def GetNumberValue(i, vars, string, listed):
    value = None
    if i[0] == "UNKNOWN":
        if i[1] not in vars:
            raise(ReferenceError(f"{i[1]} is not a active variable" + f" at line {line}"))
        elif isinstance(vars[i[1]], list):
            raise(TypeError(listed + f" at line {line}"))
        else:
            value = vars[i[1]]
    elif i[0] in ("INT", "FLOAT"):
        value = i[1]
    else:
        raise(TypeError(string + f" at line {line}"))
    if value == None:
        raise(SyntaxError("IDK WHAT HAPPENED"))
    return value

def Evaluate(compr:list, _vars:dict, _funcs:dict, _defualt_ret=None) -> tuple:
    global line
    vars = _vars
    funcs = _funcs
    ret = _defualt_ret
    for c in compr:
        if c['type'] == 'func':
            funcs.update({c['value'][0][0][1]:{'params':c['value'][0][1], 'contents':c['value'][1]}})
    for c in compr:
        if c['type'] == 'NEWLINE':
            line = c['value']
        elif c['type'] == 'set':
            if c['value'][0][0] == "UNKNOWN":
                if c['value'][0][1] not in vars:
                    vars.update({c['value'][0][1]:None})
            IsVariable(c['value'][0], vars, "set needs to begin with a variable")
            value = GetValueAll(c['value'][1], vars)
            vars.update({c['value'][0][1]:value})
        elif c['type'] == 'add':
            VariableNotADict(c['value'][0], vars, "add needs to begin with a variable", "variable can't be a dict")
            value = GetValueAll(c['value'][1], vars)
            if isinstance(value, list):
                raise(TypeError("Can't add a list"))
            if type(vars[c['value'][0][1]]) is type(value) is False:
                raise(ReferenceError(f"Can't add {type(vars[c['value'][0][1]])} and {type(value)} together."))
            vars.update({c['value'][0][1]:vars[c['value'][0][1]]+value})
        elif c['type'] == 'sub':
            VariableNotAListOrDict(c['value'][0], vars, "sub needs to begin with a variable", "variable can't be a list", "variable can't be a dict")
            value = GetNumberValue(c['value'][1], vars, "Can't subtract a string", "Can't subtract a list")
            if type(vars[c['value'][0][1]]) is type(value) is False:
                raise(ReferenceError(f"Can't subtract {type(vars[c['value'][0][1]])} and {type(value)} together."))
            vars.update({c['value'][0][1]:vars[c['value'][0][1]]-value})
        elif c['type'] == 'div':
            VariableNotAListOrDict(c['value'][0], vars, "div needs to begin with a variable", "variable can't be a list", "variable can't be a dict")
            value = GetNumberValue(c['value'][1], vars, "Can't divide a string", "Can't divide by a list")
            if type(vars[c['value'][0][1]]) is type(value) is False:
                raise(ReferenceError(f"Can't divide {type(vars[c['value'][0][1]])} and {type(value)} together."))
            if isinstance(value, int):
                vars.update({c['value'][0][1]:vars[c['value'][0][1]]//value})
            else:
                vars.update({c['value'][0][1]:vars[c['value'][0][1]]/value})
        elif c['type'] == 'mul':
            VariableNotAListOrDict(c['value'][0], vars, "mul needs to begin with a variable", "variable can't be a list", "variable can't be a dict")
            value = GetNumberValue(c['value'][1], vars, "Can't multiply a string", "Can't multiply by a list")
            if type(vars[c['value'][0][1]]) is type(value) is False:
                raise(ReferenceError(f"Can't multiply {type(vars[c['value'][0][1]])} and {type(value)} together."))
            vars.update({c['value'][0][1]:vars[c['value'][0][1]]*value})
        elif c['type'] == 'print':
            value = GetValueAll(c['value'][0], vars)
            if isinstance(value, bool):
                print(f"{value}".lower())
            else:
                print(value)
        elif c['type'] == 'append':
            VariableIsList(c['value'][0], vars, "can only append to a variable", 'can only append to a list')
            value = GetValueAll(c['value'][1], vars)
            vars[c['value'][0][1]].append(value)
        elif c['type'] == 'setindex':
            VariableIsList(c['value'][0], vars, "Have to index a variable", "Can't index a non list")
            index = GetNumberValue(c['value'][1], vars, "can't index with a string", "can't index with a list")       
            value = GetValueAll(c['value'][2], vars)
            if isinstance(value, list):
                raise(TypeError("Can't put a list in a list"))  
            vars[c['value'][0][1]][index] = value
        elif c['type'] == 'getindex':
            if c['value'][0][0] == "UNKNOWN":
                if c['value'][0][1] not in vars:
                    vars.update({c['value'][0][1]:None})
            IsVariable(c['value'][0], vars, "Can't save index to a non variable")

            if c['value'][1][0] != "UNKNOWN":
                raise(TypeError("can't index something that isn't a list"))
            if c['value'][1][1] not in vars:
                raise(KeyError(f"{c['value'][1][1]} doesn't exist"))
            if isinstance(vars[c['value'][1][1]], list) is False and isinstance(vars[c['value'][1][1]], str) is False:
                raise(TypeError("can't index from a normal var"))

            index = GetNumberValue(c['value'][2], vars, "Can't index with a string", "Can't index with a list")
            if index >= len(vars[c['value'][1][1]]):
                raise(IndexError(f"{index} is not in {vars[c['value'][1][1]]} at line {line}"))
            if index < 0:
                raise(IndexError(f"{index} is not in {vars[c['value'][1][1]]} at line {line}"))
            vars[c['value'][0][1]] = vars[c['value'][1][1]][index]
        elif c['type'] == 'pop':
            VariableIsList(c['value'][0], vars, "Can't pop from a non variable", "Can't pop from a non list")
            vars[c['value'][0][1]].pop()
        elif c['type'] == 'sleep':
            lengthoftime = GetNumberValue(c['value'][0], vars, "Can't sleep for a string amount of time", "Can't sleep for a list amount of time")
            time.sleep(lengthoftime/1000)
        elif c['type'] == 'inputstr':
            VariableNotAListOrDict(c['value'][0], vars, "Can't input to a non variable", "Can't input to a list (strings are auto lists anyway)", "cannot input directly into a dict!")
            vars[c['value'][0][1]] = input('>>> ')
        elif c['type'] == 'inputint':
            VariableNotAListOrDict(c['value'][0], vars, "Can't input to a non variable", "Can't input to a list", "Can't input to a dict")
            result = ''
            while isinstance(result, str):
                try:
                    result = int(input('>>> '))
                except ValueError:
                    print("That isn't a number")
            vars[c['value'][0][1]] = result
        elif c['type'] == 'if':
            if If(c, vars):
                ret = Evaluate(c['value'][1], vars, funcs, ret)
                if ret == 1 or ret == 2:
                    break
        elif c['type'] == "if_else":
            if If(c, vars):
                ret = Evaluate(c['value'][1], vars, funcs, ret)
                if ret == 1 or ret == 2:
                    break
            else:
                ret = Evaluate(c['value'][2], vars, funcs, ret)
                if ret == 1 or ret == 2:
                    break
        elif c['type'] == 'while':
            while If(c, vars):
                preline = int(line)
                ret2 = Evaluate(c['value'][1], vars, funcs, 0)
                line = preline
                if ret2 == 1:
                    break
        elif c['type'] == 'for':
            if c['value'][0][0][0] != "UNKNOWN":
                raise(TypeError("newvar must be followed by a name not anything else"))
            if c['value'][0][1] != 'from' or c['value'][0][3] != 'to':
                raise(SyntaxError("Format for loops like this for _ from _ to _"))
            value = GetNumberValue(c['value'][0][2], vars, "Can't for loop with a string", "Can't for loop with a list")
            compare = GetNumberValue(c['value'][0][4], vars, "Can't for loop with a string", "Can't for loop with a list")
            vars.update({c['value'][0][0][1]:value})
            ret2 = 0
            for i in range(value, compare):
                vars[c['value'][0][0][1]] = i
                preline = int(line)
                ret2 = Evaluate(c['value'][1], vars, funcs, 0)
                line = preline
                if ret2 == 1:
                    break
            vars.pop(c['value'][0][0][1])
        elif c['type'] == 'ncall':
            if c['value'][0][0] != "UNKNOWN":
                raise(TypeError("Must be a name of a function"))
            if c['value'][0][1] not in funcs:
                raise(TypeError("Must be a name of a function"))
            if "argTypes" in funcs[c['value'][0][1]].keys():
                if len(funcs[c['value'][0][1]]['argTypes']) != len(c['value'][1]):
                    raise(SyntaxError("Function must have the args needed"))
                varsIn = []
                for i, val in enumerate(c['value'][1]):
                    value = GetValueAll(val, vars)
                    valueType = str(type(value)) 
                    if valueType[8:len(valueType)-2] != funcs[c['value'][0][1]]['argTypes'][i]:
                        raise(TypeError(f"{value} is not of type {funcs[c['value'][0][1]]['argTypes'][i]}, which is needed!"))
                    varsIn.append(value)
                funcs[c['value'][0][1]]['content'](varsIn)
                continue
            elif len(c['value'][1]) != len(funcs[c['value'][0][1]]['params']):
                raise(SyntaxError("Function must have the args needed"))
            newvars = vars.copy()
            for v, fv in zip(c['value'][1], funcs[c['value'][0][1]]['params']):
                value = GetValueAll(v, vars)
                newvars.update({fv[1]:value})
            Evaluate(funcs[c['value'][0][1]]['contents'], newvars, funcs)
        elif c['type'] == 'rcall':
            if c['value'][2][0] == "UNKNOWN":
                if c['value'][2][1] not in vars:
                    vars.update({c['value'][2][1]:None})
            IsVariable(c['value'][2], vars, "Cannot save output to a non variable")
            if c['value'][0][0] != "UNKNOWN":
                raise(TypeError("Must be a name of a function"))
            if c['value'][0][1] not in funcs:
                raise(TypeError("Must be a name of a function"))
            if "argTypes" in funcs[c['value'][0][1]].keys():
                if len(funcs[c['value'][0][1]]['argTypes']) != len(c['value'][1]):
                    raise(SyntaxError("Function must have the args needed"))
                varsIn = []
                for i, val in enumerate(c['value'][1]):
                    value = GetValueAll(val, vars)
                    valueType = str(type(value)) 
                    if valueType[8:len(valueType)-2] != funcs[c['value'][0][1]]['argTypes'][i]:
                        raise(TypeError(f"{value} is not of type {funcs[c['value'][0][1]]['argTypes'][i]}, which is needed!"))
                    varsIn.append(value)
                ret2 = funcs[c['value'][0][1]]['content'](varsIn)
                if ret2 == None:
                    raise(SyntaxError(f"{line} rcall are only used for functions that return!"))
                vars[c['value'][2][1]] = ret2
                continue
            elif len(c['value'][1]) != len(funcs[c['value'][0][1]]['params']):
                raise(SyntaxError("Function must have the args needed"))

            newvars = vars.copy()
            for v, fv in zip(c['value'][1], funcs[c['value'][0][1]]['params']):
                value = GetValueAll(v, vars)
                newvars.update({fv[1]:value})
            ret2 = Evaluate(funcs[c['value'][0][1]]['contents'], newvars, funcs)
            if ret2 == None:
                raise(SyntaxError(f"{line} rcall are only used for functions that return!"))
            vars[c['value'][2][1]] = ret2
        elif c['type'] == 'return':
            value = GetValueAll(c['value'][0], vars)         
            ret = value
            break
        elif c['type'] == 'run':
            with open(f'{c["value"][0][1]}.wabs', 'r') as file:
                if f'{c["value"][0][1]}.wabs' in filesrunning:
                    raise(ImportError("Can't run a script that is already running"))
                filesrunning.append(f'{c["value"][0][1]}.wabl')
                tokens, error = Lex(file.read() + '\n')
                if error is False:
                    compr2, error = CompressTogether(tokens)
                    if error is False:
                        newvars2, newfuncs2 = Evaluate(compr2, {}, {}, 'VARS/FUNCS')
                        for k, va in newvars2.items():
                            v = {f"{c['value'][0][1]}.{k}": va}
                            vars.update(v)
                        for k, va in newfuncs2.items():
                            f = {f"{c['value'][0][1]}.{k}": va}
                            funcs.update(f)
        elif c['type'] == 'opento':
            VariableNotAListOrDict(c['value'][1], vars, "Can't save a file contents to a non variable", "Can't save a file contents to list (string is indexable like a list anyways)", "Can't save file to a dict")
            with open(c['value'][0][1], 'r') as file:
                vars[c['value'][1][1]] = file.read()
        elif c['type'] == 'break' and ret == 0:
            ret = 1
            break
        elif c['type'] == 'continue' and ret == 0:
            ret = 2
            break
        elif c['type'] == 'lengthto':
            if c['value'][1][0] == "UNKNOWN":
                if c['value'][1][1] not in vars:
                    vars.update({c['value'][1][1]:None})
            if c['value'][0][0] != "UNKNOWN":
                raise(TypeError("can't index something that isn't a list"))
            if c['value'][0][1] not in vars:
                raise(KeyError(f"{c['value'][0][1]} doesn't exist"))
            if isinstance(vars[c['value'][0][1]], list) is False and isinstance(vars[c['value'][0][1]], str) is False:
                raise(TypeError("can't get the length from a normal var"))
            VariableNotAListOrDict(c['value'][1], vars, "Can't save a length of a list to a non variable", "Can't save a length of a list to a list", "Can't save length of list to a list")
            vars[c['value'][1][1]] = len(vars[c['value'][0][1]])
        elif c['type'] == 'nlprint':
            value = GetValueAll(c['value'][0], vars)
            if isinstance(value, bool):
                print(f"{value}".lower(), end='')
            else:
                print(value, end='')
        elif c['type'] == 'tostr':
            VariableNotAListOrDict(c['value'][0], vars, "Can't convert a non variable to a string", "Can't convert list to string", "Can't convert dict to string")
            value = GetValueAll(c['value'][0], vars)
            vars[c['value'][0][1]] = str(value)
        elif c['type'] == 'toint':
            VariableNotAListOrDict(c['value'][0], vars, "Can't convert a non variable to a int", "Can't convert list to int", "Can't convert dict to int")
            value = GetValueAll(c['value'][0], vars)
            try:
                vars[c['value'][0][1]] = int(value)
            except ValueError:
                print("Can't convert a non int string to an int")
        elif c['type'] == 'writeto':
            value = GetValueAll(c['value'][0], vars)
            with open(c['value'][1][1], 'w') as file:
                file.write(str(value))
        elif c['type'] == 'update':
            VariableIsDict(c['value'][0], vars, "Must be an active variable", "Can't update a key value pair in a non dictionary")
            dictionary = GetValueAll(c['value'][1], vars)
            vars[c['value'][0][1]].update(dictionary)
        elif c['type'] == 'access':
            if c['value'][0][0] == "UNKNOWN":
                if c['value'][0][1] not in vars:
                    vars.update({c['value'][0][1]:None})
            IsVariable(c['value'][0], vars, "Can't access a non variable")
            VariableIsDict(c['value'][1], vars, "Can't access a non variable", "Can't access a non dict")
            key = GetValueAll(c['value'][2], vars)
            if key not in vars[c['value'][1][1]]:
                raise(KeyError(f"{key} doesn't exist in the dictionary {c['value'][1][1]}"))
            vars[c['value'][0][1]] = vars[c['value'][1][1]][key]
        elif c['type'] == 'getkeys':
            if c['value'][0][0] == "UNKNOWN":
                if c['value'][0][1] not in vars:
                    vars.update({c['value'][1][1]:None})
            VariableIsList(c['value'][0], vars, "Can't access a non variable", "Can't store list of keys to a non list")
            VariableIsDict(c['value'][1], vars, "Can't access a non variable", "Can't access keys of a non dict")
            vars[c['value'][0][1]] = list(vars[c['value'][1][1]].keys)
        elif c['type'] == "getvalues":
            if c['value'][0][0] == "UNKNOWN":
                if c['value'][0][1] not in vars:
                    vars.update({c['value'][1][1]:None})
            VariableIsList(c['value'][0], vars, "Can't access a non variable", "Can't store list of values to a non list")
            VariableIsDict(c['value'][1], vars, "Can't access a non variable", "Can't access values of a non dict")
            vars[c['value'][0][1]] = list(vars[c['value'][1][1]].values)
        elif c['type'] == "remove":
            VariableIsDict(c['value'][0], vars, "Can't from a remove a non variable", "Can't remove from a non dict")
            key = GetValueAll(c['value'][1], vars)
            if key not in vars[c['value'][0][1]]:
                raise(KeyError(f"{key} doesn't exist in the dictionary {c['value'][0][1]}"))
            vars[c['value'][0][1]].pop(key)
        elif c['type'] == "import":
            if c['value'][0][0] != "UNKNOWN":
                raise(SyntaxError("Can't import a non name"))
            vs, fcs = CreateModuleDefs(c['value'][0][1])
            vars.update(vs)
            funcs.update(fcs)
    if ret == 'VARS/FUNCS':
        return (vars, funcs)
    return (ret) 

def CreateModuleDefs(module):
    vars = {}
    funcs = {}
    if os.path.isdir(f"Modules/{module}") is False:
        raise(ModuleNotFoundError(f"Module {module} not found!"))
    with open(f"Modules/{module}/setup.wptl", "r") as file:
        text = file.read().replace(" ", "").split("\n")
        currentModule = None
        for line in text:
            parts = line.split("->")
            if parts[0] == "ref":
                if parts[1][len(parts[1])-3:] == ".py":
                    currentModule = importCustomModule(module, parts[1].removesuffix(".py"))
            elif parts[0] == "func":
                name, args = parts[1].split("|")
                func = currentModule.__getattribute__(parts[2])
                if module == "Builtins":
                    if len(args) == 0:
                        funcs.update({name:{"argTypes": [], "content":func}})
                    else:
                        funcs.update({name:{"argTypes": args.split(","), "content":func}})
                else:
                    if len(args) == 0:
                        funcs.update({module+"."+name:{"argTypes": [], "content":func}})
                    else:
                        funcs.update({module+"."+name:{"argTypes": args.split(","), "content":func}})
    return (vars, funcs)

def importCustomModule(directoryName, moduleName):
    spec = importlib.util.spec_from_file_location(moduleName, os.curdir + f"/Modules/{directoryName}/{moduleName}.py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return foo

with open('main.wabs', 'r') as file:
    filesrunning.append('main.wabs')
    tokens, error = Lex(file.read() + '\n')
    if error is False:
        compr, error = CompressTogether(tokens)
        if error is False:
            vs, fncs = CreateModuleDefs("Builtins")
            Evaluate(compr, vs, fncs)