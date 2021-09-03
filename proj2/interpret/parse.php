<?php
    /*
	 * parse.php
	 * Autor: Vojtěch Jurka (xjurka08)
	 */


	// Nacitani argumentu
    nactiArgumenty();
    
    // Nactu prvni radek
    if(!$radek = fgets(STDIN))
    {
        error(11, "PARSER ERROR:Žádný vstup");
    }
    //komentare pred hlavickou
    do
    {
        preg_match('/^#.*/', $radek, $buff);
        if($buff == null)
        {
            break;
        }
    }
    while($radek= fgets(STDIN));

	$radek = strtolower(trim(preg_replace("/#.*$/", "", $radek, -1)));	// odstrani komentare, mezery a prevede text na lowercase
    if($radek != ".ippcode20")
    {
        error(21, "PARSER ERROR:Špatná hlavička");
    }

    // Generovani XML

    $dokument = new DomDocument("1.0", "UTF-8");
    $dokument->formatOutput = true;

    global $order;
	$order = 1;

    $program_element = $dokument->createElement("program");      //element program
    $program_element = $dokument->appendChild($program_element); //navazovani potomku
	//vytvoreni a navazani atributu
	$language_atribut = $dokument->createAttribute("language");
	$language_atribut->value = "IPPcode20";
    $program_element->appendChild($language_atribut);

    // nacitani vstupu

    while($radek= fgets(STDIN))
	{
        // pokud je to komentar, preskakuju
        preg_match('/^#.*/', $radek, $buff);
        if($buff != null)
        {
            continue;
        }

        // odstraneni komentare z konce radku
        preg_match('/(.*)(#.*$)/', $radek, $buff);
        if($buff != null)
        {
            $radek = $buff[1];
        }
		
		$instrukce = zpracujRadek($radek);	
	
		// element instrukce
		$instruction_element = $dokument->createElement("instruction");
		$program_element->appendChild($instruction_element);
		
		// atribut order
		$order_atribut = $dokument->createAttribute("order");
		$order_atribut->value = $order++;
		$instruction_element->appendChild($order_atribut);
		
		// atribut opcode
		$opCode_atribut = $dokument->createAttribute("opcode");
		$opCode_atribut->value = $instrukce[0];
		$instruction_element->appendChild($opCode_atribut);
		
		// elementy arg
		$argCount = $instrukce[1];
		for($i = 1; $i <= $argCount; $i++)
		{
			// element arg
			$arg_element = $dokument->createElement("arg".$i);	
			$instruction_element->appendChild($arg_element);
			
			// atribut typ
			$type_atribut = $dokument->createAttribute("type");
			$type_atribut->value = $instrukce[$i*2];
			$arg_element->appendChild($type_atribut);
			
			// obsah
			$arg_text = $dokument->createTextNode($instrukce[($i*2)+1]);
			$arg_element->appendChild($arg_text);
		}
    }
    
    // tisk XML a konec

    $dokument->save("php://stdout");
	exit(0);
    

    function zpracujRadek($radek)
    {
        $array = preg_split("/[[:blank:]]+/", trim($radek), 5, PREG_SPLIT_NO_EMPTY); // rozdelim podle mezer
        //vlozeni argc elementu na index 1
        array_splice( $array, 1, 0, 0 );

        //prevod opcode na uppercase
        $array[0] = strtoupper($array[0]);

        // vyber typu instrukce
        switch($array[0])
		{
            // bez argumentu
			case "CREATEFRAME":
			case "PUSHFRAME":
			case "POPFRAME":
			case "RETURN":
            case "BREAK":
                $array[1] = 0;
            break;
               
			// <var>
			case "DEFVAR":
			case "POPS":
                $array[1] = 1;
                
                //zpracovani <var>
                $array = zpracujVar($array);
                
			break;
				
			// <label>
			case "CALL":
			case "LABEL":
			case "JUMP":
                $array[1] = 1;
                $buff = $array[2];
                $array[2] = "label";
                $array[3] = $buff;
            break;
            
			// <symb>
			case "PUSHS":
			case "WRITE":
            case "DPRINT":
            case "EXIT":
                $array[1] = 1;
                
                $array = zpracujSymb(1, $array);
            
            break;

            // <var> <symb>
			case "MOVE":
			case "NOT":
			case "INT2CHAR":
			case "STRLEN":
			case "TYPE":
                $array[1] = 2;

                //zpracovani <var>
                $array = zpracujVar($array);
                // zpracovani <symb>
                $array = zpracujSymb(2, $array);

            break;
            
			// <label> <symb> <symb>
			case "JUMPIFEQ":
			case "JUMPIFNEQ":
                $array[1] = 3;
                
                //zpracovani <label>
                $buff = $array[2];
                array_splice( $array, 2, 0, "label");

                // zpracovani <symb>
                $array = zpracujSymb(2, $array);
                $array = zpracujSymb(3, $array);

			break;
			
			// <var> <symb> <symb>
			case "ADD":
			case "SUB":
			case "MUL":
			case "IDIV":
			case "LT":
			case "GT":
			case "EQ":
			case "AND":
			case "OR":
			case "STRI2INT":
			case "CONCAT":
			case "GETCHAR":
			case "SETCHAR":
                $array[1] = 3;
                
                //zpracovani <var>
                $array = zpracujVar($array);
                //zpracovani <symb>
                $array = zpracujSymb(2, $array);
                $array = zpracujSymb(3, $array);

                
			break;
			
			// <var> <type>
			case "READ":
                $array[1] = 2;
                
                //zpracovani <var>
                $array = zpracujVar($array);
                //zpracovani <type> 
                
                if($array[4] == ("int"||"string"||"bool"))
                {
                    $array[5] = $array[4];
                    $array[4] = "type";
                }
                else
                {
                    error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                }
            break;
            

			
			// Error
			default:
				error(22, "PARSER ERROR:Špatně zapsaná instrukce");
        }
        return $array;
    }


    function nactiArgumenty()
    {
        $options = array("help");
        
        $argumenty = getopt(null, $options);	
      
        // --help
        global $argc;

        if($argc > 1) // je pouzit nejaky argument
        {
            if(isset($argumenty["help"]))	// argument --help je pouzit
            {
                if($argc == 2)	// je to jediny argument
                {
                    fputs(STDOUT, "Tento skript načítá zdrojový kód v jazyce IPPcode20 ze standardního vstupu,\n");
                    fputs(STDOUT, "provede lexikální a syntaktickou analýzu a na standardní výstup vytiskne\n");
                    fputs(STDOUT, "XML reprezentaci programu.\n");
                    exit(0);
                }
                else
                    error(10, "Nalezeny nesprávné argumenty spolu s --help.");
            }
            else // --help neni pouzit
            {
                error(10, "Nalezeny nesprávné argumenty.");
            }
        }
        
    }

    function error($hodnota, $zprava)
	{
		fputs(STDERR, "$zprava\n");
		exit($hodnota);
    }
    //zpracuje argument <symb> v poli instrukce array podle toho, na kterem je poradi a vraci pole array
    function zpracujSymb($poradi, $array)
    {
        preg_match('/(LF|TF|GF|int|bool|string|nil)@(.*)/', $array[$poradi*2], $buff);
                
                if($buff == null)
                {
                    error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                }
                else
                {
                    switch($buff[1])
                    {
                        case "GF":
                        case "LF":
                        case "TF":
                            preg_match('/^[a-zA-Z0-9-_$&%*!?]*$/', $buff[2], $buff2);
                            if($buff2 == null)
                            {
                                error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                            }
                            else
                            {
                                array_splice( $array, $poradi*2, 0, "var");
                            }
                            
                        break;
                    
                        case "int":
                            preg_match('/^[0-9]*$/', $buff[2], $buff2);
                            if($buff2 == null)
                            {
                                error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                            }
                            else
                            {
                                array_splice( $array, $poradi*2, 0, "int");
                                $array[($poradi*2)+1] = $buff2[0];
                            }
                        break;

                        case "bool":
                            if($buff[2] == ("true" || "false"))
                            {
                                array_splice( $array, $poradi*2, 0, "bool");
                                $array[($poradi*2)+1] = $buff[2];
                            }
                            else
                            {
                                error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                            }
                        break;

                        case "string":
                            array_splice( $array, $poradi*2, 0, "string");
                            $array[($poradi*2)+1] = $buff[2];

                        break;

                        case "nil":
                            if($buff[2] == "nil")
                            {
                                array_splice( $array, $poradi*2, 0, "nil");
                                $array[($poradi*2)+1] = "nil";
                            }
                            else
                            {
                                error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                            }

                        break;

                        default:
                            error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                    }
                }
                return $array;
    }
    //zpracuje <var> argument, ktery je vzdy na prvnim miste
    function zpracujVar($array)
    {
                preg_match('/(.*)@(.*)/', $array[2], $buff);

                if($buff == null)
                {
                    error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                }
                else
                {
                    if($buff[1] == ("GF"||"LF"||"TF"))
                    {
                        preg_match('/^[a-zA-Z0-9-_$&%*!?]*$/', $buff[2], $buff2);
                        if($buff2 == null)
                        {
                            error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                        }
                        else
                        {
                            array_splice( $array, 2, 0, "var");
                        }
                    }
                    else
                    {
                        error(23, "PARSER ERROR:Špatně zapsaný operand instrukce");
                    }
                }
                return $array;
    }
?>