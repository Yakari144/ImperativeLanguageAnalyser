from lark import Lark
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
    def __init__(self):
        self.variaveis = {}
        self.inFuncao = False

    def start(self,tree):
        pass

    def componente(self,tree):
        pass

    def declaracao(self,tree):
        #print("Entrei na Raiz, vou visitar os Elementos")
        for e in tree.children:
            r = self.visit(e)
        #print("Elementos visitados, vou regressar à main()")
        if self.inFuncao:
            pass

    def funcao(self,tree):
        pass

    def instrucao(self,tree):
        pass

    def tipo(self,tree):
        pass

    def exp(self,tree):
        pass

    def op(self,tree):
        pass

    def oplist(self,tree):
        pass

    def params(self,tree):
        pass

    def param(self,tree):
        pass

    def corpo(self,tree):
        pass

    def atribuicao(self,tree):
        pass

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
        pass

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
