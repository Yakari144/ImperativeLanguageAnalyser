import re


anterior = ""
fAct = []
lastF = {}
ant = ""
chamada = ""
outSel = 0
outRep = 0

def normaliza(l):
    l = l.strip()
    l = re.sub(r'\s+', ' ', l)
    l = l.replace('"',r'\"')
    return l

def isRep(str):
    if "para" in str or "repetir" in str or "enquanto" in str:
        return True
    return False

def isSel(str):
    if "se" in str or "caso" in str:
        return True
    return False

def popFunc():
    global fAct, outRep, outSel
    if fAct != []:
        if "enquanto" in str:
            outRep = 1
        elif "repetir" in str:
            outRep = 2
        elif "para" in str:
            outRep = 3
        elif "se" in str:
            outSel = 1
        elif "caso" in str:
            outSel = 2

    fAct.pop()

def toCNF():
    global anterior, fAct, lastF, ant, chamada
    fw = open("CFG.dot", "w")
    fw.write("digraph G {\n")
    fr = open("instrucoes", "r")
    for line in fr:
        line = normaliza(line)
        deffuncao = re.match(r'def \w+ ([a-z][a-zA-Z_0-9]*).*', line)
        funcao = re.match(r'([a-z][a-zA-Z_0-9]*)\s*\(.*?\).*', line)
        if line == "":
            continue
        elif saiuSe:

        elif deffuncao:
            fAct = deffuncao.group(1)
            ant = anterior
            anterior = "Entry_"+fAct
            lastF[fAct] = ""
            continue
        #elif funcao:
            #line = "Call_"+funcao.group(1)
            #fw.write("\""+anterior+"\"->\""+line+"\"\n")
            #fw.write("\""+line+"\"->\"Entry_"+funcao.group(1)+"\"\n")
            #anterior = lastF[funcao.group(1)]
            #continue
        elif line == "}":
            lastF[fAct] = anterior
            anterior = ant
            continue
        else:
            if anterior != "":

                fw.write("\""+anterior+"\"->\""+line+"\"\n")
            anterior = line
    fw.write("}")
        
toCNF()
