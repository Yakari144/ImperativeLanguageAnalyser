r'''
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