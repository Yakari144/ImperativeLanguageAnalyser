from lark import Lark, Token, Tree
from lark.visitors import Interpreter
from lark import Discard
from bs4 import BeautifulSoup
import json

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
corpofunc: "{" (componente|deffuncao|retorno)* "}"
atribuicao: ID "=" (ecomp)
leitura: LER "(" ficheiro "," ID ")"
escrita: ESCREVER "(" ficheiro "," ID ")"
ficheiro: ID ("." ID)?
selecao: SE comp "{" (declaracao|COMENTARIO|instrucao)* "}"
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
####################################################
################# Auxiliar methods #################
####################################################

    def funcAct(self):
        if len(self.funcStack) > 0:
            return self.funcStack[-1]
        else:
            return None

    def pushFunc(self, func):
        self.funcStack.append(func)

    def getTabFunc(self):
        # get the number of functions in the stack
        n = len(self.funcStack)
        return "\t" * n

    def popFunc(self):
        self.funcStack.pop()

    def inFuncao(self):
        return self.funcAct() != None

    def ecAct(self):
        if len(self.ecStack) > 0:
            return self.ecStack[-1]
        else:
            return None

    def countSelecao(self,d, func):
        if len(d.keys()) == 0:
            return 0
        else:
            r=0
            for x in d.keys():
                r += self.countSelecao(d[x], func)
                if func in x:
                    r += 1
            return r

    def pushEc(self, func):
        name = func+str(self.countSelecao(self.eC, func)+1)
        self.setEcVal(self.eC, self.ecStack, name )
        self.ecStack.append(name)

    def getTabEc(self):
        # get the number of functions in the stack
        n = len(self.ecStack)
        return "\t" * n

    def popEc(self):
        self.ecStack.pop()

    def getEcVal(self,d, keys):
        if len(keys) == 1:
            return d[keys[0]]
        else:
            return self.getEcVal(d[keys[0]], keys[1:])

    def setEcVal(self,d, keys, value):
        if len(keys) == 0:
            d[value]= {}
        else:
            self.setEcVal(d[keys[0]], keys[1:], value)

    def inEc(self):
        return self.ecAct() != None

    def getTab(self):
        return self.getTabFunc() + self.getTabEc()

    def checkDecl(self,id):
        if id in [x['nome'] for x in self.variaveis['GLOBAL']]:
            return True
        elif self.inFuncao() and id in [x['nome'] for x in self.variaveis[self.funcAct()]]:
            return True
        else:
            return False

    def setVar(self,nome,v):
        f = self.funcAct()
        if f == None:
            f='GLOBAL'
        self.variaveis[f][[x['nome'] for x in self.variaveis[f]].index(nome)] = v

    def setVar(self,nome,atr,valor):
        f = self.funcAct()
        if f == None:
            f='GLOBAL'
        self.variaveis[f][[x['nome'] for x in self.variaveis[f]].index(nome)][atr] = valor

    def printVars(self):
        print("Variaveis:")
        # get the lenght of the longest variable name
        maxnome = max([len(x['nome']) for x in self.variaveis['GLOBAL']])
        # get the lenght of the longest variable name
        maxtipo = max([len(x['tipo']) for x in self.variaveis['GLOBAL']])
        for x in self.variaveis.keys():
            print("\t"+x)
            for y in self.variaveis[x]:
                # string com o numero de espacos necessarios para alinhar as variaveis
                s1 =  " "*(maxnome-len(y['nome']))
                # string com o numero de espacos necessarios para alinhar os tipos
                s2 =  " "*(maxtipo-len(y['tipo']))
                s = "\t\t"+y['nome']+s1+" : "+y['tipo']+s2+" : "+str(y['usada'])+" : "+str(y['atribuicao'])+" :"
                print(s)
    
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
        f.close()

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
                color: black;
            }
            
            .funcName{
                position: relative;
                display: inline-block;
                color: #5C2397;
            }
            
            .def {
                position: relative;
                display: inline-block;
                color: #6c99bb
            }
            
            .ciclo {
                position: relative;
                display: inline-block;
                color: #CB692B;
            }
            
            .retornos {
                position: relative;
                display: inline-block;
                color: #A49A50;
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
            
            .graficos {
                background-color: #E6E4E3;   
            }
            
            .redeclaracao {
                position: relative;
                display: inline-block;
                border-bottom: 2px dotted black;
                color: red;
            }
            
            .naoDeclaracao {
                position: relative;
                display: inline-block;
                border-bottom: 2px dotted black;
                color: #F781D8;
            }
            
            .naoInicializada {
                position: relative;
                display: inline-block;
                border-bottom: 2px dotted black;
                color: #13590C;
            }
            
            .naoUsada {
                position: relative;
                display: inline-block;
                border-bottom: 2px dotted black;
                color: #818589;
            }
            
        </style>
        <body class="graficos">
            <h2 class="code">Análise de código</h2>
            <pre><code>
            <h3 class="code">Instruções de Análise - Variáveis</h3>
            <span class="redeclaracao">Cor -</span> <span class="code"> Redeclaração </span> <br> \n
            <span class="naoDeclaracao">Cor -</span> <span class="code"> Não-Declaração </span> <br> \n
            <span class="naoInicializada">Cor -</span> <span class="code"> Não-Inicializada </span> <br> \n
            <span class="naoUsada">Cor -</span> <span class="code"> Não-Utilizada </span> <br> \n
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

    
    def updateHTML(self):
        varsUnnused = []
        
        for x in self.variaveis.keys():
            for y in self.variaveis[x]:
                if y['usada'] == False:
                    if x == "GLOBAL":
                        varsUnnused.append("None-" + y['nome'])
                    else:
                        varsUnnused.append(x + "-" + y['nome'])
        
        for t in varsUnnused:
            print("Variável --> " + t + " não utilizada")
        
        soup = BeautifulSoup(self.HTML, 'html.parser')
        
        
        for var in varsUnnused:
            for x in soup.find_all('span', id=var):
                x['class'] = 'naoUsada'
            self.HTML = str(soup)
        
        
        
#####################################################
################ Interpreter methods ################
#####################################################

    def __init__(self):
        self.variaveis = {}
        # create a stack to store the current function
        self.funcStack = []
        self.instructions = {}
        self.HTML = ""
        self.eC = {}
        self.ecStack = []

    def start(self, tree):
        self.variaveis['GLOBAL'] = []
        # inicio do programa
        self.htmlInit()
        self.HTML += "<br>"
        self.visit_children(tree)
        self.htmlEnd()
        self.updateHTML()
        self.writeHTML()

        # fim do programa
        self.printVars()
        # print the Selecao tree
        #print(json.dumps(self.eC, indent=4))
        
        #for x in self.instructions.keys():
        #    print("Instrucao "+ x + " : " + str(self.instructions[x]))
    
    def componentes(self, tree):
        self.visit_children(tree)
    
    def componente(self, tree):
        for elemento in tree.children:
            self.HTML += self.getTab()
            if(type(elemento) == Tree):
                self.visit(elemento)
            else:
                if (elemento.type=='COMENTARIO'):
                    comentario = elemento.value
                    self.HTML += "<span class='code'> "+comentario+" </span> <br>"
            
    def declaracao(self, tree):
        atr=False
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
                        atr = True
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
                    if self.checkDecl(id):
                        self.HTML += "<span class='redeclaracao' id ='"+ str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                    else:
                        self.HTML += "<span class='code' id ='"+ str(self.funcAct()) + "-" + id +"'> " + id + " </span>"
                elif (elemento.type=='PVIR'):
                    self.HTML += "<span class='code'> ; </span> <br> <br>"
                    
                    
        # print("Elementos visitados")
        # se a variavel esta declarada no contexto atual
        if self.checkDecl(id):
            print("Variavel "+id+" ja declarada") 
        # se a variavel nao esta declarada no contexto atual
        else:
            # se a funcao atual for nula, estamos no contexto global
            if self.funcAct() == None:
                self.variaveis['GLOBAL'].append({'nome':id,'tipo':t,'usada':False,'atribuicao':atr})
            # se a funcao atual nao for nula, estamos no contexto de uma funcao
            else:
                self.variaveis[self.funcAct()].append({'nome':id,'tipo':t,'usada':False,'atribuicao':atr})

    def deffuncao(self,tree):
        self.HTML += self.getTab()
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
                    self.HTML += "<span class='funcName'> " + t + "</span> <span class='code'> ( </span>"
                    
                elif (elemento.type == 'DEF'):
                    t = elemento.value
                    self.HTML += "<span class='def'> " + t + " </span>"
        for var in self.variaveis[self.funcAct()]:
            if not var['usada']:
                print("Variavel "+var['nome']+" na funcao "+self.funcAct()+" nao usada (3)")
        self.popFunc()
        self.HTML += self.getTab() + "<span class='code'> } </span> <br> \n"

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
                    self.HTML += "<span class='code'> ; </span> <br> <br>"

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
                            print("Variavel "+id+" não declarada (2)")
                            self.HTML += "<span class='naoDeclaracao id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                        else:
                            if self.inFuncao():
                                for x in self.variaveis[self.funcAct()]:
                                    if x['nome'] == id:
                                        self.setVar(id,'usada',True)
                                        if x['atribuicao'] == False:
                                            print("Variavel "+id+" não inicializada (4)")
                                            self.HTML += "<span class='naoInicializada' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                                        else:
                                            self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                            else:
                                for x in self.variaveis['GLOBAL']:
                                    if x['nome'] == id:
                                        self.setVar(id,'usada',True)
                                        if x['atribuicao'] == False:
                                            print("Variavel "+id+" não inicializada (4)")
                                            self.HTML += "<span class='naoInicializada' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                                        else:
                                            self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                    else:
                        self.HTML += "<span class='code' >."+id+"</span>"
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
                    self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
        # print("Elementos visitados, vou regressar à main()")
        # print("Elementos visitados, vou regressar à main()")
        if id not in [x['nome'] for x in self.variaveis['GLOBAL']]:
            if self.inFuncao():
                if self.funcAct() not in self.variaveis.keys():
                    self.variaveis[self.funcAct()] = []
                if id not in [x['nome'] for x in self.variaveis[self.funcAct()]]:
                    self.variaveis[self.funcAct()].append({'nome':id,'tipo':t,'usada':False,'atribuicao':True})
                else:
                    print("Variavel "+id+" já declarada (1)")
            else:
                self.variaveis['GLOBAL'].append({'nome':id,'tipo':t,'usada':False,'atribuicao':True})
        else:
            print("Variavel "+id+" já declarada (1)")
            return

    def corpofunc(self, tree):
        self.HTML += "<span class='code'> ) </span><span class='code'> { </span> <br> <br>"
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if(elemento.data == 'componente'):
                    self.visit(elemento)
                elif(elemento.data == 'deffuncao'):
                    self.visit(elemento)
                elif(elemento.data == 'retorno'):
                    self.visit(elemento)

    def atribuicao(self, tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.visit(elemento)
            else:
                if (elemento.type == 'ID'):
                    id = elemento.value
                    self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
        if id not in [x['nome'] for x in self.variaveis['GLOBAL']]:
            if self.inFuncao():
                if self.funcAct() not in self.variaveis.keys():
                    print("Variavel "+id+" não declarada (2)")
                elif id not in [x['nome'] for x in self.variaveis[self.funcAct()]]:
                    print("Variavel "+id+" não declarada (2)")
                else:
                    self.setVar(id,'atribuicao',True)
            else:
                print("Variavel "+id+" não declarada (2)")
        else:
            self.setVar(id,'atribuicao',True)

    def leitura(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if (elemento.data == 'ficheiro'):
                    self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
                        print("Variavel "+id+" não declarada (2)")
                        self.HTML += "<span class='naoDeclaracao'>, "+id+" ) </span>"
                    else:
                        self.setVar(id,'atribuicao',True) 
                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>," + id + " (</span>"
                if (elemento.type=='LER'):
                    t = elemento.value
                    self.HTML += "<span class='code'>" + t + " ( </span>"
                    
    def escrita(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if (elemento.data == 'ficheiro'):
                    self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
                        print("Variavel "+id+" não declarada (2)")
                        self.HTML += "<span class='naoDeclaracao'>, "+id+" ) </span>"
                    else:
                        self.setVar(id,'atribuicao',True)
                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>," + id + " ) </span>"
                if (elemento.type=='ESCREVER'):
                    t = elemento.value
                    self.HTML += "<span class='code'>" + t + " ( </span>"
    
    def ficheiro(self, tree):
        first = True
        for elemento in tree.children:
            if(type(elemento)==Tree):
                self.visit(elemento)
            else:
                if(elemento.type=='ID'):
                    if first:
                        id = elemento.value
                        first = False
                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                    else:
                        id = elemento.value
                        self.HTML += "<span class='code' >."+id+" </span>"

    def selecao(self,tree):
        se = False
        c = 0
        for elemento in tree.children:
            t = ""
            if (type(elemento)==Tree):
                
                if (elemento.data != 'comp') and se:
                    self.HTML += self.getTab()
                self.visit(elemento)
                if (elemento.data == 'comp'):
                    self.HTML += "<span class='code'> { </span> <br> <br>"
            else:
                t = elemento.value
                if (elemento.type=='ID'):
                    if not self.checkDecl(t):
                        print("Variavel "+t+" não declarada (2)")
                        self.HTML += "<span class='naoDeclaracao'> "+t+" </span>"
                    else:
                        self.setVar(t,'usada',True)
                    self.HTML += "<span class='code' id ='"+ str(self.funcAct()) + "-" + t + "'>" + t + " </span> <br>"
                elif (elemento.type=='SE'):
                    self.pushEc("if")
                    se = True
                    self.HTML += "<span class='ciclo'> "+t+" </span>"
                
                elif (elemento.type=='CASO'):
                    self.pushEc("case")
                    self.HTML += "<span class='ciclo'> "+t+" </span>"
                    
                elif (elemento.type=='END'):
                    self.HTML +=self.getTab()[:-1]+ "<span class='ciclo'> "+t+" </span> <br> <br>"

                elif (elemento.type == 'COMENTARIO'):
                    c +=1
                    comentario = elemento.value
                    self.HTML += self.getTab() +"<span class='code'> "+comentario+" </span> <br>"
        if se:             
            self.HTML += self.getTab()[:-1]+ "<span class='code'> } </span> <br> <br>"
        
        if len(tree.children) == 2:
            print("Selecao "+ self.ecAct()+" vazia.")
        elif len(tree.children) == 3+c:
            v = self.getEcVal(self.eC , self.ecStack)
            if type(v)==dict and len(v.keys())==1 and 'if' in list(v.keys())[0]:
                        print("Selecao "+ self.ecAct()+" é IF com IF aninhado e de possivel junção.")
        self.popEc()

    def repeticao(self, tree):
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'comp'):
                    self.visit(elemento)
                elif (elemento.data == 'componente'):
                    self.visit(elemento)
                elif (elemento.data == 'interv'):
                    self.visit(elemento)
            else:
                if (elemento.type=='ENQ'):
                    id = elemento.value
                    self.HTML += "<span class='ciclo'> "+id+" </span>"
                elif (elemento.type=='FAZER'):
                    id = elemento.value
                    self.HTML += "<span class='ciclo'> "+id+" </span>"
                elif (elemento.type=='END'):
                    id = elemento.value
                    self.HTML += "<span class='ciclo'> "+id+" </span> <br> <br>"
                elif (elemento.type == 'REPETIR'):
                    id = elemento.value
                    self.HTML += "<span class='ciclo'> "+id+" </span>"
                elif (elemento.type == 'ATE'):
                    id = elemento.value
                    self.HTML += "<span class='ciclo'> "+id+" </span>"
                elif (elemento.type == 'PARA'):
                    id = elemento.value
                    self.HTML += "<span class='ciclo'> "+id+" </span>"

    def retorno(self, tree):
        self.HTML += self.getTab()
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'elemcomp'):
                    self.visit(elemento)
            else:
                if (elemento.type =='RET'):
                    id = elemento.value
                    self.HTML += "<span class='retornos'> "+id+" </span>"
                elif (elemento.type =='PVIR'):
                    id = elemento.value
                    self.HTML += "<span class='code'> "+id+" </span> <br> <br>"
                
    def comp(self,tree):
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if (elemento.data == 'sinalcomp'):
                    t = self.visit(elemento)
                    self.HTML += "<span class='code'> "+t+" </span>"
                elif (elemento.data == 'elemcomp'):
                    self.visit(elemento)
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
                        print("Variavel "+id+" não declarada (2)")
                        self.HTML += "<span class='naoDeclaracao'>!"+id+" </span>"
                    else:
                        self.setVar(id,'usada',True)
                        self.HTML += "<span class='code'>!"+id+" </span>"
                        
    def sinalcomp(self, tree):
        for elemento in tree.children:
            return elemento.value

    def caso(self,tree):
        self.HTML += self.getTab()
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'elemcomp'):
                    self.visit(elemento)
                    self.HTML += "<span class='code'> : { </span> <br> <br>"
                    
                elif (elemento.data == 'componente'):
                    self.visit(elemento)
        self.HTML += self.getTab()[:-1] +"<span class='code'> } </span> <br> <br>"            
        
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
                        print("Variavel "+id+" não declarada (2)")
                        self.HTML += "<span class='naoDeclaracao'> " + id + " </span>"
                    else:
                        if self.inFuncao():
                            for x in self.variaveis[self.funcAct()]:
                                if x['nome'] == id:
                                    # colocar a variavel como usada
                                    self.setVar(id,'usada',True)
                                    if x['atribuicao'] == False:
                                        print("Variavel "+id+" não inicializada (4)")
                                        self.HTML += "<span class='naoInicializada'> " + id + " </span>"
                                    else:
                                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'> " + id + " </span>"
                        else:
                            for x in self.variaveis['GLOBAL']:
                                if x['nome'] == id:
                                    self.setVar(id,'usada',True)
                                    if x['atribuicao'] == False:
                                        print("Variavel "+id+" não inicializada (4)")
                                        self.HTML += "<span class='naoInicializada'> " + id + " </span>"
                                    else:
                                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'> " + id + " </span>"
                
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
                    self.HTML += "<span class='funcName' id ='"+ str(self.funcAct()) + "-" + id +"'> " + id + " </span> <span class='code'>(</span>"
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
        

f = open('linguagem.txt', 'r')
frase = f.read()
f.close()

p = Lark(grammar)
p = Lark(grammar)
tree = p.parse(frase)
data = MyInterpreter().visit(tree)




