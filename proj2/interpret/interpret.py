#!/usr/bin/env python3

"""
IPPcode20 language interpret
 Vojtech Jurka (xjurka08)
"""

import sys
import xml.etree.ElementTree as ET
import re

#hlavni funkce
def main():

    cesta = zpracujArgumenty()

	# otevreni input souboru
    try:
        tree = ET.ElementTree(file=cesta)
    except OSError:
        errorExit(11, "Chyba pri otevirani souboru.")
    except ET.ParseError:
        errorExit(31, "Chybny syntax XML.")


    root = tree.getroot()

	# zpracuj instrukce
    zpracujInstrukce(root)
	
	# uspesne zakonceni
    sys.exit(0)

def zpracujInstrukce(root):
    
    #kontrola korene
    if root.tag != "program":
        errorExit(32, "Neocekavana struktura XML.")
    
    
    if root.items()[0] != ('language', 'IPPcode20'):
        errorExit(32, "Neocekavana struktura XML.")

    if len(root.keys()) == 2:
        if (root.keys()[1] != "name") and (root.keys()[1] != "description"):
             errorExit(32, "Neocekavana struktura XML.")
    
    if len(root.keys()) == 3:
        if (not("name" in root.keys())) or (not("description" in root.keys())):
            errorExit(32, "Neocekavana struktura XML.")
        
    if len(root.keys()) > 3:
        errorExit(32, "Neocekavana struktura XML.")
    
        
    
    #ulozeni vsech elementu v koreni do seznamu
    instrList = root.findall("./")

    if len(instrList) == 0:
        #program je prazdny, ma jen hlavicku -> uspesne zakonceni
        sys.exit(0)

    orderList = [] #seznam order stributu instrukci

    #kontrola elementu a naplneni seznamu order
    for e in instrList:
        if e.tag != "instruction":
            errorExit(32, "Neocekavana struktura XML.")
        if e.keys() != ['order', 'opcode']:
            errorExit(32, "Neocekavana struktura XML.")
        
        order = e.get("order")
        if order.isnumeric() == False:
             errorExit(32, "Neocekavana struktura XML.")
        
        orderList.append(int(order))

    #kontrola order
    orderList.sort()

    if orderList[0] < 1:
        errorExit(32, "Neocekavana struktura XML.")
    
    if len(orderList) != len(set(orderList)):           #kontrola duplicity
        errorExit(32, "Neocekavana struktura XML.")

    #zpracovani labelu v celem programu
    slovnikLabelu = najdiLabely(instrList)

    #kontrola syntaxe instrukci podle opcode
    checkSyntax(instrList)

    #postupne vykonavani instrukci
    vykonejInstrukce(instrList, orderList, slovnikLabelu)

def vykonejInstrukce(instrList, orderList, slovnikLabelu):
    
    global typeFlag
    slovnikInstrukci = {}
    #naplneni slovniku instrukci
    for i in instrList:
        slovnikInstrukci[i.get("order")] = i
    
    counter = 0
    order = orderList[counter]
    #slovniky a stack ramcu pro uchovavani nazvu a hodnot promennych
    slovnikTF = {}
    slovnikLF = {}
    slovnikGF = {}

    
    mujstack = []
    stackLF = []
    callstack = []
    TframeCreated = False
    LframeCreated = False #zasobnik LF je prazdny
    endCall = False #flag pro pripad kdy je volani funkce jako posledni instrukce
    typeFlag = False #flag pro pripad, kdy je volana instrukce type, kdy lze cist z prazdne promenne


    #postupne cykleni instrukcemi podle poradi v orderListu
    while counter < len(orderList):

        instruction = slovnikInstrukci[str(order)]
        opcode = instruction.get("opcode").upper()
        #<var> <symb>
        if opcode == "MOVE":
            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")
            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            
            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2
        
        elif opcode == "CREATEFRAME":
            slovnikTF.clear()
            TframeCreated = True

        elif opcode == "PUSHFRAME":
            if TframeCreated == False:
                errorExit(55, "Prazdny zasobnik ramcu.")
            
            stackLF.append(slovnikTF.copy())
            LframeCreated = True

            slovnikLF = slovnikTF.copy()

            TframeCreated = False

        elif opcode == "POPFRAME":
            if LframeCreated == False:
                errorExit(55, "Prazdny zasobnik ramcu.")
            
            slovnikTF = stackLF.pop()
            TframeCreated = True

            if len(stackLF) == 0:
                LframeCreated = False
                slovnikLF.clear()
            else:
                slovnikLF = stackLF[-1].copy()
        #<var>
        elif opcode == "DEFVAR":
            
            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")
            
            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == True:
                    errorExit(52, "Opakovana definice promenne.")
                slovnikGF[nazev] = prazdna()

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == True:
                    errorExit(52, "Opakovana definice promenne.")
                slovnikLF[nazev] = prazdna()

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == True:
                    errorExit(52, "Opakovana definice promenne.")
                slovnikTF[nazev] = prazdna()

        elif opcode == "CALL":
            
            if counter+1 == len(orderList): #pokud je toto posledni instrukce
                endCall = True
            else:
                callstack.append(orderList[counter+1])

            label = instruction.findtext("arg1")
            if label == None:
                errorExit(32, "Neocekavana struktura XML.")

            if not(label in slovnikLabelu):
                errorExit(52, "Navesti neni definovane.")


            order = int(slovnikLabelu[label]) #nacteni cisla order instrukce
            counter = orderList.index(order) #index orderu v orderlistu
            continue

        elif opcode == "RETURN":

            if endCall == True: #vracim se z funkce volane na konci behu programu, takze koncim program
                counter = len(orderList)
            else: #neni na konci programu, pokracuju tam kam me vrati callstack
                if len(callstack) == 0:
                    errorExit(56, "Prazdny callstack.")
                order = callstack.pop()
                counter = orderList.index(order)

            continue

        elif opcode == "PUSHS":
            arg1 = prectiHodnotu(instruction.find("arg1"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            
            mujstack.append(arg1)

        elif opcode == "POPS":

            if len(mujstack) == 0:
                errorExit(56, "Prazdny callstack.")

            hodnota = mujstack.pop()
            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = hodnota

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = hodnota

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = hodnota

        elif opcode == "ADD":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, int) == False) or (isinstance(arg3, int) == False):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 + arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 + arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 + arg3

        elif opcode == "SUB":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, int) == False) or (isinstance(arg3, int) == False):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 - arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 - arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 - arg3

        elif opcode == "MUL":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, int) == False) or (isinstance(arg3, int) == False):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 * arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 * arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 * arg3

        elif opcode == "IDIV":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, int) == False) or (isinstance(arg3, int) == False):
                errorExit(53, "Spatne typy operandu.")

            if arg3 == 0:
                errorExit(57, "Deleni nulou.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 // arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 // arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 // arg3

        elif opcode == "LT":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (arg2 == None or (arg3 == None)):
                errorExit(53, "Spatne typy operandu.")

            if type(arg2) != type(arg3):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 < arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 < arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 < arg3

        elif opcode == "GT":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (arg2 == None or (arg3 == None)):
                errorExit(53, "Spatne typy operandu.")

            if type(arg2) != type(arg3):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 > arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 > arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 > arg3
                
        elif opcode == "EQ":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (type(arg2) != type(arg3)) and (arg2 != None) and (arg3 != None):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 == arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 == arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 == arg3

        elif opcode == "AND":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, bool) == False) or (isinstance(arg3, bool) == False):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 and arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 and arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 and arg3

        elif opcode == "OR":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, bool) == False) or (isinstance(arg3, bool) == False):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 or arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 or arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 or arg3

        elif opcode == "NOT":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, bool) == False):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = not arg2

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = not arg2

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = not arg2

        elif opcode == "INT2CHAR":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, int) == False):
                errorExit(53, "Spatne typy operandu.")
            

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                try:
                    slovnikGF[nazev] = chr(arg2)
                except ValueError:
                    errorExit(58, "Cislo je mimo ASCII range.")
                

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                try:
                    slovnikLF[nazev] = chr(arg2)
                except ValueError:
                    errorExit(58, "Cislo je mimo ASCII range.")

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                try:
                    slovnikTF[nazev] = chr(arg2)
                except ValueError:
                    errorExit(58, "Cislo je mimo ASCII range.")
            
        elif opcode == "STRI2INT":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, str) == False) or (isinstance(arg3, int) == False):
                errorExit(53, "Spatne typy operandu.")

            if (arg3 >= len(arg2)) or (arg3 < 0):
                errorExit(58, "Cislo je mimo index range stringu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = ord(arg2[arg3])

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = ord(arg2[arg3])

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = ord(arg2[arg3])

        elif opcode == "READ":

            arg2 = instruction.findtext("arg2")

            try:
                hodnota = input()
            except EOFError:
                hodnota = None

            if hodnota != None:
                if arg2 == "int":
                    try:
                        hodnota_f = int(hodnota)
                    except ValueError:
                        hodnota_f = None
                    if str(hodnota_f) != hodnota:
                        hodnota_f = None
                elif arg2 == "string":
                    hodnota_f = hodnota
                elif arg2 == "bool":
                    if hodnota.lower() == "true":
                        hodnota_f = True
                    else:
                        hodnota_f = False

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                
                slovnikGF[nazev] = hodnota_f
                
                

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                
                slovnikLF[nazev] = hodnota_f
                

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")

                slovnikTF[nazev] = hodnota_f
        
        elif opcode == "WRITE":

            arg1 = prectiHodnotu(instruction.find("arg1"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            
            if isinstance(arg1, bool):
                if arg1:
                    print("true", end='')
                else:
                    print("false", end='')
            elif (isinstance(arg1, str)) or (isinstance(arg1, int)):
                print(arg1, end='')
            
            elif arg1 == None:
                print('', end='')

        elif opcode == "CONCAT":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, str) == False) or (isinstance(arg3, str) == False):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2 + arg3

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2 + arg3

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2 + arg3

        elif opcode == "STRLEN":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, str) == False):
                errorExit(53, "Spatne typy operandu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = len(arg2)

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = len(arg2)

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = len(arg2)

        elif opcode == "GETCHAR":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(arg2, str) == False) or (isinstance(arg3, int) == False):
                errorExit(53, "Spatne typy operandu.")
            
            if len(arg2) == 0:
                errorExit(58, "Predan prazdny string.")
            
            if (arg3 < 0) or (arg3 > len(arg2)):
                errorExit(58, "Cislo je mimo index range stringu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = arg2[arg3]

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = arg2[arg3]

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = arg2[arg3]

        elif opcode == "SETCHAR":

            
            hodnota = prectiHodnotu(instruction.find("arg1"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (isinstance(hodnota, str) == False) or (isinstance(arg2, int) == False) or (isinstance(arg3, str) == False):
                errorExit(53, "Spatne typy operandu.")
            
            if len(arg3) == 0:
                errorExit(58, "Predan prazdny string.")
            
            if (arg2 < 0) or (arg2 > len(hodnota)):
                errorExit(58, "Cislo je mimo index range stringu.")

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev][arg2] = arg3[0]

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev][arg2] = arg3[0]
            
            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev][arg2] = arg3[0]

        elif opcode == "TYPE":

            typeFlag = True
            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            typeFlag = False
            if isinstance(arg2, str):
                hodnota = "string"
            elif isinstance(arg2, bool):
                hodnota = "bool"
            elif isinstance(arg2, int):
                hodnota = "int"
            elif arg2 == None:
                hodnota = "nil"
            elif isinstance(arg2, prazdna):
                hodnota = ""

            arg1 = instruction.findtext("arg1")
            if arg1 == None:
                errorExit(32, "Neocekavana struktura XML.")

            nazev = arg1[3:]
            if arg1[:3] == "GF@":

                if frameCheck(slovnikGF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikGF[nazev] = hodnota

            elif arg1[:3] == "LF@":
            
                if LframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")  
                if frameCheck(slovnikLF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikLF[nazev] = hodnota

            elif arg1[:3] == "TF@":

                if TframeCreated == False:
                    errorExit(55, "Prazdny zasobnik ramcu.")            
                if frameCheck(slovnikTF, nazev ) == False:
                    errorExit(54, "Pristup k neexistujici promenne.")
                slovnikTF[nazev] = hodnota

        elif opcode == "LABEL":
            pass

        elif opcode == "JUMP":

            label = instruction.findtext("arg1")
            if label == None:
                errorExit(32, "Neocekavana struktura XML.")

            if not(label in slovnikLabelu):
                errorExit(52, "Navesti neni definovane.")


            order = int(slovnikLabelu[label]) #nacteni cisla order instrukce
            counter = orderList.index(order) #index orderu v orderlistu
            continue

        elif opcode == "JUMPIFEQ":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (type(arg2) != type(arg3)) and (arg2 != None) and (arg3 != None):
                errorExit(53, "Spatne typy operandu.")

            label = instruction.findtext("arg1")
            if label == None:
                errorExit(32, "Neocekavana struktura XML.")

            if not(label in slovnikLabelu):
                errorExit(52, "Navesti neni definovane.")

            if arg2 == arg3:
                order = int(slovnikLabelu[label]) #nacteni cisla order instrukce
                counter = orderList.index(order) #index orderu v orderlistu
                continue
            
        elif opcode == "JUMPIFNEQ":

            arg2 = prectiHodnotu(instruction.find("arg2"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            arg3 = prectiHodnotu(instruction.find("arg3"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)

            if (type(arg2) != type(arg3)) and (arg2 != None) and (arg3 != None):
                errorExit(53, "Spatne typy operandu.")

            label = instruction.findtext("arg1")
            if label == None:
                errorExit(32, "Neocekavana struktura XML.")

            if not(label in slovnikLabelu):
                errorExit(52, "Navesti neni definovane.")

            if arg2 != arg3:
                order = int(slovnikLabelu[label]) #nacteni cisla order instrukce
                counter = orderList.index(order) #index orderu v orderlistu
                continue

        elif opcode == "EXIT":

            arg1 = prectiHodnotu(instruction.find("arg1"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            

            if isinstance(arg1, int) == False:
                errorExit(53, "Spatne typy operandu.")

            if (arg1 < 0) or (arg1 > 49):
                errorExit(57, "Spatna hodnoda navratoveho kodu.")

            sys.exit(arg1)
        
        elif opcode == "DPRINT":

            arg1 = prectiHodnotu(instruction.find("arg1"), slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated)
            
            print(arg1, file=sys.stderr)

        elif opcode == "BREAK":

            print("ORDER: {0}".format(order), file=sys.stderr)
        
        

        counter += 1
        if counter < len(orderList):
            order = orderList[counter]
        

#zkontroluje, jestli je dana promenna v danem ramci deklarovana
def frameCheck(slovnik, nazev):
    if nazev in slovnik:
        return True
    else:
        return False

#precte hodnotu argumentu a vlozi ji do promenne
def prectiHodnotu(argument, slovnikTF, slovnikLF, slovnikGF, TframeCreated, LframeCreated):
    global typeFlag
    global regex #globani promenna regularniho vyrazu
    if argument == None:
        errorExit(32, "Neocekavana struktura XML.")
    if argument.get("type") == "var":

        
        nazev = argument.text[3:]
        if argument.text[:3] == "GF@":

            if frameCheck(slovnikGF, nazev ) == False:
                errorExit(54, "Pristup k neexistujici promenne.")
            if typeFlag == False:
                if isinstance(slovnikGF[nazev], prazdna):
                    errorExit(56, "Chybejici hodnota promenne.")

            return slovnikGF[nazev]
        
        elif argument.text[:3] == "LF@":
            
            if LframeCreated == False:
                errorExit(55, "Prazdny zasobnik ramcu.")  
            if frameCheck(slovnikLF, nazev ) == False:
                errorExit(54, "Pristup k neexistujici promenne.")
            if typeFlag == False:
                if isinstance(slovnikLF[nazev], prazdna):
                    errorExit(56, "Chybejici hodnota promenne.")
            
            return slovnikLF[nazev]

        elif argument.text[:3] == "TF@":

            if TframeCreated == False:
                errorExit(55, "Prazdny zasobnik ramcu.")            
            if frameCheck(slovnikTF, nazev ) == False:
                errorExit(54, "Pristup k neexistujici promenne.")
            if typeFlag == False:
                if isinstance(slovnikTF[nazev], prazdna):
                    errorExit(56, "Chybejici hodnota promenne.")
            
            return slovnikTF[nazev]
    
    elif argument.get("type") == "int":
        try:
            hodnota = int(argument.text)
        except ValueError:
            errorExit(32, "Spatne zadany int.")
        return hodnota
    elif argument.get("type") == "string":
        text = argument.text
        text = regex.sub(replace, text) #nahrazeni decimalni escape sekvence znakem
        return text
    elif argument.get("type") == "bool":
        return argument.text == "true"
    elif argument.get("type") == "nil":
        return None


def checkSyntax(instrList):
    #prochazi seznam se vsemi instrukcemi a kazdou kontroluje na syntax podle jejiho opcode

    for i in instrList:

        opcode = i.get("opcode").upper()


        #bez argumentu
        if (opcode == "CREATEFRAME") or (opcode == "PUSHFRAME") or (opcode == "POPFRAME") or (opcode == "RETURN") or (opcode == "BREAK"):
            if len(i.findall("./")) != 0:
                errorExit(32, "Spatny pocet argumentu instrukce.")
            continue
        #<var>
        elif (opcode == "DEFVAR") or (opcode == "POPS"):
            if len(i.findall("./")) != 1:
                errorExit(32, "Spatny pocet argumentu instrukce.")
            continue
        #<label>
        elif (opcode == "CALL") or (opcode == "JUMP") or (opcode == "LABEL"):
            if len(i.findall("./")) != 1:
                errorExit(32, "Spatny pocet argumentu instrukce.")
            continue
        #<symb>
        elif (opcode == "PUSHS") or (opcode == "WRITE") or (opcode == "DPRINT") or (opcode == "EXIT"):
            if len(i.findall("./")) != 1:
                errorExit(32, "Spatny pocet argumentu instrukce.")
            continue
        #<var> <symb>
        elif (opcode == "MOVE") or (opcode == "NOT") or (opcode == "INT2CHAR") or (opcode == "STRLEN") or (opcode == "TYPE"):
            if len(i.findall("./")) != 2:
                errorExit(32, "Spatny pocet argumentu instrukce.")
            continue
        #<label> <symb> <symb>
        elif (opcode == "JUMPIFEQ") or (opcode == "JUMPIFNEQ"):
            if len(i.findall("./")) != 3:
                errorExit(32, "Spatny pocet argumentu instrukce.")
            continue
        #<var> <symb> <symb>
        elif (opcode == "ADD") or (opcode == "SUB") or (opcode == "MUL") or (opcode == "IDIV") or (opcode == "LT") or (opcode == "GT") or (opcode == "EQ") or (opcode == "AND") or (opcode == "OR") or (opcode == "STRI2INT") or (opcode == "CONCAT") or (opcode == "GETCHAR") or (opcode == "SETCHAR"):
            if len(i.findall("./")) != 3:
                errorExit(32, "Spatny pocet argumentu instrukce.")
            continue
        #<var> <type>
        elif (opcode == "READ"):
            if len(i.findall("./")) != 2:
                errorExit(32, "Spatny pocet argumentu instrukce.")
            continue
        else:
            errorExit(32, "Spatne zapsany opcode.")


def najdiLabely(instrList):
    
    slovnikLabelu = {}
    for i in instrList:
        if i.get("opcode").upper() == "LABEL":
            name = i.find("arg1").text

            if name == None:
                errorExit(32, "Neocekavana struktura XML.")

            if name in slovnikLabelu:
                errorExit(52, "Duplicitni label.")
            
            slovnikLabelu[name] = i.get("order")
    
    return slovnikLabelu


def zpracujArgumenty():
    
    global my_stdin

    if len(sys.argv) < 2:
	    errorExit(10, "Nespravny pocet argumentu. Pouzij argument --help.")

    if sys.argv[1] == "--help":
        if len(sys.argv) > 2:
            errorExit(10, "Spatna kombinace argumentu. Pouzij argument --help.")
        print("Program interpretuje kod v jazyku IPPcode20 zpracovany do XML formatu.")
        print("Pouziti:")
        print("python3.8 interpret.py --source=<source file> --input=<input_file> (alespon jeden z techto argumentu musi byt specifikovan)")
        sys.exit(0)
    
    elif sys.argv[1][:9] == "--source=":

        if len(sys.argv) > 2:
            if sys.argv[2][:8] == "--input=":

                my_stdin = sys.stdin
                try:
                    sys.stdin = open(sys.argv[2][8:])
                except OSError:
                    errorExit(11, "Chyba pri otevirani souboru.")
            
            else:
                errorExit(10, "Nespravne zadane argumenty. Pouzij argument --help.")

        return sys.argv[1][9:]

    elif sys.argv[1][:8] == "--input=":

        my_stdin = sys.stdin
        try:
            sys.stdin = open(sys.argv[1][8:])
        except OSError:
            errorExit(11, "Chyba pri otevirani souboru.")
        
        if len(sys.argv) > 2:
            if sys.argv[2][:9] == "--source=":
                return sys.argv[2][9:]
            else:
                errorExit(10, "Nespravne zadane argumenty. Pouzij argument --help.")
        else:
            return sys.stdin


def errorExit(kod, zprava):
    print("ERROR: {0}".format(zprava), file=sys.stderr)
    sys.exit(kod)


#objekt prazdne promenne
class prazdna:
    pass

#pomocna funkce pro konverzi escape sekvenci
def replace(match):
    return chr(int(match.group(1)))

#regularni vyraz pro nalezani escape sekvenci v textu
regex = re.compile(r"\\(\d{1,3})")

main()
