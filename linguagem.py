from lark import Lark, Token, Tree
from lark.visitors import Interpreter
from lark import Discard

# Primeiro precisamos da GIC
grammar = r'''
//Regras Sintaticas
start: componentes
componentes: (componente|deffuncao)*
componente: declaracao | COMENTARIO | instrucao 
declaracao: tipo ID ( "=" ecomp )? PVIR    
deffuncao: DEF tipo ID "(" params? ")" corpofunc
funcao: ID "(" (ecomp("," ecomp)*)? ")"
instrucao : atribuicao PVIR
        | leitura PVIR
        | escrita PVIR
        | selecao
        | repeticao
        | funcao PVIR
tipo : INT
    | BOOLEAN
    | STRING
    | ARRAY
    | TUPLO
    | LISTA
ecomp: exp|elemcomp
exp: NUM op NUM
    | ID "[" NUM "]"
    | ID "." oplist
    | ID "." ID
op :  ADD
    | SUB
    | DIV
    | MULT
    | EXPO
    | PERC
oplist : CONS
    | SNOC
    | IN
    | HEAD
    | TAIL
params: param (VIR param)*
param: tipo ID
corpofunc: "{" (componentes|deffuncao|retorno)* "}"
atribuicao: ID "=" (ecomp)
leitura: LER "(" ficheiro "," ID ")"
escrita: ESCREVER "(" ficheiro "," ID ")"
ficheiro: ID ("." ID)?
selecao: SE comp "{" componente* "}"
        | CASO ID caso+ END
repeticao: ENQ comp FAZER componente+ END
        | REPETIR componente+ ATE comp END
        | PARA interv FAZER componente+ END
retorno: RET elemcomp PVIR
comp: elemcomp sinalcomp elemcomp
    | "!" ID
sinalcomp: EQ
    | GE
    | LE
    | DIF
    | LESS
    | G
caso: elemcomp ":" "{" componente+ "}"
interv: "[" NUM "," NUM "]"
elemcomp: ID
    | NUM
    | STR
    | funcao
    | array
    | tuplo
    | lista
    | bool
array : "[" (elemcomp (VIR elemcomp)*)? "]"
tuplo : "(" elemcomp (VIR elemcomp)+ ")"
lista : elemcomp "->" elemcomp
bool : TRUE | FALSE
//
//
//Regras Lexicográficas
//
TRUE: "True"
FALSE: "False"
ID: "a".."z"("a".."z"|"A".."Z"|"_"|"0".."9")*
COMENTARIO: /\/\*(.|\n)*?\*\//
PVIR : ";"
DEF:"def"
INT:"int"
BOOLEAN: "bool"
STRING: "string"
ARRAY: "array"
TUPLO: "tuplo"
LISTA: "lista"
NUM : "0".."9"+
ADD : "+"
SUB : "-"
DIV : "/"
MULT: "*"
EXPO: "^"
PERC: "%"
CONS : "cons"
SNOC : "snoc"
IN : "in"
HEAD : "head"
TAIL : "tail"
VIR: ","
LER: "ler"
ESCREVER: "escrever"
SE: "se"
CASO: "caso"
ENQ: "enquanto"
FAZER: "fazer"
END: "end"
REPETIR: "repetir"
ATE: "ate"
PARA: "para"
RET: "devolve"
EQ : "=="
GE : ">="|"=>"
LE : "<="|"=<"
DIF : "!="
LESS : "<"
G : ">"
STR: /"(\\\"|[^"])*"/
//Tratamento dos espaços em branco
%import common.WS
%ignore WS
'''


# definir o transformer


class MyInterpreter(Interpreter):
    def funcAct(self):
        if len(self.funcStack) > 0:
            return self.funcStack[-1]
        else:
            return None

    def pushFunc(self, func):
        self.funcStack.append(func)


    def popFunc(self):
        self.funcStack.pop()

    def inFuncao(self):
        return self.funcAct() != None

    def checkDecl(self,id):
        if id in [x['nome'] for x in self.variaveis['GLOBAL']]:
            return True
        elif self.inFuncao() and id in [x['nome'] for x in self.variaveis[self.funcAct()]]:
            return True
        else:
            return False

    def htmlInit(self):
        self.HTML += ''' 
        <!DOCTYPE html>
        <html>
        <style>
            .error {
                position: relative;
                display: inline-block;
                border-bottom: 1px dotted black;
                color: red;
            }
            
            .code {
                position: relative;
                display: inline-block;
            }
            
            .error .errortext {
                visibility: hidden;
                width: 200px;
                background-color: #555;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 5px 0;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                margin-left: -40px;
                opacity: 0;
                transition: opacity 0.3s;
            }

            .error .errortext::after {
                content: "";
                position: absolute;
                top: 100%;
                left: 20%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #555 transparent transparent transparent;
            }

            .error:hover .errortext {
                visibility: visible;
                opacity: 1;
            }
        </style>
        <body>
            <h2>Análise de código</h2>
            <pre><code>
        '''
    
    def htmlEnd(self):
        self.HTML += '''
            </code></pre>
        </body>
        </html>
        '''
    
    def writeHTML(self):
        f = open("output.html", "w")
        f.write(self.HTML)

    def htmlInit(self):
        self.HTML += ''' 
        <!DOCTYPE html>
        <html>
        <style>
            .error {
                position: relative;
                display: inline-block;
                border-bottom: 1px dotted black;
                color: red;
            }
            
            .code {
                position: relative;
                display: inline-block;
            }
            
            .error .errortext {
                visibility: hidden;
                width: 200px;
                background-color: #555;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 5px 0;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                margin-left: -40px;
                opacity: 0;
                transition: opacity 0.3s;
            }

            .error .errortext::after {
                content: "";
                position: absolute;
                top: 100%;
                left: 20%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #555 transparent transparent transparent;
            }

            .error:hover .errortext {
                visibility: visible;
                opacity: 1;
            }
        </style>
        <body>
            <h2>Análise de código</h2>
            <pre><code>
        '''
    
    def htmlEnd(self):
        self.HTML += '''
            </code></pre>
        </body>
        </html>
        '''
    
    def writeHTML(self):
        f = open("output.html", "w")
        f.write(self.HTML)

    def __init__(self):
        self.variaveis = {}
        # create a stack to store the current function
        self.funcStack = []
        self.instructions = {}
        self.HTML = ""

    def start(self, tree):
        self.variaveis['GLOBAL'] = []
        # inicio do programa
        self.htmlInit()
        self.HTML += "<br>"
        self.visit_children(tree)
        self.htmlEnd()
        self.writeHTML()
        # fim do programa
        print("Variaveis:")
        for x in self.variaveis.keys():
            print("\t"+x)
            for y in self.variaveis[x]:
                print("\t\t"+y['nome']+" : "+y['tipo'] + " : " + str(y['usada']))
        
        #for x in self.instructions.keys():
        #    print("Instrucao "+ x + " : " + str(self.instructions[x]))
    
    def componentes(self, tree):
        self.visit_children(tree)
    
    def componente(self, tree):
        for elemento in tree.children:
            if(type(elemento) == Tree):
                self.visit(elemento)
            else:
                if (elemento.type=='COMENTARIO'):
                    comentario = elemento.value
                    self.HTML += "<span class='code'> "+comentario+" </span> <br>"
            
    def declaracao(self, tree):
        for elemento in tree.children:
            # simbolo nao terminal
            if (type(elemento)==Tree):
                # nao terminal 'tipo' na gramatica
                if( elemento.data == 'tipo'):
                    # obter o valor do nao terminal (return da funcao "tipo(self,tree)")
                    t = self.visit(elemento)
                    self.HTML += "<span class='code'> "+t+" </span>"
                else :
                    if (elemento.data == 'ecomp'):
                        if 'atribuicao' not in self.instructions.keys():
                            self.instructions['atribuicao'] = 1
                        else:
                            self.instructions['atribuicao'] += 1
                        self.HTML += "<span class='code'> = </span>"
                    self.visit(elemento)
            else:
                # simbolo terminal 'ID' na gramatica
                if (elemento.type=='ID'):
                    # obter o valor do terminal
                    id = elemento.value
                    self.HTML += "<span class='code'> "+id+" </span>"
                elif (elemento.type=='PVIR'):
                    self.HTML += "<span class='code'>;</span> <br>"
                    
                    
        # print("Elementos visitados")
        # se a variavel esta declarada no contexto atual
        if self.checkDecl(id):
            print("Variavel "+id+" ja declarada") 
        # se a variavel nao esta declarada no contexto atual
        else:
            # se a funcao atual for nula, estamos no contexto global
            if self.funcAct() == None:
                self.variaveis['GLOBAL'].append({'nome':id,'tipo':t,'usada':False})
            # se a funcao atual nao for nula, estamos no contexto de uma funcao
            else:
                self.variaveis[self.funcAct()].append({'nome':id,'tipo':t,'usada':False})

    def deffuncao(self,tree):
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'tipo'):
                    t = self.visit(elemento)
                    self.HTML += "<span class='code'> " + t + " </span>"
                
                elif (elemento.data == 'params'):
                    t = self.visit(elemento)
                
                elif (elemento.data == 'corpofunc'):
                    t = self.visit(elemento)
                    
            else:
                if (elemento.type == 'ID'):
                    self.pushFunc(elemento.value)
                    t = elemento.value
                    self.HTML += "<span class='code'> " + t + " ( </span>"
                    
                elif (elemento.type == 'DEF'):
                    t = elemento.value
                    self.HTML += "<span class='code'> " + t + " </span>"
        self.popFunc()

    def instrucao(self, tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if elemento.data not in self.instructions.keys():
                    self.instructions[elemento.data] = 1
                else :
                    self.instructions[elemento.data] += 1
                self.visit(elemento)
            else:
                if (elemento.type == 'PVIR'):
                    self.HTML += "<span class='code'> ; </span> <br>"



    def tipo(self, tree):
        for elemento in tree.children:
            return elemento.value

    def ecomp(self,tree):
        self.visit_children(tree)

    def exp(self,tree):
        i = 0
        firstEntry = 0
        firstElement = ""
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if( elemento.data == 'op'):
                    # obter o valor do nao terminal (return da funcao "tipo(self,tree)")
                    t = self.visit(elemento)
                    self.HTML += "<span class='code'> "+t+" </span>"
                elif (elemento.data == 'oplist'):
                    t = self.visit(elemento)
                    self.HTML += "<span class='code'> "+t+" </span>"
            else:
                if (elemento.type=='ID'):
                    if (firstEntry == 0):
                        firstEntry = 1
                        firstElement = "ID"
                    else:
                        firstEntry = 2
                    
                    id = elemento.value
                        
                    if i == 0:
                        i+=1
                        if not self.checkDecl(id):
                            print("Variavel "+id+" não declarada")
                            self.HTML += "<span class='error'> "+id+"</span>"
                        else:
                            if self.inFuncao():
                                for x in self.variaveis[self.funcAct()]:
                                    if x['nome'] == id:
                                        x['usada'] = True
                            else:
                                for x in self.variaveis['GLOBAL']:
                                    if x['nome'] == id:
                                        x['usada'] = True
                            self.HTML += "<span class='code'> "+id+"</span>"
                    else:
                        self.HTML += "<span class='code'>."+id+"</span>"
                
                elif (elemento.type == 'NUM'):
                    if (firstEntry == 0):
                        firstEntry = 1
                        firstElement = "NUM"
                        
                    if firstElement == "NUM":
                        num = elemento.value
                        self.HTML += "<span class='code'> "+num+" </span>"
                    else:
                        num = elemento.value
                        self.HTML += "<span class='code'>[ "+num+" ]</span>"

    def op(self, tree):
        for elemento in tree.children:
            return elemento.value


    def oplist(self, tree):
        for elemento in tree.children:
            return elemento.value


    def params(self, tree):
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'param'):
                    self.visit(elemento)
            else:
                if (elemento.type == 'VIR'):
                    self.HTML += "<span class='code'>, </span>"

    def param(self, tree):
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'tipo'):
                    t = self.visit(elemento)
                    self.HTML += "<span class='code'> " + t + " </span>"
            else:
                if (elemento.type == 'ID'):
                    id = elemento.value
                    self.HTML += "<span class='code'> " + id + " </span>"
        # print("Elementos visitados, vou regressar à main()")
        # print("Elementos visitados, vou regressar à main()")
        if id not in [x['nome'] for x in self.variaveis['GLOBAL']]:
            if self.inFuncao():
                if self.funcAct() not in self.variaveis.keys():
                    self.variaveis[self.funcAct()] = []
                if id not in [x['nome'] for x in self.variaveis[self.funcAct()]]:
                    self.variaveis[self.funcAct()].append(
                        {'nome': id, 'tipo': t, 'usada': False})
                    self.variaveis[self.funcAct()].append(
                        {'nome': id, 'tipo': t, 'usada': False})
                else:
                    print("Variavel "+id+" já declarada")
            else:
                self.variaveis['GLOBAL'].append(
                    {'nome': id, 'tipo': t, 'usada': False})
                self.variaveis['GLOBAL'].append(
                    {'nome': id, 'tipo': t, 'usada': False})
        else:
            print("Variavel "+id+" já declarada")
            return


    def corpofunc(self, tree):
        self.HTML += "<span class='code'> ) </span> <br> <span class='code'> { </span> <br>"
        self.visit_children(tree)


    def atribuicao(self, tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if (elemento.type == 'ID'):
                    id = elemento.value
                    self.HTML += "<span class='code'> " + id + " = </span>"
        if id not in [x['nome'] for x in self.variaveis['GLOBAL']]:
            if self.inFuncao():
                if self.funcAct() not in self.variaveis.keys():
                    print("Variavel "+id+" não declarada")
                elif id not in [x['nome'] for x in self.variaveis[self.funcAct()]]:
                    print("Variavel "+id+" não declarada")
            else:
                print("Variavel "+id+" não declarada")

    def leitura(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
                        print("Variavel "+id+" não declarada")
                    
    def escrita(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
                        print("Variavel "+id+" não declarada")

    def ficheiro(self, tree):
        pass

    def selecao(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
                        print("Variavel "+id+" não declarada")


    def repeticao(self, tree):
        self.visit_children(tree)



    def retorno(self, tree):
        self.visit_children(tree)

    def comp(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
                        print("Variavel "+id+" não declarada")


    def sinalcomp(self, tree):
        pass

    def caso(self,tree):
        self.visit_children(tree)


    def interv(self, tree):
        first = True
        self.HTML += "<span class='code'> [ </span>"
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if(elemento.type=='NUM'):
                    if first:
                        first = False
                    else:
                        self.HTML += "<span class='code'>, </span>"
                    self.HTML += "<span class='code'> " + elemento.value + " </span>"
        self.HTML += "<span class='code'> ] </span>"
        
    def elemcomp(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
                        print("Variavel "+id+" não declarada")
                        self.HTML += "<span class='error'> " + id + " </span>"
                    else:
                        if self.inFuncao():
                            for x in self.variaveis[self.funcAct()]:
                                if x['nome'] == id:
                                    x['usada'] = True
                        else:
                            for x in self.variaveis['GLOBAL']:
                                if x['nome'] == id:
                                    x['usada'] = True
                        self.HTML += "<span class='code'> " + id + " </span>"
                elif (elemento.type=='NUM'):
                    num = elemento.value
                    self.HTML += "<span class='code'> " + num + " </span>"
                elif (elemento.type == 'STR'):
                    t = elemento.value
                    self.HTML += "<span class='code'> " + t + " </span>"
                
    def funcao(self,tree):
        first = True;
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (first):
                    self.visit(elemento)
                    first = False
                else:
                    self.HTML += "<span class='code'>, </span>"
                    self.visit(elemento)
            else: 
                if (elemento.type == 'ID'):
                    id = elemento.value
                    self.HTML += "<span class='code'> " + id + " ( </span>"
        self.HTML += "<span class='code'> ) </span>" 
        
    def array(self,tree):
        self.HTML += "<span class='code'> [ </span>"
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else :
                if (elemento.type=='VIR'):
                    num = elemento.value
                    self.HTML += "<span class='code'>, </span>"
        self.HTML += "<span class='code'> ] </span>"
        

    def tuplo(self,tree):
        self.HTML += "<span class='code'> ( </span>"
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else :
                if (elemento.type=='VIR'):
                    num = elemento.value
                    self.HTML += "<span class='code'>, </span>"
        self.HTML += "<span class='code'> ) </span>"

    def lista(self,tree):
        first = True
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
                if first:
                    self.HTML += "<span class='code'> -> </span>"
                    first = False

    def bool(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if(elemento.type == 'TRUE'):
                    self.HTML += "<span class='code'> true </span>"
                elif (elemento.type == 'FALSE'):
                    self.HTML += "<span class='code'> false </span>"
        

    # simbolos terminais
    def TRUE(self, tree):
        return tree.value
    
    def FALSE(self, tree):
        return tree.value
    
    def ID(self,tree):
        return tree.value

    def COMENTARIO(self, tree):
        return tree.value

    def PVIR(self, tree):
        pass

    def DEF(self, tree):
        pass

    def INT(self, tree):
        pass

    def BOOLEAN(self, tree):
        pass

    def STRING(self, tree):
        pass

    def ARRAY(self, tree):
        pass

    def TUPLO(self, tree):
        pass

    def LISTA(self, tree):
        pass

    def NUM(self, tree):
        pass

    def ADD(self, tree):
        return tree.value

    def SUB(self, tree):
        return tree.value

    def DIV(self, tree):
        return tree.value

    def MULT(self, tree):
        return tree.value

    def EXPO(self, tree):
        return tree.value

    def PERC(self, tree):
        return tree.value

    def CONS(self, tree):
        pass

    def SNOC(self, tree):
        pass


    def IN(self, tree):
        pass

    def HEAD(self, tree):
        pass

    def TAIL(self, tree):
        pass

    def VIR(self, tree):
        pass

    def LER(self, tree):
        pass

    def ESCREVER(self, tree):
        pass

    def SE(self, tree):
        pass

    def CASO(self, tree):
        pass

    def ENQ(self, tree):
        pass

    def FAZER(self, tree):
        pass

    def END(self, tree):
        pass

    def REPETIR(self, tree):
        pass

    def ATE(self, tree):
        pass

    def PARA(self, tree):
        pass

    def RET(self, tree):
        pass

    def EQ(self, tree):
        pass

    def GE(self, tree):
        pass

    def LE(self, tree):
        pass

    def DIF(self, tree):
        pass

    def LESS(self, tree):
        pass

    def G(self, tree):
        pass

    def STR(self, tree):
        pass



f = open('linguagem.txt', 'r')
frase = f.read()
f.close()

p = Lark(grammar)
p = Lark(grammar)
tree = p.parse(frase)
data = MyInterpreter().visit(tree)
