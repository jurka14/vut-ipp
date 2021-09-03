<?php

    /*
	 * test.php
	 * Autor: Vojtěch Jurka (xjurka08)
	 */



    //zpracovani parametru
    
    $slozkaTestu = "./";
    $recursive = false;
    $parse_only = false;
    $int_only = false;
    $parseCesta = "./parse.php";
    $interpretCesta = "./interpret.py";
    $jexamxmlCesta = "/pub/courses/ipp/jexamxml/jexamxml.jar";
    $total = 0;
    $total_proslo = 0;

    $options = array("help", "directory:", "recursive", "parse-script:", "int-script:", "parse_only", "int-only", "jexamxml:");

    $argumenty = getopt(null, $options);

    if(isset($argumenty["help"]))
    {
        if($argc == 2) //argument help musi byt pouzit samotny
        {
            print("Tento skript slouzi pro automaticke testovani postupne aplikace skriptu parse.php a interpret.py");
            exit(0);
        }
        else
        {
            error(10, "--help nesmi byt pouzit s ostatnimi argumenty");
        }
    }

    if(isset($argumenty["directory"]))
    {
        $slozkaTestu = $argumenty["directory"];
    }

    if(substr($slozkaTestu, -1) != "/")
    {
        $slozkaTestu = $slozkaTestu."/"; //adresa slozky konci vzdycky lomitkem
    }

    if(isset($argumenty["recursive"]))
    {
        $recursive = true;
    }

    if(isset($argumenty["parse-only"]))
    {
        if(isset($argumenty["int-only"]))
        {
            error(10, "Chybna kombinace parametru.");
        }
        if(isset($argumenty["int-script"]))
        {
            error(10, "Chybna kombinace parametru.");
        }
        $parse_only = true;
    }

    if(isset($argumenty["parse-script"]))
    {
        $parseCesta = $argumenty["parse-script"];
    }

    if(isset($argumenty["int-only"]))
    {
        if(isset($argumenty["parse-only"]))
        {
            error(10, "Chybna kombinace parametru.");
        }
        if(isset($argumenty["parse-script"]))
        {
            error(10, "Chybna kombinace parametru.");
        }
        $int_only = true;
    }

    if(isset($argumenty["int-script"]))
    {
        $interpretCesta = $argumenty["int-script"];
    }

    if(isset($argumenty["jexamxml"]))
    {
        $jexamxmlCesta = $argumenty["jexamxml"];
    }

    //zpracovani parametru dokonceno
    //samotna prace skriptu

    //prohledavani slozky s testy

    if(!file_exists($slozkaTestu))
    {
        error(11, "Chybejici slozka testu.");
    }

    $slozky = array();
    $vysledky = array();

    scan($slozkaTestu);

    
    //vypis html kodu s vysledky
    echo "<!DOCTYPE HTML>
    <html lang=\"cs\">
        <head>
            <meta charset=\"utf-8\"/>
            <style>
            </style>
            <title>IPP project test</title>
        </head>
        <body>
            <div class=\"container\">
                <h1>IPP projekt výsledek testů</h1>
    ";
    echo "      <h2> Celkem prošlo ".$total_proslo." z ".$total." testů.</h2>
    ";
    echo "      <table border=\"1\">
                    <tr>
                        <th>Složka</th>
                        <th>Prošlo</th> 
                        <th>Celkem</th>
                    </tr>
    ";
    foreach($slozky as $slozka)
    {
    echo "            <tr>
                        <td>".$slozka["jmeno"]."</td>
                        <td>".$slozka["proslo"]."</td> 
                        <td>".$slozka["celkem"]."</td>
                    </tr>
        ";
    }

    echo "      </table>
    ";
    echo "      <br><br>
                <table border=\"1\">
                    <tr>
                        <th>Složka</th>
                        <th>Název</th> 
                        <th>Výstup</th>
                        <th>Návratový kód</th>
                        <th>Výsledek</th>
                    </tr>
    ";
    foreach($vysledky as $vysledek)
    {
    echo "            <tr>
                        <td>".$vysledek["slozka"]."</td>
                        <td>".$vysledek["nazev"]."</td> 
                        <td>".$vysledek["out"]."</td>
                        <td>".$vysledek["rc"]."</td>
    ";

    if($vysledek["out"] == "prosel" && $vysledek["rc"] == "prosel")
    {
    echo "              <td bgcolor=\"green\">OK</td>
    ";
    }
    else
    {
    echo "              <td bgcolor=\"red\">BAD</td>
    ";
    }
    
    echo "            </tr>
    ";
    }
    echo "      </table>
            </div>
        </body>
    </html>
    ";

    
    
   

     
    function test($nazev, $slozkaTestu, $IDslozky)
    {
        //globalni promenne
        global $slozky, $vysledky;

        global $parse_only;
        global $int_only;
        global $parseCesta;
        global $interpretCesta;
        global $jexamxmlCesta;
        global $total_proslo;

        //vytvoreni chybejicich souboru

        $cesta = $slozkaTestu.$nazev;

        if(!file_exists($cesta.".out"))
        {
			$file = touch($cesta.".out");
			
            if($file == false)
            {
                error(12, "Nepodarilo se vytvorit soubor.");
            }
        }
        
        if(!file_exists($cesta.".in"))
        {
			$file = touch($cesta.".in");
			
            if($file == false)
            {
                error(12, "Nepodarilo se vytvorit soubor.");
            }
        }

        if(!file_exists($cesta.".rc"))
        {
			$file = fopen($cesta.".rc", "w");
			
            if($file == false)
            {
                error(12, "Nepodarilo se vytvorit soubor.");
            }

            fwrite($file, "0");
            fclose($file);
        }

        if($parse_only == true)
        {
            //spusteni parse.php
            exec("php7.4 ".$parseCesta." <\"$cesta.src\" >\"$cesta.my.out\" 2>\"$cesta.error\"", $dump, $diff);
            

            //kontrola rc
            exec("printf $diff | diff -q - \"$cesta.rc\"", $dump, $diff);
            if($diff == 0)
            {
                $rc = "prosel";
            }
            else
            {
                $rc = "neprosel";
            }
            unset($diff);

            //kontrola out
            exec("java -jar ".$jexamxmlCesta." \"$cesta.out\" \"$cesta.my.out\" diffs.xml  /D /pub/courses/ipp/jexamxml/options NAVRATOVA_HODNOTA=\"$diff\"");
            if($diff == 0)
            {
                $out = "prosel";
            }
            else
            {
                $out = "neprosel";
            }

            //smazu docasne soubory
            unlink("$cesta.my.out");
            unlink("diffs.xml");
            unlink("$cesta.error");
            

            //ulozim vysledky
            $vysledky[$nazev]["slozka"] = $slozkaTestu;
            $vysledky[$nazev]["nazev"] = $nazev;
            $vysledky[$nazev]["out"] = $out;
            $vysledky[$nazev]["rc"] = $rc;

            $slozky[$IDslozky]["celkem"]++;
            if($out == "prosel" && $rc == "prosel")
            {
                $slozky[$IDslozky]["proslo"]++;
                $total_proslo++;
            }
        }

        if($int_only == true)
        {
            
            //spusteni interpret.py
            exec("python3.8 ".$interpretCesta." --source=\"$cesta.src\" --input=\"$cesta.in\" >\"$cesta.my.out\" 2>\"$cesta.error\"", $dump, $diff);

            //kontrola rc
            exec("printf $diff | diff -q - \"$cesta.rc\"", $dump, $diff);
            if($diff == 0)
            {
                $rc = "prosel";
            }
            else
            {
                $rc = "neprosel";
            }
            unset($diff);

            //kontrola out
            exec("diff -q \"$cesta.out\" \"$cesta.my.out\"", $dump, $diff);
            if($diff == 0)
            {
                $out = "prosel";
            }
            else
            {
                $out = "neprosel";
            }

            //smazu docasne soubory
            unlink("$cesta.my.out");
            unlink("$cesta.error");

            //ulozim vysledky
            $vysledky[$nazev]["slozka"] = $slozkaTestu;
            $vysledky[$nazev]["nazev"] = $nazev;
            $vysledky[$nazev]["out"] = $out;
            $vysledky[$nazev]["rc"] = $rc;

            $slozky[$IDslozky]["celkem"]++;
            if($out == "prosel" && $rc == "prosel")
            {
                $slozky[$IDslozky]["proslo"]++;
                $total_proslo++;
            }
        }
        //both rezim
        if($parse_only == false && $int_only == false)
        {
            //spusteni parse.php
            exec("php7.4 ".$parseCesta." <\"$cesta.src\" >\"$cesta.tmp\" 2>\"$cesta.error\"");
            
            //spusteni interpret.py
            exec("python3.8 ".$interpretCesta." --source=\"$cesta.tmp\" --input=\"$cesta.in\" >\"$cesta.my.out\" 2>\"$cesta.error\"", $dump, $diff);

            //kontrola rc
            exec("printf $diff | diff -q - \"$cesta.rc\"", $dump, $diff);
            if($diff == 0)
            {
                $rc = "prosel";
            }
            else
            {
                $rc = "neprosel";
            }
            unset($diff);

            //kontrola out
            exec("diff -q \"$cesta.out\" \"$cesta.my.out\"", $dump, $diff);
            if($diff == 0)
            {
                $out = "prosel";
            }
            else
            {
                $out = "neprosel";
            }

            //smazu docasne soubory
            unlink("$cesta.my.out");
            unlink("$cesta.tmp");
            unlink("$cesta.error");

            //ulozim vysledky
            $vysledky[$nazev]["slozka"] = $slozkaTestu;
            $vysledky[$nazev]["nazev"] = $nazev;
            $vysledky[$nazev]["out"] = $out;
            $vysledky[$nazev]["rc"] = $rc;

            $slozky[$IDslozky]["celkem"]++;
            if($out == "prosel" && $rc == "prosel")
            {
                $slozky[$IDslozky]["proslo"]++;
                $total_proslo++;
            }

        }

    }


    function scan($slozkaTestu)
    {
        //pouzivame globalni promenne skriptu krome slozky s testy. ta se predava jako parametr kvuli rekurzi
        global $slozky;
        global $recursive;
        global $total;
        


        //ulozim informace o slozce
        $IDslozky = count($slozky);
        $slozky[$IDslozky]["jmeno"] = $slozkaTestu;
        $slozky[$IDslozky]["celkem"] = 0;
        $slozky[$IDslozky]["proslo"] = 0;

        //scan slozky
        $soubory = scandir($slozkaTestu);

        foreach($soubory as $soubor)
        {
            if(is_dir($slozkaTestu.$soubor)) //pokud je to slozka
            {
                if($recursive == false)
                {
                    continue;
                }
                else
                {
                    if($soubor == "." || $soubor == "..") // zabraneni zacykleni
                    {
                        continue;
                    }
                    scan($slozkaTestu.$soubor."/"); //rekurzivni scan
                }
            }
            else //je to soubor
            {
                if(preg_match("/.src$/", $soubor))
                {
                    $nazev = substr($soubor, 0, -4);//oriznu priponu souboru
                    test($nazev, $slozkaTestu, $IDslozky); //spoustim test
                    $total++;
                }
                else //soubory bez pripony .src preskakuju
                {
                    continue;
                }
            }
        }

        

        
    }

    function error($hodnota, $zprava)
	{
		fputs(STDERR, "$zprava\n");
		exit($hodnota);
    }

?>