import os
import re
from lark import Lark, Token, Tree
from lark.visitors import Interpreter
from lark import Discard
from bs4 import BeautifulSoup
import json
from bs4 import BeautifulSoup

# Primeiro precisamos da GIC
grammar = r'''
//Regras Sintaticas
start: componentes
componentes: (componente|deffuncao)*
componente: COMENTARIO | instrucao   
deffuncao: DEF tipo ID "(" params? ")" corpofunc
funcao: ID "(" (ecomp("," ecomp)*)? ")"
instrucao : atribuicao PVIR
        | leitura PVIR
        | escrita PVIR
        | declaracao PVIR
        | selecao
        | repeticao
        | funcao PVIR
declaracao: tipo ID ( "=" ecomp )? 
tipo : INT
    | BOOLEAN
    | STRING
    | ARRAY
    | TUPLO
    | LISTA
ecomp: exp|elemcomp
exp: NUM op NUM
    | ID "[" NUM "]"
    | ID DOT oplist
    | ID DOT ID
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
atribuicao: ID "=" ecomp
leitura: LER "(" ficheiro "," ID ")"
escrita: ESCREVER "(" ficheiro "," ID ")"
ficheiro: ID (DOT ID)?
selecao: SE comp "{" (COMENTARIO|instrucao)* "}" senao?
        | CASO ID caso+ END
senao: SENAO "{" (COMENTARIO|instrucao)* "}"
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
SENAO: "senao"
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
DOT: "."
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
        self.variaveis[func] = []

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

    def countEcSE(self,d):
        c = 0
        for x in d.keys():
            for a in ['if','case']:
                if a in x:
                    c+= 1
            c += self.countEcSE(d[x])
        return c
    
    def countEcREP(self,d):
        c = 0
        for x in d.keys():
            for a in ['do','while','for']:
                if a in x:
                    c+= 1
            c += self.countEcREP(d[x])
        return c

    def countEcAux(self,d):
        #     0 1   2   3   4   5
        #    cs cr csr css crr crs
        c = [ 0, 0,  0,  0,  0,  0]
        for x in d.keys():
            for a in ['do','while','for']:
                if a in x:
                    c[1] += 1
                    c2 = self.countEcAux(d[x])
                    c[2] += c2[2]
                    c[3] += c2[3]
                    c[4] += c2[1] + c2[2] + c2[4]
                    c[5] += c2[0] + c2[3] + c2[5]
            for a in ['if','case']:
                if a in x:
                    c[0] += 1
                    c2 = self.countEcAux(d[x])
                    c[2] += c2[1] + c2[2] + c2[4]
                    c[3] += c2[0] + c2[3] + c2[5]
                    c[4] += c2[4]
                    c[5] += c2[5]
        return c

    def countEc(self):
        c = self.countEcAux(self.eC)
        self.HTML += f"<tr><td><span>SE's dentro de SE's:</td><td>   {str(c[3])}</span></td></tr>"
        self.HTML += f"<tr><td><span>SE's dentro de REP's:</td><td>  {str(c[5])}</span></td></tr>"
        self.HTML += f"<tr><td><span>REP's dentro de SE's:</td><td>  {str(c[2])}</span></td></tr>"
        self.HTML += f"<tr><td><span>REP's dentro de REP's:</td><td> {str(c[4])}</span></td></tr>"
        print("SE's dentro de SE's: " + str(c[3]))
        print("SE's dentro de REP's: " + str(c[5]))
        print("REP's dentro de SE's: " + str(c[2]))
        print("REP's dentro de REP's: " + str(c[4]))

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
        vares = []
        maxnome = 0
        maxtipo = 0
        for f in self.variaveis:
            vares += self.variaveis[f]
        if len(vares) > 0:
            maxnome = max([len(x['nome']) for x in vares])
            maxtipo = max([len(x['tipo']) for x in vares])
        for x in self.variaveis.keys():
            print("\t"+x)
            for y in self.variaveis[x]:
                # string com o numero de espacos necessarios para alinhar as variaveis
                s1 =  " "*(maxnome-len(y['nome']))
                # string com o numero de espacos necessarios para alinhar os tipos
                s2 =  " "*(maxtipo-len(y['tipo']))
                s = "\t\t"+y['nome']+s1+" : "+y['tipo']+s2+" : "+str(y['usada'])+" : "+str(y['atribuicao'])+" :"
                print(s)
    
    def writeHTML(self):
        f = open("output.html", "w")
        f.write(self.HTML)
        f.close()

    def htmlInit(self):
        self.HTML += ''' 
        <!DOCTYPE html>
        <html>
        <head>
            <title>My HTML Page</title>
            <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
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

            .ciclo.juncao {
                position: relative;
                display: inline-block;
                color: #ff9900;
                border-bottom: 2px dotted black;
            }

            .ilhas {
                position: relative;
                display: inline-block;
                color: #00ff00;
                border-bottom: 2px dotted black;
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
            
            .container {
                display: flex;
                overflow-x: auto;
            }

            .left-container,
            .right-container {
                flex: 1;
            }
            
            .image-container {
  width: fit-content; /* Set the width to fit the image */
  height: fit-content; /* Set the height to fit the image */
  display: inline-block; /* Display the container as an inline element */
  overflow: hidden; /* Hide any overflow of the image */
}

.image-container img {
  display: block; /* Make the image a block element */
  max-width: 100%; /* Limit the image width to the container's width */
  cursor: grab; /* Show a grab cursor when hovering over the image */
}

        .image-container img:active {
            cursor: grabbing; /* Show a grabbing cursor when the image is clicked */
        }
    </style>
    <script>
        var isMouseDown = false;
        var startX, startY, scrollLeft, scrollTop;

        function startPan(event) {
            isMouseDown = true;
            startX = event.clientX - event.target.offsetLeft;
            startY = event.clientY - event.target.offsetTop;
            scrollLeft = event.target.scrollLeft;
            scrollTop = event.target.scrollTop;
        }

        function endPan() {
            isMouseDown = false;
        }

        function panImage(event) {
            if (!isMouseDown) return;
            event.preventDefault();
            var img = event.target;
            var offsetX = event.clientX - img.offsetLeft;
            var offsetY = event.clientY - img.offsetTop;
            var deltaX = offsetX - startX;
            var deltaY = offsetY - startY;
            img.scrollLeft = scrollLeft - deltaX;
            img.scrollTop = scrollTop - deltaY;
        }
    </script>
</head>
        <body class="graficos">
        <div class="container">
            <div class="left-container">
                <h2 class="code">Análise de código</h2>
                <pre><code>
                <h3 class="code">Instruções de Análise - Variáveis</h3>
                <span class="redeclaracao">Cor -</span> <span class="code"> Redeclaração </span> <br> \n
                <span class="naoDeclaracao">Cor -</span> <span class="code"> Não-Declaração </span> <br> \n
                <span class="naoInicializada">Cor -</span> <span class="code"> Não-Inicializada </span> <br> \n
                <span class="naoUsada">Cor -</span> <span class="code"> Não-Utilizada </span> <br> \n 
                <h3 class="code">Instruções de Análise - Seleções</h3>
                <span class="ciclo juncao">Cor -</span> <span class="code"> Seleção com seleção aninhada de possivel junção </span> <br> \n 
                <h3 class="code">Instruções de Análise - Outros</h3>
                <span class="ilhas">Cor -</span> <span class="code"> Inicio de código inalcansável </span> <br> \n 
        '''

    def htmlEnd(self):
        self.HTML += '''
        </div>
        </div>
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

        # for t in varsUnnused:
        #    print("Variável --> " + t + " não utilizada")

        soup = BeautifulSoup(self.HTML, 'html.parser')

        for var in varsUnnused:
            for x in soup.find_all('span', id=var):
                x['class'] = 'naoUsada'
        
        # in every class "naoDeclarada" add title "Variável não declarada"
        xs = ['redeclaracao','naoDeclaracao','naoInicializada','naoUsada','ciclo juncao','ilhas']
        ys = ['Redeclaração','Não-Declaração','Não-Inicializada','Não-Utilizada','Seleção com seleção aninhada de possivel junção','Inicio de código inalcansável']
        for i in range(0,len(xs)):
            for y in soup.find_all(class_=xs[i]):
                y['title'] = ys[i]
        self.HTML = str(soup)

    def geraGrafos(self):
        os.system("dot -Tpng -o cfgImage.jpg cfg.dot")
        os.system("dot -Tpng -o sdgImage.jpg sdg.dot")
        self.HTML += '''
        </div>
        <div class="right-container">
        <h2 class="code">Grafos de fluxo de controlo</h2>
        <div class="image-container w3-card-4">
        <a href="cfgImage.jpg" target="_blank">
            <img src="cfgImage.jpg" alt="Image" onmousedown="startPan(event)" onmouseup="endPan()" onmousemove="panImage(event)" onmouseout="endPan()" draggable="false">
        </a>
        </div>
        <h2 class="code">Grafos de dependências de controlo</h2>
        <div class="image-container w3-card-4">
        <a href="sdgImage.jpg" target="_blank">
            <img src="sdgImage.jpg" alt="Image" onmousedown="startPan(event)" onmouseup="endPan()" onmousemove="panImage(event)" onmouseout="endPan()" draggable="false">
        </a>
        '''

    def getSDGFunc(self):
        r = 'Entry_GLOBAL'
        if len(self.sdgFunc) > 0:
            r = "\""+self.sdgFunc[-1]+"\""
        return r
    
    def complexidadeMcCabes(self):
        #file_path = "sdg.dot"  # Replace with your file path
        #file = open(file_path, "r")
        #lines = file.readlines()
        #file.close()
        lines = self.sdg.split("\n")
        del lines[0]       # Delete the first element
        del lines[-1] 
        direita = []
        nodos = []

        funcoes = {}
        for line in lines:
            if "Entry" in line:
                ls = line.split("->")
                for i in range(0, len(ls)):
                    ls[i] = ls[i].strip().replace("\n", "")
                if ls[1] not in direita:
                    direita.append(ls[1])
                nodos.append(ls[0])
                nodos.append(ls[1])
                for i in range(0, len(ls)):
                    if "Entry" in ls[i]:
                        if ls[i] not in funcoes.keys():
                            key = ls[i].strip().replace("\n", "")
                            funcoes[key] = {}
               
        antigo = ""
        for line in lines:
            if '->' in line:
                ls = line.split("->")
                for i in range(0, len(ls)):
                    ls[i] = ls[i].strip().replace("\n", "")
                if ls[1] not in direita:
                    direita.append(ls[1])
                nodos.append(ls[0])
                nodos.append(ls[1])
                key1 = ls[0]
                key2 = ls[1]
                if key1 in funcoes.keys():
                    if "arestas" not in funcoes[key1].keys():
                        funcoes[key1]["arestas"] = 1
                    else:
                        funcoes[key1]["arestas"] += 1
                    if "nodos" not in funcoes[key1].keys():
                        funcoes[key1]["nodos"] = [key2]
                    else:
                        if key2 not in funcoes[key1]["nodos"]:
                            funcoes[key1]["nodos"].append(key2)

                    antigo = key1
                elif key1 and key2 not in funcoes.keys():
                    if "nodos" not in funcoes[antigo].keys():
                        funcoes[antigo]["nodos"] = [key1, key2]
                        funcoes[antigo]["arestas"] += 1
                    else:
                        if key1 not in funcoes[antigo]["nodos"]:
                            funcoes[antigo]["nodos"].append(key1)
                        if key2 not in funcoes[antigo]["nodos"]:
                            funcoes[antigo]["nodos"].append(key2)
                        funcoes[antigo]["arestas"] += 1
                else :
                    if "arestas" not in funcoes[antigo].keys():
                        funcoes[antigo]["arestas"] = 1
                    else:
                        funcoes[antigo]["arestas"] += 1 
        self.HTML += "</div><div><h3>Complexidade de McCabe</h3>"
        for key in funcoes.keys():
            self.HTML += "<span> Função " + key + "</span> <br>"
            self.HTML += f'''<pre>
                    \tNodos: {len(funcoes[key]["nodos"])}
                    \tArestas: {funcoes[key]["arestas"]}
                    \tComplexidade de McCabe: {funcoes[key]["arestas"] - len(funcoes[key]["nodos"]) + 2}
                </pre>'''
            print("Funcao: " + key)
            print("\tNodos: " + str(funcoes[key]["nodos"]))
            print("\tArestas: " + str(funcoes[key]["arestas"]))
            print("\tComplexidade de McCabe: " + str((funcoes[key]["arestas"]) - len(funcoes[key]["nodos"]) + 2))
        # remove duplicates from the list
        n = list(dict.fromkeys(nodos))
        notDireita = [x for x in n if x not in direita]
        if len(notDireita) > 0:
            self.HTML += "<span> Grafos de Ilha:</span> <br>"
            self.HTML += "<ul>"
            for x in notDireita:
                self.HTML += "<li>" + x + "</li>"
                # in self.HTML where id=x add the class "ilhas"
                soup = BeautifulSoup(self.HTML, 'html.parser')
                x = x.replace("\"", "").replace(" ", "").strip()
                for y in soup.find_all('span', id=x):
                    y['class'].append('ilhas')
            self.HTML = str(soup)


            self.HTML += "</ul>"
        else:
            self.HTML += "<span> Não existem grafos de ilha </span> <br>"

#####################################################
################ Interpreter methods ################
#####################################################

    def __init__(self):
        self.vars = [[],[],[],[]]
        self.variaveis = {}
        '''
        Variaveis:
            GLOBAL
                */  nome   : tipo   : usada : atribuicao : */
            nome_funcao
                    argumentos  : int    : False : True :
                    variaveis   : array  : False : True :
        '''
        # create a stack to store the current function
        self.sdgFunc = []
        self.funcStack = []
        self.instructions = {}
        self.HTML = ""
        self.eC = {}
        self.ecStack = []
        self.cfg = "digraph G {\n"
        self.sdg = "digraph G {\n"
        self.cfgAnt = ""
        self.instC = 0

    def start(self, tree):
        self.variaveis['GLOBAL'] = []
        # inicio do programa
        self.htmlInit()
        self.HTML += "<br>"
        self.visit_children(tree)
        self.cfg+="}\n"
        self.sdg+="}\n"
        with open("cfg.dot", "w") as f:
            f.write(self.cfg)
            f.close()
        with open("sdg.dot", "w") as f:
            f.write(self.sdg)
            f.close()
        self.HTML +=f"""
            </code></pre>
            <h3>Estatisticas</h3>
            <table>
            <tr>
                <th>  </th><th>  </th>
                </tr>
                <tr><td><span>Variáveis já declaradas:</td><td> {str(len(self.vars[0]))}</span></td></tr>
                <tr><td><span>Variáveis não declaradas:</td><td> {str(len(self.vars[1]))}</span></td></tr>
                <tr><td><span>Variáveis não utilizadas:</td><td> {str(len(self.vars[2]))}</span></td></tr>
                <tr><td><span>Variáveis não inicializadas:</td><td> {str(len(self.vars[3]))}</span></td></tr>
                
        """
        print("Variáveis já declaradas: " + str(len(self.vars[0])))
        print("Variáveis não declaradas: " + str(len(self.vars[1])))
        print("Variáveis não utilizadas: " + str(len(self.vars[2])))
        print("Variáveis não inicializadas: " + str(len(self.vars[3])))
        tipos={}
        for x in self.variaveis.keys():
            for v in self.variaveis[x]:
                if v['tipo'] in tipos.keys():
                    tipos[v['tipo']] += 1
                else:
                    tipos[v['tipo']] = 1
        t = 0
        for x in tipos.keys():
            t += tipos[x]
            self.HTML += "<tr><td><span>Variáveis do tipo " + x + f":</td><td> {str(tipos[x])}</span></td></tr>"
            print("Variáveis do tipo " + x + ": " + str(tipos[x]))
        self.HTML += f"<tr><td><span>Total de variaveis:</td><td> {str(t)}</span></td></tr>"
        print("Total de variáveis: " + str(t))
        self.countEc()
        self.geraGrafos()
        self.complexidadeMcCabes()
        self.htmlEnd()
        self.updateHTML()
        
        self.writeHTML()
        # fim do programa
        self.printVars()
        # print the Selecao tree
        #print(json.dumps(self.eC, indent=4))
        
        for x in self.instructions.keys():
            print("Instrucao "+ x + " : " + str(self.instructions[x]))
    
    def componentes(self, tree):
        retorno =""
        for elemento in tree.children:
            if (type(elemento)==Tree):
                retorno += self.visit(elemento)
        with open("instrucoes", "w") as f:
            f.write(retorno)
    
    def componente(self, tree):
        retorno =""
        for elemento in tree.children:
            self.HTML += self.getTab()
            if(type(elemento) == Tree):
                retorno += self.visit(elemento)
            else:
                if (elemento.type=='COMENTARIO'):
                    comentario = elemento.value
                    self.HTML += "<span class='code'> "+comentario+" </span> <br>"
        return retorno
            
    def declaracao(self, tree):
        retorno =""
        atr=False
        for elemento in tree.children:
            # simbolo nao terminal
            if (type(elemento)==Tree):
                # nao terminal 'tipo' na gramatica
                if( elemento.data == 'tipo'):
                    # obter o valor do nao terminal (return da funcao "tipo(self,tree)")
                    t = self.visit(elemento)
                    retorno +=" "+ t + " "
                    self.HTML += "<span class='code'> "+t+" </span>"
                elif (elemento.data == 'ecomp'):
                    atr = True
                    if 'atribuicao' not in self.instructions.keys():
                        self.instructions['atribuicao'] = 1
                    else:
                        self.instructions['atribuicao'] += 1
                    self.HTML += "<span class='code'> = </span>"
                    retorno += " = "
                    retorno += self.visit(elemento)
            else:
                # simbolo terminal 'ID' na gramatica
                if (elemento.type=='ID'):
                    # obter o valor do terminal
                    id = elemento.value
                    retorno += id
                    if self.checkDecl(id):
                        self.HTML += "<span class='redeclaracao' id ='"+ str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                    else:
                        self.HTML += "<span class='code' id ='"+ str(self.funcAct()) + "-" + id +"'> " + id + " </span>"

          
        # se a variavel esta declarada no contexto atual
        if self.checkDecl(id):
            self.vars[0].append(str(self.funcAct()) +"-"+id) 
        # se a variavel nao esta declarada no contexto atual
        else:
            # se a funcao atual for nula, estamos no contexto global
            if self.funcAct() == None:
                self.variaveis['GLOBAL'].append({'nome':id,'tipo':t,'usada':False,'atribuicao':atr})
            # se a funcao atual nao for nula, estamos no contexto de uma funcao
            else:
                self.variaveis[self.funcAct()].append({'nome':id,'tipo':t,'usada':False,'atribuicao':atr})
        return retorno

    def deffuncao(self,tree):
        retorno = "" 
        ant = self.cfgAnt
        self.HTML += self.getTab()
        for elemento in tree.children:
            if (type(elemento) == Tree):
                t = self.visit(elemento)
                if (elemento.data == 'tipo'):
                    self.HTML += "<span class='code'> " + t + " </span>"
                elif (elemento.data == 'corpofunc'):
                    retorno += ")" 
                retorno += " "+ t + " "
            else:
                t = elemento.value
                if (elemento.type == 'ID'):
                    self.pushFunc(t)
                    self.sdgFunc.append("Entry_"+t)
                    self.HTML += "<span id='Entry_"+t+"' class='funcName'> " + t + "</span> <span class='code'> ( </span>"
                    retorno += " "+ t + "(" + " "
                    self.cfgAnt = "Entry_"+t
                elif (elemento.type == 'DEF'):
                    retorno += " "+ t + " "
                    self.HTML += "<span class='def'> " + t + " </span>"
        for var in self.variaveis[self.funcAct()]:
            if not var['usada']:
#                print("Variavel "+var['nome']+" na funcao "+self.funcAct()+" nao usada (3)")
                self.vars[2].append(str(self.funcAct()) +"-"+var['nome'])
        if self.cfgAnt != "":
            self.cfg += '"'+ self.cfgAnt + "\" -> " + "Exit_"+self.funcAct() + "\n"
        self.cfgAnt = ant
        self.popFunc()
        self.sdgFunc.pop()
        self.HTML += self.getTab() + "<span class='code'> } </span> <br> \n"
        return retorno
 
    def funcao(self,tree):
        first = True;
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (first):
                    first = False
                else:
                    self.HTML += "<span class='code'>, </span>"
                    retorno += ", " + " "
                retorno += self.visit(elemento) + " "
            else: 
                if (elemento.type == 'ID'):
                    id = elemento.value     
                    retorno += id +"(" + " "
                    self.HTML += "<span class='funcName' id ='"+ str(self.funcAct()) + "-" + id +"'> " + id + " </span> <span class='code'>(</span>"
                    self.sdg += self.getSDGFunc()+' -> "Entry_'+id+'"\n'
        self.HTML += "<span class='code'> ) </span>" 
        retorno += ")" + " "
        return retorno
        
    def instrucao(self, tree):
        self.instC += 1
        retorno = str(self.instC) +": " 
        isF = ""
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if elemento.data not in self.instructions.keys():
                    self.instructions[elemento.data] = 1
                else :
                    self.instructions[elemento.data] += 1
                if elemento.data=='selecao' or elemento.data=='repeticao':
                    self.visit(elemento)
                    retorno = self.cfgAnt
                    self.cfgAnt = ""
                else:
                    t = self.visit(elemento)
                    retorno += t + " "
                    if (elemento.data == 'funcao'):    
                        isF = t
            else:
                if (elemento.type == 'PVIR'):
                    self.HTML += "<span class='code'> ; </span> <br> <br>"
                    retorno += " ; " + " "
        if self.cfgAnt != "":
            self.cfg+= '"'+self.cfgAnt + '" -> "' + retorno + '"\n'
            f = self.getSDGFunc()
            self.sdg+=f+' -> "'+retorno+'"\n'
        self.cfgAnt = retorno
        retorno+="\n"
        return retorno

    def tipo(self, tree):
        for elemento in tree.children:
            return elemento.value

    def ecomp(self,tree):
        retorno = "" 
        retorno += self.visit(tree.children[0]) + " "
        return retorno

    def exp(self,tree):
        retorno = "" 
        i = 0
        firstEntry = 0
        firstElement = ""
        for elemento in tree.children:
            if (type(elemento)==Tree):
                t = self.visit(elemento)
                retorno += t + " "
                self.HTML += "<span class='code'> "+t+" </span>"
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    retorno += id + " "
                    if (firstEntry == 0):
                        firstElement = "ID"
                        firstEntry = 1
                    else:
                        firstEntry = 2
                    if i == 0:
                        i+=1
                        if not self.checkDecl(id):
#                            print("Variavel "+id+" não declarada (2)")
                            self.vars[1].append(str(self.funcAct()) +"-"+id)
                            self.HTML += "<span class='naoDeclaracao id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                        else:
                            if self.inFuncao():
                                for x in self.variaveis[self.funcAct()]:
                                    if x['nome'] == id:
                                        self.setVar(id,'usada',True)
                                        if x['atribuicao'] == False:
#                                            print("Variavel "+id+" não inicializada (4)")
                                            self.vars[3].append(str(self.funcAct()) +"-"+id)
                                            self.HTML += "<span class='naoInicializada' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                                        else:
                                            self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                            else:
                                for x in self.variaveis['GLOBAL']:
                                    if x['nome'] == id:
                                        self.setVar(id,'usada',True)
                                        if x['atribuicao'] == False:
#                                            print("Variavel "+id+" não inicializada (4)")
                                            self.vars[3].append(str(self.funcAct()) +"-"+id)
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
                        retorno += num + " "
                        self.HTML += "<span class='code'> "+num+" </span>"
                    else:
                        num = elemento.value
                        retorno += "["+num+"]" + " "
                        self.HTML += "<span class='code'>[ "+num+" ]</span>"
                elif (elemento.type == 'DOT'):
                    retorno += elemento.value + " "
        return retorno

    def op(self, tree):
        for elemento in tree.children:
            return elemento.value

    def oplist(self, tree):
        for elemento in tree.children:
            return elemento.value

    def params(self, tree):
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'param'):
                    retorno += self.visit(elemento) + " "
            else:
                if (elemento.type == 'VIR'):
                    self.HTML += "<span class='code'>, </span>"
                    retorno += ", " + " "
        return retorno

    def param(self, tree):
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'tipo'):
                    t = self.visit(elemento)
                    retorno += t + " "
                    self.HTML += "<span class='code'> " + t + " </span>"
            else:
                if (elemento.type == 'ID'):
                    id = elemento.value
                    retorno += id + " "
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
#                    print("Variavel "+id+" já declarada (1)")
                    self.vars[0].append(self.funcAct() +"-"+id)
            else:
                self.variaveis['GLOBAL'].append({'nome':id,'tipo':t,'usada':False,'atribuicao':True})
        else:
#            print("Variavel "+id+" já declarada (1)")
            self.vars[0].append(self.funcAct() +"-"+id)
        return retorno

    def corpofunc(self, tree):
        retorno = "{\n"
        self.HTML += "<span class='code'> ) </span><span class='code'> { </span> <br> <br>"
        for elemento in tree.children:
            if (type(elemento)==Tree):
                retorno += self.visit(elemento)
        retorno += "}\n"
        return retorno

    def atribuicao(self, tree):
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento)==Tree):
                retorno += self.visit(elemento) + " "
            else:
                if (elemento.type == 'ID'):
                    id = elemento.value
                    retorno += id + " = " + " "
                    decl = True
                    if id not in [x['nome'] for x in self.variaveis['GLOBAL']]:
                        if self.inFuncao():
                            if self.funcAct() not in self.variaveis.keys() or id not in [x['nome'] for x in self.variaveis[self.funcAct()]]:
#                                print("Variavel "+id+" não declarada (2)")
                                self.vars[1].append(str(self.funcAct()) +"-"+id)
                                decl=False
                            else:
                                self.setVar(id,'atribuicao',True)
                        else:
#                            print("Variavel "+id+" não declarada (2)")
                            self.vars[1].append(str(self.funcAct()) +"-"+id)
                    else:
                        self.setVar(id,'atribuicao',True)
                    if not decl:
                        self.HTML += "<span class='naoDeclaracao' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                    else:
                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                    self.HTML += "<span class='code'>=</span>"
                    

        return retorno

    def leitura(self,tree):
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if (elemento.data == 'ficheiro'):
                    retorno += self.visit(elemento) +"," + " "
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    retorno += id +")" + " "
                    if not self.checkDecl(id):
#                        print("Variavel "+id+" não declarada (2)")
                        self.vars[1].append(str(self.funcAct()) +"-"+id)
                        self.HTML += "<span class='naoDeclaracao'>, "+id+" ) </span>"
                    else:
                        self.setVar(id,'atribuicao',True) 
                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>," + id + " (</span>"
                if (elemento.type=='LER'):
                    t = elemento.value
                    self.HTML += "<span class='code'>" + t + " ( </span>"
                    retorno += t + " (" + " "
        return retorno
                    
    def escrita(self,tree):
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento)==Tree):
                if (elemento.data == 'ficheiro'):
                    retorno += self.visit(elemento) + ", " + " "
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    if not self.checkDecl(id):
#                        print("Variavel "+id+" não declarada (2)")
                        self.vars[1].append(str(self.funcAct()) +"-"+id)
                        self.HTML += "<span class='naoDeclaracao'>, "+id+" ) </span>"
                    else:
                        self.setVar(id,'atribuicao',True)
                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>," + id + " ) </span>"
                    retorno += id + " )" + " "
                if (elemento.type=='ESCREVER'):
                    t = elemento.value
                    self.HTML += "<span class='code'>" + t + " ( </span>"
                    retorno += t + " (" + " "
        return retorno
    
    def ficheiro(self, tree):
        first = True
        for elemento in tree.children:
            if(type(elemento)==Tree):
                retorno += self.visit(elemento) + " "
            else:
                if(elemento.type=='ID'):
                    id = elemento.value
                    retorno += id + " "
                    if first:
                        first = False
                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'>" + id + " </span>"
                    else:
                        self.HTML += "<span class='code' >."+id+" </span>"
                elif(elemento.type=='DOT'):
                    retorno += elemento.value + " "
        return retorno
                
    def selecao(self,tree):
        retorno = str(self.instC)+": " 
        se = False
        senao = False
        c = 0
        ant = ""
        inicioIF = ""
        for elemento in tree.children:
            t = ""
            if (type(elemento)==Tree):
                if (elemento.data == 'comp') and se:
                    # instrucao do if
                    retorno += self.visit(elemento) + " "
                    # grafo CFG ant->if
                    self.cfg+= '"'+self.cfgAnt + '" -> "' + retorno + '"\n'
                    # grafo SDG func->if
                    self.sdg+= self.getSDGFunc()+' -> "' + retorno + '"\n'
                    # update func para if
                    self.sdgFunc.append(retorno)
                    # guarda inicio do if
                    inicioIF = retorno
                    # instrucao then
                    entao = str(self.instC)+": ENTAO"
                    # atribuir txt a instrucao then
                    self.sdg += '"'+entao+'" [label="ENTAO"]\n'
                    self.sdgFunc.append(entao)
                    # instrucao else no CFG
                    self.cfg+= '"'+inicioIF + '" -> "'+entao +'"\n'
                    # atualiza a cfgAnt
                    self.cfgAnt = entao
                    # instrucao else no SDG
                    self.sdg+= '"'+inicioIF+'" -> "'+entao+'"\n'
                    # colocar o if em diamante
                    self.cfg+= '"'+inicioIF+'" [shape=diamond]\n'
                    retorno += " {\n"
                    self.HTML += "<span class='code'> { </span> <br> <br>"
                elif (elemento.data == 'senao'):
                    # instrucao else
                    senao = str(self.instC)+": SENAO"
                    # atribuir txt a instrucao then
                    self.sdg += '"'+senao+'" [label="SENAO"]\n'
                    # instrucao else no SDG
                    self.sdg+= '"'+inicioIF+'" -> "'+senao+'"\n'
                    # pop do then no SDG
                    self.sdgFunc.pop()
                    # update func para else
                    self.sdgFunc.append(senao)
                    # guarda inicio do else no CFG
                    ant = self.cfgAnt
                    self.cfgAnt = inicioIF
                    # trata do corpo do else
                    self.visit(elemento)
                    senao = True
                elif (elemento.data == 'caso'):
                    retorno += self.visit(elemento) + " "
                else:
                    self.HTML += self.getTab()
                    self.visit(elemento)
            else:
                t = elemento.value
                retorno += t + " "
                if (elemento.type=='ID'):
                    if not self.checkDecl(t):
                        self.vars[1].append(self.funcAct() +"-"+t)
                        self.HTML += "<span class='naoDeclaracao'> "+t+" </span>"
                    else:
                        self.setVar(t,'usada',True)
                    self.HTML += "<span class='code' id ='"+ str(self.funcAct()) + "-" + t + "'>" + t + " </span> <br>"
                elif (elemento.type=='SE'):
                    self.pushEc("if")
                    se = True
                    self.HTML += "<span id='"+self.ecAct()+"' class='ciclo'> "+t+" </span>"
                
                elif (elemento.type=='CASO'):
                    self.pushEc("case")
                    self.HTML += "<span id='"+self.ecAct()+"' class='ciclo'> "+t+" </span>"
                    
                elif (elemento.type=='END'):
                    self.HTML +=self.getTab()[:-1]+ "<span class='ciclo'> "+t+" </span> <br> <br>"

                elif (elemento.type == 'COMENTARIO'):
                    c +=1
                    comentario = elemento.value
                    self.HTML += self.getTab() +"<span class='code'> "+comentario+" </span> <br>"
        if se: 
            # pop do then ou do else no SDG
            self.sdgFunc.pop()
            # pop do if no SDG
            self.sdgFunc.pop()
            # instrucao de saida do if
            self.instC += 1
            ex = str(self.instC)+": SAIR_SE"
            self.cfg+= '"'+self.cfgAnt + '" -> "' + ex + '"\n'
            if senao:
                self.cfg+= '"'+ant + '" -> "' + ex + '"\n'
            else:
                self.cfg+= '"'+inicioIF + '" -> "' + ex + '"\n'
            self.cfgAnt = ex
            retorno += "}"
            self.HTML += self.getTab()[:-1]+ "<span class='code'> } </span> <br> <br>"
        
        if len(tree.children) == 2:
            print("Selecao "+ self.ecAct()+" vazia.")
        elif len(tree.children) == 3+c:
            v = self.getEcVal(self.eC , self.ecStack)
            if type(v)==dict and len(v.keys())==1 and 'if' in list(v.keys())[0]:
                print("Selecao "+ self.ecAct()+" é IF com IF aninhado e de possivel junção.")
                self.HTML = self.HTML.replace("id='"+self.ecAct()+"' class='ciclo'", "id='"+self.ecAct()+"' class='ciclo juncao'")
            else:
                print(v)
        self.popEc()
        return retorno

    def senao(self,tree):
        self.HTML += self.getTab()[-1]
        self.HTML += "<span class='code'> }</span>"
        newIt = str(self.instC)+": SENAO"
        self.cfg+= '"'+self.cfgAnt + '" -> "' + newIt + '"\n'
        self.cfgAnt = newIt
        for elemento in tree.children:
            if (type(elemento)==Tree):
                self.HTML += self.getTab()
                self.visit(elemento)
            else:
                t = elemento.value
                if (elemento.type=='SENAO'):
                    self.HTML += "<span class='ciclo'> "+t+" </span>"
                    self.HTML += "<span class='code'> { </span> <br> <br>"
                elif (elemento.type == 'COMENTARIO'):
                    c +=1
                    comentario = elemento.value
                    self.HTML += self.getTab() +"<span class='code'> "+comentario+" </span> <br>"
        
    def repeticao(self, tree):
        retorno = ""
        inicioCiclo = ""
        inicioDoWhile=""
        enquanto = False
        fazer = False
        repetir = False
        ate = False
        endAte = False
        para = False
        for elemento in tree.children:
            if (type(elemento) == Tree):
                if (elemento.data == 'comp'):
                    if(enquanto):
                        retorno += self.visit(elemento) + " "
                        self.cfg += '"'+ self.cfgAnt + '" -> "' + str(self.instC) + ': ' + retorno + '"\n'
                        self.cfg += '"'+ str(self.instC) + ": " + re.sub("\n", "", retorno) + '" [shape=diamond]\n'
                        self.cfgAnt = str(self.instC) + ": " + retorno
                        self.sdg += self.getSDGFunc()+' -> "'+self.cfgAnt+'"\n'
                        inicioCiclo = self.cfgAnt
                        self.sdgFunc.append(self.cfgAnt)
                        enquanto = False
                    if(ate):
                        #print(inicioDoWhile)
                        retorno = self.visit(elemento)
                        #print(retorno)
                        n = str(self.instC)+": ATE " + re.sub("\n", "", retorno)
                        self.cfg += '"'+ self.cfgAnt + '" -> "' + n + '"\n'
                        self.cfg += '"'+ n + '" -> "' + re.sub("\n", "", inicioDoWhile) + '"\n'
                        self.cfg += '"'+ n + '" [shape=diamond]\n'
                        self.cfgAnt = n
                        # id [label="Texto"]
                        self.sdg += self.getSDGFunc()+' [label="'+self.getSDGFunc().split('"')[1]+': repetir ... ate '+re.sub("\n", "", retorno)+'"]\n'
                        ate = False
                        endAte = True
                elif(elemento.data == 'componente'):
                    if(repetir):
                        retorno  = re.sub('\n','',self.visit(elemento))
                        inicioDoWhile = retorno
                        self.cfgAnt = retorno
                        repetir = False
                    else:
                        self.visit(elemento)
                elif (elemento.data == 'interv'):
                    if(para):
                        retorno += self.visit(elemento) + " "
                        self.cfg += '"'+ self.cfgAnt + '" -> "' + str(self.instC) + ': ' + retorno + '"\n'
                        self.cfg += '"'+ str(self.instC) + ": " + retorno + '" [shape=diamond]\n'
                        self.cfgAnt = str(self.instC) + ": " + retorno
                        self.sdg += self.getSDGFunc()+' -> "'+self.cfgAnt+'"\n'
                        inicioCiclo = self.cfgAnt
                        self.sdgFunc.append(self.cfgAnt)
            else:
                id = elemento.value
                retorno += id + " "
                eA = False
                if (elemento.type=='ENQ'):
                    enquanto = True
                    eA = True
                    self.pushEc("do")
                elif (elemento.type == 'REPETIR'):
                    repI = str(self.instC)
                    self.sdg += self.getSDGFunc()+' -> "'+repI+'"\n'
                    self.sdgFunc.append(repI)
                    repetir = True
                    self.pushEc("while")
                elif (elemento.type == 'PARA'):
                    para = True
                    eA = True
                    self.pushEc("for")
                elif (elemento.type == 'FAZER'):
                    fazer = True
                elif (elemento.type == 'ATE'):
                    ate = True
                    eA = True
                    self.HTML += self.getTab()[:-1]
                elif (elemento.type=='END'):
                    if(endAte):
                        endAte = False
                    else:
                        self.cfg += '"'+self.cfgAnt + '" -> "' + inicioCiclo + '"\n'
                        self.cfgAnt = inicioCiclo
                        self.HTML += self.getTab()[:-1]

                self.HTML += "<span id='"+self.ecAct()+"' class='ciclo'> "+id+" </span>"
                if not eA:
                    self.HTML += "<br> <br>"
        self.popEc()
        self.sdgFunc.pop()
        return retorno
                
    def retorno(self, tree):
        retorno = str(self.instC) +": " 
        self.instC += 1
        self.HTML += self.getTab()
        for elemento in tree.children:
            if (type(elemento) == Tree):
                retorno += self.visit(elemento) + " "
            else:
                id = elemento.value
                retorno += id + " "
                if (elemento.type =='RET'):
                    self.HTML += "<span class='retornos'> "+id+" </span>"
                elif (elemento.type =='PVIR'):
                    self.HTML += "<span class='code'> "+id+" </span> <br> <br>"
        self.cfg += "\""+ self.cfgAnt + "\" -> \"" + retorno + "\"\n"
        f = self.funcAct() if self.funcAct() != None else "GLOBAL"
        self.cfg += "\""+ retorno + "\" -> \"" + "Exit_"+f + "\"\n"
        self.sdg+= self.getSDGFunc()+' -> "'+retorno+'"\n'
        self.cfgAnt = ''
        return retorno+"\n"
                
    def comp(self,tree):
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento)==Tree):
                t = self.visit(elemento)
                retorno += t + " "
                if (elemento.data == 'sinalcomp'):
                    self.HTML += "<span class='code'> "+t+" </span>"
            else:
                id = elemento.value
                retorno += "!"+id + " "
                if not self.checkDecl(id):
#                    print("Variavel "+id+" não declarada (2)")
                    self.vars[1].append(str(self.funcAct()) +"-"+id)
                    self.HTML += "<span class='naoDeclaracao'>!"+id+" </span>"
                else:
                    self.setVar(id,'usada',True)
                    self.HTML += "<span class='code'>!"+id+" </span>"
        return retorno
                        
    def sinalcomp(self, tree):
        for elemento in tree.children:
            return elemento.value

    def caso(self,tree):
        retorno = "" 
        self.HTML += self.getTab()
        for elemento in tree.children:
            if (type(elemento) == Tree):
                retorno += self.visit(elemento) + " "
                if (elemento.data == 'elemcomp'):
                    retorno += ": {" + " "
                    self.HTML += "<span class='code'> : { </span> <br> <br>"
        self.HTML += self.getTab()[:-1] +"<span class='code'> } </span> <br> <br>"
        return retorno + " }"            
        
    def interv(self, tree):
        retorno = "[" + " "
        first = True
        self.HTML += "<span class='code'> [ </span>"
        for elemento in tree.children:
            if first:
                first = False
            else:
                self.HTML += "<span class='code'>, </span>"
            self.HTML += "<span class='code'> " + elemento.value + " </span>"
            retorno += elemento.value + " "
        self.HTML += "<span class='code'> ] </span>"
        return retorno + "]"
        
    def elemcomp(self,tree):
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento)==Tree):
                retorno += self.visit(elemento) + " "
            else:
                if (elemento.type=='ID'):
                    id = elemento.value
                    retorno += id + " "
                    if not self.checkDecl(id):
#                        print("Variavel "+id+" não declarada (2)")
                        self.vars[1].append(str(self.funcAct()) +"-"+id)
                        self.HTML += "<span class='naoDeclaracao'> " + id + " </span>"
                    else:
                        if self.inFuncao():
                            for x in self.variaveis[self.funcAct()]:
                                if x['nome'] == id:
                                    # colocar a variavel como usada
                                    self.setVar(id,'usada',True)
                                    if x['atribuicao'] == False:
#                                        print("Variavel "+id+" não inicializada (4)")
                                        self.vars[3].append(str(self.funcAct()) +"-"+id)
                                        self.HTML += "<span class='naoInicializada'> " + id + " </span>"
                                    else:
                                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'> " + id + " </span>"
                        else:
                            for x in self.variaveis['GLOBAL']:
                                if x['nome'] == id:
                                    self.setVar(id,'usada',True)
                                    if x['atribuicao'] == False:
#                                        print("Variavel "+id+" não inicializada (4)")
                                        self.vars[3].append(str(self.funcAct()) +"-"+id)
                                        self.HTML += "<span class='naoInicializada'> " + id + " </span>"
                                    else:
                                        self.HTML += "<span class='code' id ='"+str(self.funcAct()) + "-" + id +"'> " + id + " </span>"
                
                elif (elemento.type=='NUM'):
                    num = elemento.value
                    retorno += num + " "
                    self.HTML += "<span class='code'> " + num + " </span>"

                elif (elemento.type == 'STR'):
                    t = elemento.value
                    t = t.replace('"',r'\"')
                    retorno += t + " "
                    self.HTML += "<span class='code'> " + t + " </span>"
        
        return retorno
        
    def array(self,tree):
        retorno = "[" + " "
        self.HTML += "<span class='code'> [ </span>"
        for elemento in tree.children:
            if (type(elemento)==Tree):
                retorno += self.visit(elemento) + " "
            else :
                if (elemento.type=='VIR'):
                    self.HTML += "<span class='code'>, </span>"
                    retorno += ", " + " "
        self.HTML += "<span class='code'> ] </span>"
        return retorno + "]"
        
    def tuplo(self,tree):
        retorno = "(" + " "
        self.HTML += "<span class='code'> ( </span>"
        for elemento in tree.children:
            if (type(elemento)==Tree):
                retorno += self.visit(elemento)
            else :
                if (elemento.type=='VIR'):
                    retorno += ", " + " "
                    self.HTML += "<span class='code'>, </span>"
        self.HTML += "<span class='code'> ) </span>"
        return retorno + ")"
    
    def lista(self,tree):
        retorno = "" 
        first = True
        for elemento in tree.children:
            if (type(elemento)==Tree):
                retorno += self.visit(elemento) + " "
                if first:
                    self.HTML += "<span class='code'> -> </span>"
                    retorno += " -> " + " "
                    first = False
        return retorno
    
    def bool(self,tree):
        retorno = "" 
        for elemento in tree.children:
            if (type(elemento)==Tree):
                retorno += self.visit(elemento) + " "
            else:
                if(elemento.type == 'TRUE'):
                    retorno += "true" + " "
                    self.HTML += "<span class='code'> true </span>"
                elif (elemento.type == 'FALSE'):
                    retorno += "false" + " "
                    self.HTML += "<span class='code'> false </span>"
        return retorno
        
f = open('testeSDG.txt', 'r')
#f = open('linguagem2.txt', 'r')
frase = f.read()
f.close()

p = Lark(grammar)
p = Lark(grammar)
tree = p.parse(frase)
data = MyInterpreter().visit(tree)
