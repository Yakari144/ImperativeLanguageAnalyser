from lark import Lark,Token,Tree
from lark.visitors import Interpreter
from lark import Discard

## Primeiro precisamos da GIC
grammar = r'''
//Regras Sintaticas
start: componente*
componente: declaracao | funcao | COMENTARIO | instrucao 
declaracao: tipo ID ( "=" (elemcomp|exp) )? PVIR
funcao: DEF tipo ID "(" params? ")" corpofunc
instrucao : atribuicao PVIR
        | leitura PVIR
        | escrita PVIR
        | selecao
        | repeticao
tipo : INT
    | BOOLEAN
    | STRING
    | ARRAY
    | TUPLO
    | LISTA
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
corpofunc: "{" (componente|retorno)* "}"
atribuicao: ID "=" (exp|elemcomp)
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
    | array
    | tuplo
    | lista
    | bool
array : "[" (elemcomp (VIR elemcomp)*)? "]"
tuplo : "(" elemcomp (VIR elemcomp)+ ")"
lista : elemcomp "->" elemcomp
bool : "True" | "False"
//
//
//Regras Lexicográficas
//
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
    
    def pushFunc(self,func):
        self.funcStack.append(func)
    
    def popFunc(self):
        self.funcStack.pop()

    def inFuncao(self):
        return self.funcAct() != None

    def __init__(self):
        self.variaveis = {}
        # create a stack to store the current function
        self.funcStack = []

    def start(self,tree):
        self.variaveis['GLOBAL'] = []
        # inicio do programa
        self.visit_children(tree)
        # fim do programa
        print("Variaveis:")
        for x in self.variaveis.keys():
            print("\t"+x)
            for y in self.variaveis[x]:
                print("\t\t"+y['nome']+" : "+y['tipo'])

    def componente(self,tree):
        self.visit_children(tree)
        
    def declaracao(self,tree):
        for elemento in tree.children:
            # simbolo nao terminal
            if (type(elemento)==Tree):
                # nao terminal 'tipo' na gramatica
                if( elemento.data == 'tipo'):
                    # obter o valor do nao terminal (return da funcao "tipo(self,tree)")
                    t = self.visit(elemento)
            else:
                # simbolo terminal 'ID' na gramatica
                if (elemento.type=='ID'):
                    # obter o valor do terminal
                    id = elemento.value
        # print("Elementos visitados")
        # se nao existir a variavel na lista de variaveis globais
        if id not in [x['nome'] for x in self.variaveis['GLOBAL']]:
            # se estivermos numa funcao
            if self.inFuncao():
                # se a funcao nao existir na lista de variaveis
                if self.funcAct() not in self.variaveis.keys():
                    # criar a funcao na lista de variaveis
                    self.variaveis[self.funcAct()] = []
                # se a variavel nao existir na lista de variaveis da funcao
                if id not in [x['nome'] for x in self.variaveis[self.funcAct()]]:
                    # adicionar a variavel à lista de variaveis da funcao
                    self.variaveis[self.funcAct()].append({'nome':id,'tipo':t,'usada':False})
                # se a variavel ja existir na lista de variaveis da funcao
                else:
                    print("Variavel "+id+" já declarada")
            # se nao estivermos numa funcao
            else:
                # adicionar a variavel à lista de variaveis globais
                self.variaveis['GLOBAL'].append({'nome':id,'tipo':t,'usada':False})
        # se a variavel ja existir na lista de variaveis globais
        else:
            print("Variavel "+id+" já declarada")
            return

    def funcao(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    self.pushFunc(elemento.value)
        self.popFunc()
    
    def instrucao(self,tree):
        self.visit_children(tree)

    def tipo(self,tree):
        for elemento in tree.children:
            return elemento.value

    def exp(self,tree):
        return self.visit_children(tree)

    def op(self,tree):
        pass

    def oplist(self,tree):
        pass

    def params(self,tree):
        return self.visit_children(tree)

    def param(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if( elemento.data == 'tipo'):
                    t = self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
        #print("Elementos visitados, vou regressar à main()")
        if id not in [x['nome'] for x in self.variaveis['GLOBAL']]:
            if self.inFuncao():
                if self.funcAct() not in self.variaveis.keys():
                    self.variaveis[self.funcAct()] = []
                if id not in [x['nome'] for x in self.variaveis[self.funcAct()]]:
                    self.variaveis[self.funcAct()].append({'nome':id,'tipo':t,'usada':False})
                else:
                    print("Variavel "+id+" já declarada")
            else:
                self.variaveis['GLOBAL'].append({'nome':id,'tipo':t,'usada':False})
        else:
            print("Variavel "+id+" já declarada")
            return

    def corpofunc(self,tree):
        self.visit_children(tree)

    def atribuicao(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                atr = self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
        if id not in [x['nome'] for x in self.variaveis['GLOBAL']]:
            if self.inFuncao():
                if self.funcAct() not in self.variaveis.keys():
                    print("Variavel "+id+" não declarada")
                elif id not in [x['nome'] for x in self.variaveis[self.funcAct()]]:
                    print("Variavel "+id+" não declarada")
            else:
                print("Variavel "+id+" não declarada")

    def leitura(self,tree):
        pass

    def escrita(self,tree):
        pass

    def ficheiro(self,tree):
        pass

    def selecao(self,tree):
        pass

    def repeticao(self,tree):
        pass

    def retorno(self,tree):
        pass

    def comp(self,tree):
        pass

    def sinalcomp(self,tree):
        pass

    def casos(self,tree):
        pass

    def interv(self,tree):
        pass

    def elemcomp(self,tree):
        return self.visit_children(tree)

    def array(self,tree):
        pass

    def tuplo(self,tree):
        pass

    def lista(self,tree):
        pass



    # simbolos terminais
    def ID(self,tree):
        pass

    def COMENTARIO(self,tree):
        pass

    def PVIR(self,tree):
        pass

    def DEF(self,tree):
        pass

    def INT(self,tree):
        pass

    def BOOLEAN(self,tree):
        pass

    def STRING(self,tree):
        pass

    def ARRAY(self,tree):
        pass

    def TUPLO(self,tree):
        pass

    def LISTA(self,tree):
        pass

    def NUM(self,tree):
        pass

    def ADD(self,tree):
        pass

    def SUB(self,tree):
        pass

    def DIV(self,tree):
        pass

    def MULT(self,tree):
        pass

    def EXPO(self,tree):
        pass

    def PERC(self,tree):
        pass

    def CONS(self,tree):
        pass

    def SNOC(self,tree):
        pass

    def IN(self,tree):
        pass

    def HEAD(self,tree):
        pass

    def TAIL(self,tree):
        pass

    def VIR(self,tree):
        pass

    def LER(self,tree):
        pass

    def ESCREVER(self,tree):
        pass

    def SE(self,tree):
        pass

    def CASO(self,tree):
        pass

    def ENQ(self,tree):
        pass

    def FAZER(self,tree):
        pass

    def END(self,tree):
        pass

    def REPETIR(self,tree):
        pass

    def ATE(self,tree):
        pass

    def PARA(self,tree):
        pass

    def RET(self,tree):
        pass

    def EQ(self,tree):
        pass

    def GE(self,tree):
        pass

    def LE(self,tree):
        pass

    def DIF(self,tree):
        pass

    def LESS(self,tree):
        pass

    def G(self,tree):
        pass

    def STR(self,tree):
        pass

f = open('linguagem.txt', 'r')
frase = f.read()
f.close()

p = Lark(grammar) 
tree = p.parse(frase)
data = MyInterpreter().visit(tree)
