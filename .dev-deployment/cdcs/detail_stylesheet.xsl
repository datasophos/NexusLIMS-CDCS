<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema"
    xmlns:nx="https://data.nist.gov/od/dm/nexus/experiment/v1.0"
    xmlns:exslt="http://exslt.org/common"
    xmlns:math="http://exslt.org/math"
    extension-element-prefixes="exslt"
    version="1.0">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>


    <xsl:param name="xmlName" select="''"/>

    <xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>
    <xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>

    <!--
        These variables control the limit for interactive dataset display. More than this
        number and the stylesheet will revert to a simple file list rather than an
        interactive display of each activity
    -->
    <xsl:variable name="maxDatasetCount">100</xsl:variable>
    <xsl:variable name="simpleDisplay" select="count(//nx:dataset) > $maxDatasetCount"/>

    <xsl:variable name="month-num-dictionary">
        <month month-number="01">January</month>
        <month month-number="02">February</month>
        <month month-number="03">March</month>
        <month month-number="04">April</month>
        <month month-number="05">May</month>
        <month month-number="06">June</month>
        <month month-number="07">July</month>
        <month month-number="08">August</month>
        <month month-number="09">September</month>
        <month month-number="10">October</month>
        <month month-number="11">November</month>
        <month month-number="12">December</month>
    </xsl:variable>
    <xsl:key name="lookup.date.month" match="month" use="@month-number"/>

    <xsl:variable name="periodic-table-dictionary">
        <element symbol="H">1 - Hydrogen</element>
        <element symbol="He">2 - Helium</element>
        <element symbol="Li">3 - Lithium</element>
        <element symbol="Be">4 - Beryllium</element>
        <element symbol="B">5 - Boron</element>
        <element symbol="C">6 - Carbon</element>
        <element symbol="N">7 - Nitrogen</element>
        <element symbol="O">8 - Oxygen</element>
        <element symbol="F">9 - Fluorine</element>
        <element symbol="Ne">10 - Neon</element>
        <element symbol="Na">11 - Sodium</element>
        <element symbol="Mg">12 - Magnesium</element>
        <element symbol="Al">13 - Aluminum</element>
        <element symbol="Si">14 - Silicon</element>
        <element symbol="P">15 - Phosphorus</element>
        <element symbol="S">16 - Sulfur</element>
        <element symbol="Cl">17 - Chlorine</element>
        <element symbol="Ar">18 - Argon</element>
        <element symbol="K">19 - Potassium</element>
        <element symbol="Ca">20 - Calcium</element>
        <element symbol="Sc">21 - Scandium</element>
        <element symbol="Ti">22 - Titanium</element>
        <element symbol="V">23 - Vanadium</element>
        <element symbol="Cr">24 - Chromium</element>
        <element symbol="Mn">25 - Manganese</element>
        <element symbol="Fe">26 - Iron</element>
        <element symbol="Co">27 - Cobalt</element>
        <element symbol="Ni">28 - Nickel</element>
        <element symbol="Cu">29 - Copper</element>
        <element symbol="Zn">30 - Zinc</element>
        <element symbol="Ga">31 - Gallium</element>
        <element symbol="Ge">32 - Germanium</element>
        <element symbol="As">33 - Arsenic</element>
        <element symbol="Se">34 - Selenium</element>
        <element symbol="Br">35 - Bromine</element>
        <element symbol="Kr">36 - Krypton</element>
        <element symbol="Rb">37 - Rubidium</element>
        <element symbol="Sr">38 - Strontium</element>
        <element symbol="Y">39 - Yttrium</element>
        <element symbol="Zr">40 - Zirconium</element>
        <element symbol="Nb">41 - Niobium</element>
        <element symbol="Mo">42 - Molybdenum</element>
        <element symbol="Tc">43 - Technetium</element>
        <element symbol="Ru">44 - Ruthenium</element>
        <element symbol="Rh">45 - Rhodium</element>
        <element symbol="Pd">46 - Palladium</element>
        <element symbol="Ag">47 - Silver</element>
        <element symbol="Cd">48 - Cadmium</element>
        <element symbol="In">49 - Indium</element>
        <element symbol="Sn">50 - Tin</element>
        <element symbol="Sb">51 - Antimony</element>
        <element symbol="Te">52 - Tellurium</element>
        <element symbol="I">53 - Iodine</element>
        <element symbol="Xe">54 - Xenon</element>
        <element symbol="Cs">55 - Cesium</element>
        <element symbol="Ba">56 - Barium</element>
        <element symbol="La">57 - Lanthanum</element>
        <element symbol="Ce">58 - Cerium</element>
        <element symbol="Pr">59 - Praseodymium</element>
        <element symbol="Nd">60 - Neodymium</element>
        <element symbol="Pm">61 - Promethium</element>
        <element symbol="Sm">62 - Samarium</element>
        <element symbol="Eu">63 - Europium</element>
        <element symbol="Gd">64 - Gadolinium</element>
        <element symbol="Tb">65 - Terbium</element>
        <element symbol="Dy">66 - Dysprosium</element>
        <element symbol="Ho">67 - Holmium</element>
        <element symbol="Er">68 - Erbium</element>
        <element symbol="Tm">69 - Thulium</element>
        <element symbol="Yb">70 - Ytterbium</element>
        <element symbol="Lu">71 - Lutetium</element>
        <element symbol="Hf">72 - Hafnium</element>
        <element symbol="Ta">73 - Tantalum</element>
        <element symbol="W">74 - Tungsten</element>
        <element symbol="Re">75 - Rhenium</element>
        <element symbol="Os">76 - Osmium</element>
        <element symbol="Ir">77 - Iridium</element>
        <element symbol="Pt">78 - Platinum</element>
        <element symbol="Au">79 - Gold</element>
        <element symbol="Hg">80 - Mercury</element>
        <element symbol="Tl">81 - Thallium</element>
        <element symbol="Pb">82 - Lead</element>
        <element symbol="Bi">83 - Bismuth</element>
        <element symbol="Po">84 - Polonium</element>
        <element symbol="At">85 - Astatine</element>
        <element symbol="Rn">86 - Radon</element>
        <element symbol="Fr">87 - Francium</element>
        <element symbol="Ra">88 - Radium</element>
        <element symbol="Ac">89 - Actinium</element>
        <element symbol="Th">90 - Thorium</element>
        <element symbol="Pa">91 - Protactinium</element>
        <element symbol="U">92 - Uranium</element>
        <element symbol="Np">93 - Neptunium</element>
        <element symbol="Pu">94 - Plutonium</element>
        <element symbol="Am">95 - Americium</element>
        <element symbol="Cm">96 - Curium</element>
        <element symbol="Bk">97 - Berkelium</element>
        <element symbol="Cf">98 - Californium</element>
        <element symbol="Es">99 - Einsteinium</element>
        <element symbol="Fm">100 - Fermium</element>
        <element symbol="Md">101 - Mendelevium</element>
        <element symbol="No">102 - Nobelium</element>
        <element symbol="Lr">103 - Lawrencium</element>
        <element symbol="Rf">104 - Rutherfordium</element>
        <element symbol="Db">105 - Dubnium</element>
        <element symbol="Sg">106 - Seaborgium</element>
        <element symbol="Bh">107 - Bohrium</element>
        <element symbol="Hs">108 - Hassium</element>
        <element symbol="Mt">109 - Meitnerium</element>
        <element symbol="Ds">110 - Darmstadtium</element>
        <element symbol="Rg">111 - Roentgenium</element>
        <element symbol="Cn">112 - Copernicium</element>
        <element symbol="Nh">113 - Nihonium</element>
        <element symbol="Fl">114 - Flerovium</element>
        <element symbol="Mc">115 - Moscovium</element>
        <element symbol="Lv">116 - Livermorium</element>
        <element symbol="Ts">117 - Tennessine</element>
        <element symbol="Og">118 - Oganesson</element>
    </xsl:variable>
    <xsl:key name="lookup.element.symbol" match="element" use="@symbol"/>

    <!-- This lookup table assigns a color to each instrument's badge so they can be visually distinguished
       on the list page -->
    <xsl:variable name="instr-color-dictionary">
        <instr instr-PID="FEI-Titan-TEM-635816">#ff7f0e</instr>
        <instr instr-PID="FEI-Titan-STEM-630901">#2ca02c</instr>
        <instr instr-PID="FEI-Quanta200-ESEM-633137">#d62728</instr>
        <instr instr-PID="JEOL-JEM3010-TEM-565989">#9467bd</instr>
        <instr instr-PID="FEI-Helios-DB-636663">#8c564b</instr>
        <instr instr-PID="Hitachi-S4700-SEM-606559">#e377c2</instr>
        <instr instr-PID="Hitachi-S5500-SEM-635262">#17becf</instr>
        <instr instr-PID="JEOL-JSM7100-SEM-N102656">#bcbd22</instr>
        <instr instr-PID="Philips-EM400-TEM-599910">#bebada</instr>
        <instr instr-PID="Philips-CM30-TEM-540388">#b3de69</instr>
        <instr instr-PID="FEI-Titan-TEM-640918">#25276A</instr>
        <instr instr-PID="Zeiss-LEO_1525_FESEM-927910">#1a581d</instr>
        <instr instr-PID="FEI-Helios-DB-647035">#3f1f5f</instr>
        <instr instr-PID="FEI-Helios-DB-647036">#40686f</instr>
        <instr instr-PID="Zeiss-Gemini_300_SEM-936834">#791212</instr>
        <instr instr-PID="FEI-Quanta_400_SEM-938570">#154157</instr>
        <instr instr-PID="JEOL-7800F_SEM-N113138">#81538d</instr>
        <instr instr-PID="FEI-Titan-ETEM-644764">#CC8B2F</instr>
        <instr instr-PID="Thermo-Scios-DB-9957773">#496BC4</instr>
    </xsl:variable>
    <xsl:key name="lookup.instr.color" match="instr" use="@instr-PID"/>


    <!-- Lookup table for tooltip text for extension badges

Use it like:

<xsl:variable name="value_to_lookup" select="'tif'"/>
<xsl:value-of select='extension-to-tooltip-lookup/row[@ext = $value_to_lookup]'/>
-->
    <xsl:variable name="extension-to-tooltip-lookup-fragment">
        <row ext="" tooltip="File extension" />
        <row ext="dm3" tooltip="Gatan DigitalMicrograph file (v3)" />
        <row ext="dm4" tooltip="Gatan DigitalMicrograph file (v4)" />
        <row ext="tif" tooltip="Tiff-format image" />
        <row ext="tiff" tooltip="Tiff-format image" />
        <row ext="ser" tooltip="FEI .ser file" />
        <row ext="emi" tooltip="FEI .emi file" />
        <row ext="txt" tooltip="Text file" />
        <row ext="dat" tooltip="Custom .dat file" />
        <row ext="spc" tooltip="EDAX EDS spectrum file" />
        <row ext="spd" tooltip="EDAX EDS spectrum image file" />
        <row ext="jpg" tooltip="JPEG-format image" />
        <row ext="jpeg" tooltip="JPEG-format image" />
        <row ext="osc" tooltip="EDAX EBSD file" />
        <row ext="ang" tooltip="EDAX EBSD file" />
        <row ext="h5" tooltip="HDF5 container file" />
        <row ext="hdf5" tooltip="HDF5 container file" />
        <row ext="msa" tooltip="MSA spectrum file" />
        <row ext="xml" tooltip="Custom XML format file" />
        <row ext="csv" tooltip="Comma separated value file" />
        <row ext="xls" tooltip="Excel workbook file" />
        <row ext="xlsx" tooltip="Excel workbook file" />
        <row ext="ppt" tooltip="Powerpoint presentation file" />
        <row ext="pptx" tooltip="Powerpoint presentation file" />
        <row ext="doc" tooltip="Word document file" />
        <row ext="docx" tooltip="Word document file" />
        <row ext="pdf" tooltip="Portable Document Format file" />
        <row ext="spx" tooltip="Bruker spectrum file" />
        <row ext="rpl" tooltip="LISPIX-format spectrum image file" />
        <row ext="rtf" tooltip="Rich text format file" />
        <row ext="oip" tooltip="Oxford Instruments project file" />
        <row ext="oipx" tooltip="Oxford Instruments project file" />
        <row ext="h5oina" tooltip="Oxford Instruments data export file" />
        <row ext="ebsp" tooltip="Oxford EBSD pattern" />
    </xsl:variable>
    <xsl:variable
        name="extension-to-tooltip-lookup"
        select="exslt:node-set($extension-to-tooltip-lookup-fragment)" />

    <xsl:template match="/">
        <xsl:apply-templates select="/nx:Experiment"/>
    </xsl:template>
    <xsl:template match="nx:Experiment">
        <xsl:variable name="reservation-date-part">
            <xsl:call-template name="tokenize-select">
                <xsl:with-param name="text" select="nx:summary/nx:reservationStart"/>
                <xsl:with-param name="delim">T</xsl:with-param>
                <xsl:with-param name="i" select="1"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="firstfile-date-part">
            <xsl:call-template name="tokenize-select">
                <xsl:with-param name="text" select="nx:acquisitionActivity[1]/nx:startTime"/>
                <xsl:with-param name="delim">T</xsl:with-param>
                <xsl:with-param name="i" select="1"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="title">
            <xsl:value-of select="nx:title"/>
        </xsl:variable>
        <xsl:variable name="pid">
            <xsl:value-of select="@pid"/>
        </xsl:variable>

        <xsl:variable name="extension-fragment">
            <xsl:element name="extensions">
                <xsl:for-each select="//nx:dataset/nx:location">
                    <xsl:call-template name="get-file-extension">
                        <xsl:with-param name="path">
                            <xsl:value-of select="."/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:element>
        </xsl:variable>

        <xsl:variable name="extensionCount">
            <xsl:for-each select="exslt:node-set($extension-fragment)/extensions/ext[not(preceding::value = value)]">
                <xsl:variable name="thisExtension" select="value/text()"/>
                <xsl:variable name="thisCount" select="count(exslt:node-set($extension-fragment)/extensions/ext[value = $thisExtension])"/>
                <xsl:element name="extension">
                    <xsl:attribute name="count">
                        <xsl:value-of select="$thisCount"/>
                    </xsl:attribute>
                    <xsl:value-of select="$thisExtension"/>
                </xsl:element>
            </xsl:for-each>
        </xsl:variable>


        <div style='display: none;' id="simpleDisplay">
            <xsl:value-of select="$simpleDisplay"/>
        </div>
<!--   This div holds a placeholder preview image for those datasets that don't have a preview set. It's value is only included once in the HTML produced by the XSLT, and then set in each place it's needed by javascript when the page is done loading (this is faster than inserting the below base64 inline at every position via the XSLT -->
        <div style='display: none;' id="placeholder-preview-src">data:image/jpeg;base64,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atLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmrSy5q0suatLLmqdtWTtoKxX1z+gM5cusV9c/oDOXLrFfXP6Azly6xX1z+gM5cusV9c/oDOXLrFfXP6Azly6xX1z+gM5cusV9c/oDOXLrFfXP6Azly6xX1z+gM5cusV9c/oDOXLrFfXP6Azly6xX1z+gM5cusV9c+ekJRrFJOslNiGRyYmJom5Y+Z8/nLl1ivrnztyT6cAxfP15JzsKYSGsy6xkw87nLl1ivrnzt5yQyM7wNHJ2Tlo5K8a+czly6xX1z514Ii74bSERtzzmcuXWK+ufO3UwGOneBNMyykc0+Aw85nLl1ivrnyq65G5DTY72kiR0PDeFufnGaiZkj7bGtg3ucDp0VokrKuFBby6yZk1Cqk8rnLl1ivrnyswoJnNFMJDEN6ycM1a7Kcp1jZ4QyOOZI5oexGUabhmziLjZCHEUNgjuopgN5LOXLrFfXPkJGUMQ/wApbfHyhjH2TDURGmrYzpUA3B90w0FUtAAmGPbfFb0qoCSbl0d0chzJmj3fykfIZy5dYr658NMTbWEbyWQZB0YbllRNH37JtDQVyNJ5PgH+BHeNfxRB3k2GYNziRMqRewVj26wos0W+2RKJ2WyDKPFISLeLbSmRHa5j3NKnMyviWZmt+7ms54fOXLrFfXPhZB8nGspWUWl3u1o7VYuIKWJNxvBIsjNlaj2RnSvdOocfUlDrGFBErdPgUUKincU6pOv9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zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzyV/bzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzxz3/wC88888888888888888888888888888888888888888888888888888888885388Q9tc8z68888888888888888888888888888888888888888888888888888908XL88stu880g739888888888888888888888888888888888888888888886tv88aq8cf8888888//AONNfP5bX/PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPHPfdvPD/ADzw3Xzzy5fzzzzzz/333zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzyrzPXzzfzzx/zzzzzzzzzXTyxn3fzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzx/wA8vt89L8888888mJ8L988/Mc88888888888888888888888888888888888888888888888Zt88k/688eu888888889x888888888888888888888888888888888880d888888888888V/wDvPPPPPPPPPPfHOvPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPDnfNdvPKHNfPPPOsVfPPPOh1vPPR/Lbv/PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPOXP/ADzzzyvz+nzzzzzzzzzzyr/9/wA88887t38888888888888888888888888888888/s/88z289+8t8888888888883of8gd888e/8888888888888888888888888888888888+v+z88+O88888otX888888d88V63+2888888888888888888888888888888nsq88938+f88888w488/8AVvPOcPPPPPPH/KlPPKP3/PPPPPPPPPPPPPPPPPPPPPPPL/8A3/zzzzzzzzzzzzS3zzzzzzzXjzzzzzzzzzzzxb33fzzzzzzzzzzzzzzzzzzzzzzzzD3Hzzzz/fTzzzzy3zzzzrzzw5/zzzzz7Pzzzzxj3Z/zzzzzzzzzzzzzzzzzzzzzzzz617zzzxz+rTzzzzzzn7xzzzvzzzzzzyz8rzzzyz//AM8888888888888888888888888888888V/8c8z6888+/wDPPPHfPPNePPGP8PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPO/PE/PLf8A/wA8SvU/888s/Z28438e688/M+88w17y/wDPPPPPPPPPPPPPPPPPPPPPPPPOXlfPPPPPPPPLTPO3vN//AP8A78un88O888887/8APK+HvPPPPPPPPPPPPPPPPPPPPPPPPPLP/PFSvPPPPPPPPPPHv/8A+nzzzzzzzzzzyWnzzw/zzzzzzzzzzzzzzzzzzzzzzzzzzjLbzzyPzzzzzzzzvzxb/wD/AOPOP/PPPPPPPKrPPODf/PPPPPPPPPPPPPPPPPPPPPPPPLtPPuPPPPPPPJKvL9vDtv8Ao7z6fyffzzzzzzzLy3pzzzzzzzzzzzzzzzzzzzzzzzzzzw7y5nzz6bfzzHxzzzzy153zzzzzynzzQ3fzzx/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzyz+3Tz13zzzRTzzzxHzzz7/AM8c/q888888888888888888888888888888883+w8888d678888888fc8Q88/8APPPPPPNNV/PPPMifvPPPPPPPPPPPPPPPPPPPPPPPP3Pb/wDzzzz7zzzzzy+vzzw/zzy47zzzzzw7zzzzz333fzzzzzzzzzzzzzzzzzzzzzzyzz33/wA8888888888x28843388Zk888888888888W949888888888888888888888888vLf88tC86+888888888s8088888888877/6j88s6l888888888888888888888888888888888U9889418888+Pd88884018887+88908888888888888888888888888888888/u/8APLfvKfv1PPPPPPPPPPPOv7HfLPfPPPi/PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP9f/POvPPlv9vPPPPPPPPPPK/e9fPOfPPDXPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPLHvGtfPD3PPPPPMjP/ADzzzz27zyxHyjnzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzGXzzzzzzzzvvzzb+zzzjXzzzzzzzz7Tzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzxarzy7bbzyynzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz37bzzzPxxzzzzzzzz13zV7zz/LfzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzyX277zzzzzzHTzzzzvzzy5zz3/0zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzxL337zzLTzwjzzzzx7zzzzTz7f3vzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzy7JTzz7X7Lrzzzzzzzjfzarzzm87zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzwxzynzyd7Lzznfw93zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzx3zxf25Xzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzx72h/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz227zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz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</div>

        <div class="w-100">

            <div id="loading">
                <img src="/static/img/logo_bare.png"/>
            </div>


            <!-- ============= Main Generation of the Page ============= -->
            <!-- Add sidebar to the page -->
            <xsl:if test="not($simpleDisplay)">
              <div class="sidebar">
                  <table id="nav-table" class="table table-sm table-hover">
                      <!-- Procedurally generate unique id numbers which relate each acquisition event to its position on
                          the webpage such that it will jump there when the link is clicked -->
                      <thead>
                          <tr><th>Explore record:</th></tr>
                      </thead>
                      <tbody>
                      <xsl:for-each select="nx:acquisitionActivity">
                          <tr><td>
                          <a class="link" href="#{generate-id(current())}">
                              Activity <xsl:value-of select="@seqno+1"/>
                          </a>
                              <div><xsl:call-template name="parse-activity-contents"></xsl:call-template></div>
                          </td></tr>
                      </xsl:for-each>
                      </tbody>
                      </table>

                      <!-- Create button which jumps to the top of the page when clicked -->
                      <button id="to-top-btn" type="button" class="btn btn-primary" value="Top" onclick="window.NexusLIMSDetail.toTop()">
                          <i class="fa fa-arrow-up"></i> Scroll to Top
                      </button>
              </div>
              <div id="btn-sidebar" data-bs-toggle="tooltip" data-bs-placement="right"
                   data-bs-title="Click to explore record contents">
                  <a><i class="fas fa-chevron-right"></i></a>
              </div>
            </xsl:if>

            <div class="main d-flex" style="padding: 0; position: relative; z-index: 100;" id="top-button-div">
                  <button id="btn-edit-record" type="button" class="btn btn-outline-dark btn-top-group"
                          data-bs-toggle="tooltip" data-bs-placement="top"
                          title="Manually edit the contents of this record (login required)">
                      <i class="fas fa-file-alt menu-fa"></i> Edit this record
                  </button>

                  <button id="btn-xml-dl" type="button" class="btn btn-outline-dark btn-top-group"
                      data-bs-toggle="tooltip" data-bs-placement="top"
                      title="Download metadata contents of this record as XML">
                      <i class="fas fa-code menu-fa"></i> Download XML
                  </button>

                <xsl:if test="not($simpleDisplay)">
                    <button id="btn-filelisting" type="button"
                            class="btn btn-outline-dark btn-top-group"
                            data-bs-toggle="tooltip" data-bs-placement="top"
                            title="View a file listing (and download the files) of this record"
                            onclick="window.NexusLIMSDetail.openModal('filelist-modal');">
                     <i class="fas fa-cloud-download-alt menu-fa"></i> Download files
                    </button>

                </xsl:if>
                <xsl:choose>
                    <xsl:when test="$pid != ''">
                        <span id='pid-to-copy' style='display: none;'>
                            <xsl:value-of select="$pid"/>
                        </span>
                        <button id="btn-copy-pid" type="button" class="btn btn-outline-dark btn-top-group"
                            data-bs-toggle="tooltip" data-bs-placement="top"
                            title="Click here to copy this record's PID"
                            onclick="window.NexusLIMSDetail.copy_and_change_tt()">
                            <i class="fas fa-link menu-fa"></i> Copy record PID
                        </button>
                        <script>
                            let tt_text = "Click here to copy this record's PID";

                            $('#btn-copy-pid').mouseout(() => {
                                // console.log('processing mouseout');
                                setTimeout(() => {
                                    $('#btn-copy-pid').attr('data-bs-original-title', tt_text);
                                    var tooltip = bootstrap.Tooltip.getInstance(document.getElementById('btn-copy-pid')); if (tooltip) { document.getElementById('btn-copy-pid').setAttribute('data-bs-original-title', tt_text); tooltip.update(); }
                                   // $('#btn-copy-pid').tooltip('show');
                                }, 150);
                            })
                        </script>
                    </xsl:when>
                </xsl:choose>
                <button id="btn-previous-page" type="button" class="btn btn-outline-dark btn-top-group"
                        data-bs-toggle="tooltip" data-bs-placement="top"
                        title="Go back to the previous page">
                    <i class="fas fa-arrow-left menu-fa"></i> Back to previous
                </button>
            </div>

            <!-- Main content -->
            <span id='xmlName' style='display: none;'><xsl:value-of select="$xmlName"/></span>
            <div class="row align-items-center">
            <div class="main col-sm-12" id="main-column">
                <xsl:variable name="expTitle">
                    <xsl:choose>
                        <xsl:when test="$title = 'No matching calendar event found'">
                            <xsl:text>Untitled experiment</xsl:text>
                            <span class='no-cal-warning'> (No matching calendar event found)</span>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$title"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="date">
                    <xsl:choose>
                        <xsl:when test="$reservation-date-part != ''">
                            <xsl:call-template name="localize-date">
                                <xsl:with-param name="date">
                                    <xsl:value-of select="$reservation-date-part"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:when test="$firstfile-date-part != ''">
                            <xsl:call-template name="localize-date">
                                <xsl:with-param name="date">
                                    <xsl:value-of select="$firstfile-date-part"/>
                                </xsl:with-param>
                            </xsl:call-template>
                            <span style="font-size:small; font-style:italic;"> (taken from file timestamps)</span>
                        </xsl:when>
                        <xsl:otherwise>Unknown date</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <xsl:if test="$simpleDisplay">
                    <div class="row mt-0" id="simple-display-row">
                        <div class="col-sm"></div>
                        <div class="col-sm-9">
                            <div
                                id="simple-warning-inner-div"
                                class="alert alert-warning simple-warning mt-3 mb-4">
                                <i
                                    class="fas fa-times float-right" onclick="$('#simple-warning-inner-div').hide()"
                                    style="cursor: pointer;"
                                    data-bs-toggle='tooltip'
                                    data-bs-placement='right'
                                    title='Click to hide this warning'/>
                                <div class="pr-4">
                                 Heads up! This experiment record contains
                                 more datasets (<xsl:value-of select="format-number(count(//nx:dataset),'#,###')"/>) than NexusLIMS can interactively
                                 show, so a simplified representation is provided.

                                 To download your files, please access the central file storage directly, or click the individual download links for files of interest below.
                                </div>
                            </div>
                        </div>
                        <div class="col-sm"></div>
                    </div>
                </xsl:if>
                <div class="row mt-4">
                    <button
                        id="to-top-btn"
                        type="button"
                        class="btn btn-primary"
                        value="Top"
                        onclick="window.NexusLIMSDetail.toTop()"
                        style="position: fixed; width: 125px; left: 40px; padding: 10px;">
                        <i class="fa fa-arrow-up"></i> Scroll to Top
                    </button>
                    <div class="col-md-6" id="session_info_column">
                        <div id='record-header' style="margin-bottom: 1em;">
                            <div id='summary-info'>
                                <span class="list-record-title page-header">
                                    <i class="fas fa-file-alt results-icon"/>
                                    <xsl:value-of select="$expTitle"/>
                                </span>
                                <br/>
                                <xsl:variable name="instr-pid">
                                    <xsl:value-of select="string(nx:summary/nx:instrument/@pid)"/>
                                </xsl:variable>
                                <span id='instr-badge' class="badge list-record-badge">
                                    <xsl:choose>
                                        <xsl:when test="nx:summary/nx:instrument/text()">
                                            <xsl:attribute name="style">background-color:<xsl:for-each select="document('')">
                                                <xsl:value-of select="key('lookup.instr.color', $instr-pid)"/>
                                            </xsl:for-each> !important;</xsl:attribute>
                                            <xsl:element name="a">

                                                <xsl:value-of select="nx:summary/nx:instrument"/>
                                            </xsl:element>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            Unknown instrument
                                        </xsl:otherwise>
                                    </xsl:choose>

                                </span>
                                <span class="badge list-record-badge">
                                    <xsl:element name="a">
                                        <xsl:if test="not($simpleDisplay)">
                                            <xsl:attribute name="href">
                                                javascript:void(0);
                                            </xsl:attribute>
                                            <xsl:attribute name="onclick">
                                                window.NexusLIMSDetail.openModal('filelist-modal');
                                            </xsl:attribute>
                                            <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                            <xsl:attribute name="data-bs-placement">bottom</xsl:attribute>
                                            <xsl:attribute name="title">Click to view a file listing of this record</xsl:attribute>
                                        </xsl:if>
                                        <xsl:value-of select="count(//nx:dataset)"/> data file<xsl:if test="count(//nx:dataset)>1">s</xsl:if> in <xsl:value-of select="count(//nx:acquisitionActivity)"/> activit<xsl:choose>
                                            <xsl:when test="count(//nx:acquisitionActivity) = 1">y</xsl:when>
                                            <xsl:otherwise>ies</xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:element>
                                </span>
                                <i class="fa fa-cubes" style="margin-left:0.75em; font-size: small;"
                                    data-bs-toggle="tooltip" data-bs-placement="bottom" title="Filetypes present in record"/><span style="font-size: small;"><xsl:text>: </xsl:text></span>
                                <!-- badges for unique file extensions -->
                                <xsl:variable name="unique-extensions">
                                    <xsl:call-template name="get-unique-extensions">
                                        <xsl:with-param name="global" select="true()"/>
                                    </xsl:call-template>
                                </xsl:variable>
                                <xsl:call-template name="extensions-to-badges">
                                    <xsl:with-param name="input" select="exslt:node-set($unique-extensions)"/>
                                </xsl:call-template>
                            </div>
                            <div class="experimenter-and-date">
                                <span class="list-record-experimenter">
                                    <xsl:choose>
                                        <xsl:when test="nx:summary/nx:experimenter">
                                            <xsl:value-of select="nx:summary/nx:experimenter"/>
                                        </xsl:when>
                                        <xsl:otherwise>Unknown experimenter</xsl:otherwise>
                                    </xsl:choose>
                                </span>
                                <xsl:text> - </xsl:text>
                                <span class="list-record-date"><i><xsl:value-of select="$date"/></i></span>
                            </div>
                            <div class="motivation-text">

                                <xsl:choose>
                                    <xsl:when test="nx:summary/nx:motivation/text()">
                                        <span style="font-style:italic;">Motivation: </span><xsl:value-of select="nx:summary/nx:motivation"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        No motivation provided
                                        <xsl:call-template name="help-tip">
                                            <xsl:with-param name="tip-placement">right</xsl:with-param>
                                            <xsl:with-param name="tip-text">This value is pulled from the "Experiment Purpose" field of a calendar reservation</xsl:with-param>
                                        </xsl:call-template>
                                    </xsl:otherwise>
                                </xsl:choose>

                            </div>
                            <xsl:choose>
                                <xsl:when test="$pid != ''">
                                    <div class="pid-row">
                                        <span style="font-style:italic;">Persistent ID: </span>
                                        <xsl:element name="a">
                                            <xsl:attribute name="href">
                                                <xsl:value-of select="$pid"/>
                                            </xsl:attribute>
                                            <xsl:value-of select="$pid"/>
                                        </xsl:element>
                                    </div>
                                </xsl:when>
                            </xsl:choose>
                        </div>

                        <h3 id="res-info-header">Session Summary
                        <xsl:if test="nx:summary/@ref">
                            -
                            <xsl:element name="a">
                                <xsl:attribute name="href"><xsl:value-of select="nx:summary/@ref"/></xsl:attribute>
                                <xsl:attribute name="target">_blank</xsl:attribute>
                                <i class='fa fa-calendar-alt'/>
                            </xsl:element>
                            <xsl:text> </xsl:text>
                        </xsl:if>
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-text">Summary information is extracted from the calendar reservation associated with this record; click the calendar icon (if present) to visit the page for this reservation</xsl:with-param>
                        </xsl:call-template>
                        </h3>
                        <!-- Display summary information (date, time, instrument, and id) -->

                        <table class="table upper-table" id="summary-table"
                               style="border-collapse:collapse;">
                            <xsl:if test="nx:summary/nx:reservationStart/text()">
                                <tr>
                                    <th scope="row">Start Time: </th>
                                    <td>
                                        <xsl:call-template name="tokenize-select">
                                            <xsl:with-param name="text" select="nx:summary/nx:reservationStart"/>
                                            <xsl:with-param name="delim">T</xsl:with-param>
                                            <xsl:with-param name="i" select="1"/>
                                        </xsl:call-template>
                                        <xsl:text> – </xsl:text>
                                        <xsl:call-template name="tokenize-select">
                                            <xsl:with-param name="text" select="nx:summary/nx:reservationStart"/>
                                            <xsl:with-param name="delim">T</xsl:with-param>
                                            <xsl:with-param name="i" select="2"/>
                                        </xsl:call-template>
                                    </td>
                                </tr>
                            </xsl:if>
                            <xsl:if test="nx:summary/nx:reservationEnd/text()">
                                <tr>
                                    <th scope="row">End Time: </th>
                                    <td align="justify">
                                        <xsl:call-template name="tokenize-select">
                                            <xsl:with-param name="text" select="nx:summary/nx:reservationEnd"/>
                                            <xsl:with-param name="delim">T</xsl:with-param>
                                            <xsl:with-param name="i" select="1"/>
                                        </xsl:call-template>
                                        <xsl:text> – </xsl:text>
                                        <xsl:call-template name="tokenize-select">
                                            <xsl:with-param name="text" select="nx:summary/nx:reservationEnd"/>
                                            <xsl:with-param name="delim">T</xsl:with-param>
                                            <xsl:with-param name="i" select="2"/>
                                        </xsl:call-template>
                                    </td>
                                </tr>
                            </xsl:if>
                            <xsl:if test="nx:summary/nx:collaborator">
                                <tr>
                                    <th scope="row">Collaborator<xsl:if test="count(nx:summary/nx:collaborator) > 1">s</xsl:if>: </th>
                                    <td>
                                        <xsl:for-each select="nx:summary/nx:collaborator">
                                            <xsl:if test="position() > 1"><br/></xsl:if>
                                            <xsl:value-of select="."/>
                                        </xsl:for-each>
                                    </td>
                                </tr>
                            </xsl:if>
                            <xsl:if test="nx:id/text()">
                                <tr>
                                    <th scope="row">Reservation ID:<xsl:text> </xsl:text>
                                        <xsl:call-template name="help-tip">
                                            <xsl:with-param name="tip-placement">right</xsl:with-param>
                                            <xsl:with-param name="tip-text">ID from this instrument's calendar reservation</xsl:with-param>
                                        </xsl:call-template></th>
                                    <td><xsl:value-of select="nx:id"/></td>
                                </tr>
                            </xsl:if>
                         <!--   <xsl:if test="acquisitionActivity[@seqno=0]/sampleID/text()">
                                <tr>
                                    <th scope="row">Sample name: </th>
                                    <td> <xsl:value-of select="sample/name"/></td>
                                </tr>
                            </xsl:if>
                            <xsl:if test="acquisitionActivity[@seqno=0]/sampleID/text()">
                                <tr>
                                    <th scope="row">Sample ID:<xsl:text> </xsl:text>
                                        <xsl:call-template name="help-tip">
                                            <xsl:with-param name="tip-placement">right</xsl:with-param>
                                            <xsl:with-param name="tip-text">Automatically generated random ID (for now)</xsl:with-param>
                                        </xsl:call-template></th>
                                    <td><xsl:value-of select="acquisitionActivity[@seqno=0]/sampleID"/></td>
                                </tr>
                            </xsl:if>
                            <xsl:variable name="description-stripped">
                                <xsl:call-template name='strip-tags'>
                                    <xsl:with-param name="text" select="sample/description"/>
                                </xsl:call-template>
                            </xsl:variable>
                            <xsl:if test="string-length($description-stripped) > 0">
                                <tr>
                                    <th scope="row">Description: </th>
                                    <td><xsl:value-of select="$description-stripped"/></td>
                                </tr>
                            </xsl:if> -->
                        </table>

                        <xsl:if test="nx:sample/*/text() | nx:sample/@ref">
                            <h3 id="sample-info-header">Sample Information
                                <xsl:call-template name="help-tip">
                                    <xsl:with-param name="tip-text">Sample information is extracted from the calendar reservation associated with this record</xsl:with-param>
                                </xsl:call-template>
                            </h3>
                            <table class="table upper-table" id="sample-table"
                                style="border-collapse:collapse;">
                                <xsl:choose>
                                    <xsl:when test="count(nx:sample) = 1">
                                        <xsl:if test="nx:sample/nx:name/text()">
                                            <tr>
                                                <th scope="row">Name:
                                                    <xsl:call-template name="help-tip">
                                                        <xsl:with-param name="tip-text">The name given to this sample (as entered at the time of reservation)</xsl:with-param>
                                                    </xsl:call-template>
                                                </th>
                                                <td> <xsl:value-of select="nx:sample/nx:name"/></td>
                                            </tr>
                                        </xsl:if>
                                        <xsl:if test="nx:sample/@ref">
                                            <tr>
                                                <th scope="row">PID:
                                                    <xsl:call-template name="help-tip">
                                                        <xsl:with-param name="tip-text">A persistent identifier for this sample (if a URL, you can click to view more sample details)</xsl:with-param>
                                                    </xsl:call-template>
                                                </th>
                                                <td>
                                                    <xsl:call-template name="link-or-text">
                                                        <xsl:with-param name="val">
                                                            <xsl:value-of select="nx:sample/@ref"/>
                                                        </xsl:with-param>
                                                    </xsl:call-template>
                                                </td>
                                            </tr>
                                        </xsl:if>
                                        <xsl:if test="nx:sample/nx:description/text()">
                                            <tr>
                                                <th scope="row">Description:
                                                    <xsl:call-template name="help-tip">
                                                        <xsl:with-param name="tip-text">The description given to this sample (as entered at the time of reservation)</xsl:with-param>
                                                    </xsl:call-template>
                                                </th>
                                                <td> <xsl:value-of select="nx:sample/nx:description"/></td>
                                            </tr>
                                        </xsl:if>
                                        <xsl:if test="nx:sample/nx:elements/*">
                                            <tr>
                                                <th scope="row">Elements:
                                                <xsl:call-template name="help-tip">
                                                    <xsl:with-param name="tip-text">The physical elements (as chosen by the user) that are expected to be in this sample</xsl:with-param>
                                                </xsl:call-template>
                                                </th>
                                                <td>
                                                    <xsl:call-template name="elements-to-list">
                                                        <xsl:with-param name="elements">
                                                            <xsl:copy-of select="nx:sample/nx:elements/*"/>
                                                        </xsl:with-param>
                                                        <xsl:with-param name="tooltip-position">right</xsl:with-param>
                                                    </xsl:call-template>
                                                </td>
                                            </tr>
                                        </xsl:if>
                                    </xsl:when>
                                    <xsl:when test="count(nx:sample) > 1">
                                        <table class="table table-sm table-hover sample-table compact wrap" border="1"
                                               style="width:90%; border-collapse:collapse; text-align: center;">
                                            <thead>
                                                <tr>
                                                    <th style='padding-left: 1.0em; padding-right: 1.0em;'>#</th>
                                                    <th>
                                                        Name
                                                        <xsl:call-template name="help-tip">
                                                            <xsl:with-param name="tip-text">The name given to this sample (as entered at the time of reservation)</xsl:with-param>
                                                        </xsl:call-template>
                                                    </th>
                                                    <th>
                                                        PID
                                                        <xsl:call-template name="help-tip">
                                                            <xsl:with-param name="tip-text">A persistent identifier for this sample (if a URL, you can click to view more sample details)</xsl:with-param>
                                                        </xsl:call-template>
                                                    </th>
                                                    <th>
                                                        Description
                                                        <xsl:call-template name="help-tip">
                                                            <xsl:with-param name="tip-text">The description given to this sample (as entered at the time of reservation)</xsl:with-param>
                                                        </xsl:call-template>
                                                    </th>
                                                    <th>
                                                        Elements
                                                        <xsl:call-template name="help-tip">
                                                            <xsl:with-param name="tip-text">The physical elements (as chosen by the user) that are expected to be in this sample</xsl:with-param>
                                                        </xsl:call-template>
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                        <xsl:for-each select="nx:sample">
                                            <xsl:variable name="i" select="position()" />

                                            <tr>
                                                <td style='padding-left: 1.0em; padding-right: 1.0em;'><xsl:value-of select="$i"/></td>
                                                <xsl:choose>
                                                    <xsl:when test="./nx:name/text()">
                                                        <td><xsl:value-of select="./nx:name"/></td>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <td>
                                                            <xsl:element name="span">
                                                            <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                            <xsl:attribute name="data-bs-placement">right</xsl:attribute>
                                                            <xsl:attribute name="title">No value entered</xsl:attribute>
                                                                —
                                                            </xsl:element>
                                                        </td>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                                <xsl:choose>
                                                    <xsl:when test="normalize-space(./@ref) != ''">
                                                        <td>
                                                            <xsl:call-template name="link-or-text">
                                                                <xsl:with-param name="val">
                                                                    <xsl:value-of select="./@ref"/>
                                                                </xsl:with-param>
                                                            </xsl:call-template>
                                                        </td>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <td>
                                                            <xsl:element name="span">
                                                                <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                                <xsl:attribute name="data-bs-placement">right</xsl:attribute>
                                                                <xsl:attribute name="title">No value entered</xsl:attribute>
                                                                —
                                                            </xsl:element>
                                                        </td>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                                <xsl:choose>
                                                    <xsl:when test="./nx:description/text()">
                                                        <td>
                                                            <xsl:for-each select="./nx:description">
                                                                <p><xsl:value-of select="."/></p>
                                                            </xsl:for-each>
                                                        </td>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <td>
                                                            <xsl:element name="span">
                                                                <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                                <xsl:attribute name="data-bs-placement">right</xsl:attribute>
                                                                <xsl:attribute name="title">No value entered</xsl:attribute>
                                                                —
                                                            </xsl:element>
                                                        </td>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                                <xsl:choose>
                                                    <xsl:when test="./nx:elements/*">
                                                        <td>
                                                            <xsl:call-template name="elements-to-list">
                                                                <xsl:with-param name="elements">
                                                                    <xsl:copy-of select="./nx:elements/*"/>
                                                                </xsl:with-param>
                                                            </xsl:call-template>
                                                        </td>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <td>
                                                            <xsl:element name="span">
                                                                <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                                <xsl:attribute name="data-bs-placement">right</xsl:attribute>
                                                                <xsl:attribute name="title">No value entered</xsl:attribute>
                                                                —
                                                            </xsl:element>
                                                        </td>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </tr>
                                        </xsl:for-each>
                                            </tbody>
                                        </table>
                                    </xsl:when>
                                </xsl:choose>
                            </table>
                        </xsl:if>

                        <xsl:if test="nx:project/*/text()">
                          <h3 id="proj-info-header">Project Information
                              <xsl:call-template name="help-tip">
                                  <xsl:with-param name="tip-text">Project information is extracted from the user's division and group, as well as the calendar reservation associated with this record</xsl:with-param>
                              </xsl:call-template>
                              <xsl:if test="nx:project/nx:ref/text()">
                                  <xsl:text> </xsl:text>
                                  <sup>
                                      <xsl:element name="a">
                                          <xsl:attribute name="href"><xsl:value-of select="nx:project/nx:ref"/></xsl:attribute>
                                          <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                          <xsl:attribute name="data-bs-placement">top</xsl:attribute>
                                          <xsl:attribute name="title">Link to this project's reference</xsl:attribute>
                                          <i class='fa fa-link'/>
                                      </xsl:element>
                                  </sup>
                              </xsl:if>
                          </h3>

                            <table class="table table-sm upper-table" id="proj-table"
                              style="border-collapse:collapse;width:80%;">
                            <xsl:if test="nx:project/nx:name/text()">
                                  <tr>
                                      <th align="left" class="col-sm-4 parameter-name">Name: </th>
                                      <td align="left" class="col-sm-8">
                                          <xsl:value-of select="nx:project/nx:name/text()"/>
                                      </td>
                                  </tr>
                              </xsl:if>
                            <xsl:if test="nx:project/nx:project_id/text()">
                                  <tr>
                                      <th align="left" class="col-sm-4 parameter-name">ID: </th>
                                      <td align="left" class="col-sm-8">
                                          <xsl:value-of select="nx:project/nx:project_id/text()"/>
                                      </td>
                                  </tr>
                              </xsl:if>
                            <xsl:if test="nx:project/nx:division/text()">
                                  <tr>
                                      <th align="left" class="col-sm-4 parameter-name">Division: </th>
                                      <td align="left" class="col-sm-8">
                                          <xsl:value-of select="nx:project/nx:division/text()"/>
                                      </td>
                                  </tr>
                              </xsl:if>
                            <xsl:if test="nx:project/nx:group/text()">
                                  <tr>
                                      <th align="left" class="col-sm-4 parameter-name">Group: </th>
                                      <td align="left" class="col-sm-8">
                                          <xsl:value-of select="nx:project/nx:group/text()"/>
                                      </td>
                                  </tr>
                              </xsl:if>
                          </table>
                        </xsl:if>
                    </div>

                    <!-- Image gallery showing images from every dataset of the session -->
                    <div class="col-md-6 slideshow-col">
                        <div id="img_gallery">
                            <xsl:for-each select="//nx:dataset[nx:preview]">
                                <xsl:variable name="aa_num" select="count(../preceding-sibling::nx:acquisitionActivity) + 1"/>
                                <figure class="slide">
                                    <img class="nx-img"><xsl:attribute name="src"><xsl:value-of select="$previewBaseUrl"/><xsl:value-of select="nx:preview"/></xsl:attribute></img>
                                    <figcaption class="nx-caption">
                                        <div class="row gallery-caption-row">
                                            <div class="gal-nav-container">
                                               <a  class="gal-nav gal-prev" onclick="window.NexusLIMSDetail.plusSlide(-1); window.NexusLIMSDetail.disable_gallery_tooltips();"
                                                   data-bs-toggle="tooltip" data-bs-placement="left"
                                                   title="The left/right arrow keys can also be used to navigate the image gallery">
                                                   <span class="fa-stack fa-lg">
                                                       <i class="fas fa-circle fa-stack-2x"></i>
                                                       <i class="fas fa-arrow-left fa-stack-1x fa-inverse"></i>
                                                   </span>
                                               </a>
                                            </div>
                                            <xsl:variable name="dataset-number" select="count(ancestor::nx:acquisitionActivity/preceding-sibling::nx:acquisitionActivity/nx:dataset) + count(preceding-sibling::nx:dataset) + 1"/>
                                            <div class="gallery-caption">
                                                <span>Preview <xsl:value-of select="position()"/> of <xsl:value-of select="count(//nx:dataset[nx:preview])" />
                                                    (<xsl:choose>
                                                            <!-- if simple display, make dataset text a link -->
                                                            <xsl:when test="$simpleDisplay">
                                                                <a href="#{generate-id(current())}"
                                                                   data-bs-toggle='tooltip'
                                                                   data-bs-placement='bottom'
                                                                   title='Jump to dataset {$dataset-number} details'
                                                                   onclick='$("#simple-filelist-table tr").removeClass("table-warning"); $("a[name={generate-id(current())}").parent().parent().addClass("table-warning")'>
                                                                    dataset #<xsl:value-of select="$dataset-number"/><xsl:text> </xsl:text>
                                                                    <sup class="link-icon"><i class='fa fa-link'/></sup><xsl:text> </xsl:text>
                                                                </a>
                                                            </xsl:when>
                                                            <!-- if not simple, make dataset text just text -->
                                                            <xsl:otherwise>dataset #<xsl:value-of select="$dataset-number"/></xsl:otherwise>
                                                        </xsl:choose>)
                                                </span>
                                                <code class='gallery-filename'>  <!-- show the name of the file with a fixed width and tooltip of full name -->
                                                    <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                    <xsl:attribute name="data-bs-placement">top</xsl:attribute>
                                                    <xsl:attribute name="title"><xsl:value-of select="./nx:name"/></xsl:attribute>
                                                    <xsl:value-of select="./nx:name"/>
                                                </code>
                                                <xsl:choose>
                                                    <xsl:when test="$simpleDisplay">
                                                        <!-- if simple display, just show activity text -->
                                                        <span>Activity <xsl:value-of select="$aa_num"/> of <xsl:value-of select="count(//nx:acquisitionActivity)"/></span>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <!-- if not simple, make activity text a clickable link -->
                                                        <a href="#{generate-id(..)}"
                                                           data-bs-toggle='tooltip'
                                                           data-bs-placement='bottom'
                                                           title='Jump to activity {$aa_num} in record'>
                                                            Activity <xsl:value-of select="$aa_num"/> of <xsl:value-of select="count(//nx:acquisitionActivity)"/>
                                                            <xsl:text> </xsl:text><sup class="link-icon"><i class='fa fa-link'/></sup></a>
                                                    </xsl:otherwise>
                                                </xsl:choose>

                                            </div>
                                            <div class="gal-nav-container">
                                                <a  class="gal-nav gal-next" onclick="window.NexusLIMSDetail.plusSlide(1); window.NexusLIMSDetail.disable_gallery_tooltips();"
                                                data-bs-toggle="tooltip" data-bs-placement="right"
                                                title="The left/right arrow keys can also be used to navigate the image gallery">
                                                <span class="fa-stack fa-lg">
                                                    <i class="fas fa-circle fa-stack-2x"></i>
                                                    <i class="fas fa-arrow-right fa-stack-1x fa-inverse"></i>
                                                </span>
                                            </a></div>
                                        </div>
                                    </figcaption>
                                </figure>
                            </xsl:for-each>
                        </div>
                    </div>
                </div>
                <hr/>

               <xsl:choose>
                   <xsl:when test="$simpleDisplay">
                        <h3>Dataset Listing
                            <xsl:call-template name="help-tip">
                                <xsl:with-param name="tip-text">This table contains a row for every dataset identified as part of this Experiment, including links to download the dataset itself and its metadata. If available, a link to the preview image is included as well.</xsl:with-param>
                            </xsl:call-template>
                        </h3>
                        <xsl:call-template name="simple-filelist-table"/>
                   </xsl:when>
                   <xsl:otherwise>
                    <!-- Loop through and show details of each acquisition activity -->
                    <xsl:for-each select="nx:acquisitionActivity">
                        <div class="row aa_header_row">
                            <div class="col-md-12">
                                <div class="row">
                                    <xsl:if test="@seqno = 0">
                                        <xsl:attribute name="style">margin-top: -20px;</xsl:attribute>
                                    </xsl:if>
                                    <div class="col-md-6 aa-header-info">
                                        <!-- Generate name id which corresponds to the link associated with the acquisition activity -->
                                        <a class="aa_anchor" name="{generate-id(current())}"/>
                                        <span class="aa_header"><b>Experiment activity <xsl:value-of select="@seqno+1"/></b><xsl:text> </xsl:text></span>

                                        <a href='javascript:void(0)' onclick="$(this).blur(); window.NexusLIMSDetail.openModal('{generate-id(current())}-modal');"
                                           data-bs-toggle='tooltip' data-bs-placement='right'
                                           title="Click to view this activity's setup parameters">
                                           <i class='fa fa-tasks fa-border param-button'/>
                                        </a>
                                        <div style="font-size:15px">Activity contents:
                                            <i>
                                                <xsl:call-template name="parse-activity-contents"></xsl:call-template>
                                            </i>
                                        </div>
                                        <span class="badge list-record-badge">
                                            <xsl:value-of select="count(nx:dataset)"/> data file<xsl:if test="count(nx:dataset) > 1">s</xsl:if>
                                        </span>
                                        <i class="fa fa-cubes" style="margin-left:0.75em; font-size: small;"
                                            data-bs-toggle="tooltip" data-bs-placement="bottom" title="Filetypes present in this activity"/><span style="font-size: small;"><xsl:text>: </xsl:text></span>
                                        <xsl:variable name="this-aa-unique-extensions">
                                            <xsl:call-template name="get-unique-extensions">
                                                <xsl:with-param name="global" select="false()"/>
                                            </xsl:call-template>
                                        </xsl:variable>
                                        <xsl:call-template name="extensions-to-badges">
                                            <xsl:with-param name="input" select="exslt:node-set($this-aa-unique-extensions)"/>
                                        </xsl:call-template>
                                    </div>
                                </div>
                                <div class="row aa-content-row align-items-center" style="margin-top: -20px;">
                                    <!-- preview image column -->
                                    <div class="col-lg-4 aa-img-col">
                                        <xsl:for-each select="nx:dataset">
                                            <!-- only show the first image in this AA's gallery by setting the
                                                "hidden" class on all others -->
                                            <xsl:variable name="classString">
                                                <xsl:choose>
                                                    <xsl:when test="position() > 1">nx-img aa-img hidden</xsl:when>
                                                    <xsl:otherwise>nx-img aa-img visible</xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:variable>
                                            <xsl:element name="img">
                                                <xsl:attribute name="class">
                                                   <xsl:choose>
                                                       <xsl:when test="nx:preview">
                                                           <xsl:value-of select="$classString"/>
                                                       </xsl:when>
                                                       <xsl:otherwise>
                                                           <xsl:value-of select="concat($classString, ' preview-placeholder')"/>
                                                       </xsl:otherwise>
                                                   </xsl:choose>
                                                </xsl:attribute>
                                                <xsl:attribute name="id"><xsl:value-of select="generate-id()"/>-aa-img</xsl:attribute>
                                                <xsl:attribute name="src">
                                                    <xsl:choose>
                                                        <xsl:when test="nx:preview">
                                                            <xsl:value-of select="$previewBaseUrl"/><xsl:value-of select="nx:preview"/>
                                                        </xsl:when>
                                                        <xsl:otherwise></xsl:otherwise>
                                                    </xsl:choose>
                                                </xsl:attribute>
                                            </xsl:element>

                                        </xsl:for-each>

                                    </div>

                                    <!-- dataset listing column -->
                                    <div class="col-lg-8 aa-table-col">
                                        <table class="table table-sm table-hover aa-table compact wrap" border="1"><!-- style="width:100%; border-collapse:collapse;" -->
                                            <thead>
                                                <tr>
                                                    <th>
                                                        Dataset Name
                                                        <xsl:call-template name="help-tip">
                                                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                                                            <xsl:with-param name="tip-text">The name given to the dataset (typically the filename)</xsl:with-param>
                                                        </xsl:call-template>
                                                    </th>
                                                    <th>
                                                        Creation Time
                                                    </th>
                                                    <th>
                                                        Type
                                                        <xsl:call-template name="help-tip">
                                                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                                                            <xsl:with-param name="tip-text">A label indicating the data type of this dataset (taken from a controlled list)</xsl:with-param>
                                                        </xsl:call-template>
                                                    </th>
                                                    <th>
                                                        Role
                                                        <xsl:call-template name="help-tip">
                                                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                                                            <xsl:with-param name="tip-text">A label indicating the experimental role of this dataset (taken from a controlled list)</xsl:with-param>
                                                        </xsl:call-template>
                                                    </th>
                                                    <xsl:choose>
                                                        <xsl:when test="nx:dataset/nx:format/text()">
                                                            <th>
                                                                Format
                                                                <xsl:call-template name="help-tip">
                                                                    <xsl:with-param name="tip-placement">top</xsl:with-param>
                                                                    <xsl:with-param name="tip-text">A string (can be a MIME type) indicating the format of the dataset (e.g. TIFF, DICOM, Excel)</xsl:with-param>
                                                                </xsl:call-template>
                                                            </th>
                                                        </xsl:when>
                                                    </xsl:choose>
                                                    <th class='text-center'><!-- style='padding-right: 1%' -->Meta</th>
                                                    <th class='text-center'><!-- style='padding-right: 1%' -->D/L</th>
                                                </tr>
                                            </thead>
                                            <!-- Loop through each dataset -->
                                            <tbody>
                                                <xsl:for-each select="nx:dataset">
                                                    <tr img-id="{generate-id()}-aa-img">
                                                        <!-- Populate table values with the metadata name and value -->
                                                        <!-- generate a dataset id that matches preview image as an attribute on the first column for accessing later via JS -->
                                                        <xsl:element name="td">
                                                            <xsl:value-of select="nx:name"/>
                                                        </xsl:element>
                                                        <xsl:element name="td">
                                                            <xsl:choose>
                                                                <xsl:when test="nx:meta[@name = 'Creation Time']">
                                                                    <xsl:variable name="dt" select="string(nx:meta[@name = 'Creation Time'])"/>
                                                                    <xsl:value-of select="concat(
                                                                        substring($dt,1,10),' ',
                                                                        substring($dt,12,5))" />
                                                                </xsl:when>
                                                                <xsl:when test="../nx:setup/nx:param[@name = 'Creation Time']">
                                                                    <xsl:variable name="dt" select="string(../nx:setup/nx:param[@name = 'Creation Time'])"/>
                                                                    <xsl:value-of select="concat(
                                                                        substring($dt,1,10),' ',
                                                                        substring($dt,12,5))" />
                                                                </xsl:when>
                                                                <xsl:otherwise>---</xsl:otherwise>
                                                            </xsl:choose>
                                                        </xsl:element>
                                                        <xsl:variable name="dataset-type">
                                                            <xsl:choose>
                                                                <xsl:when test="string(@type) = 'SpectrumImage'">Spectrum Image</xsl:when>
                                                                <xsl:otherwise><xsl:value-of select="@type"/></xsl:otherwise>
                                                            </xsl:choose>
                                                        </xsl:variable>
                                                        <td><xsl:value-of select="$dataset-type"/></td>
                                                        <td><xsl:value-of select="@role"/></td>
                                                        <xsl:choose>
                                                            <xsl:when test="../nx:dataset/nx:format/text()">
                                                                <td><xsl:value-of select="nx:format/text()"/></td>
                                                            </xsl:when>
                                                        </xsl:choose>
                                                        <td class='text-center aa-meta-col'>
                                                            <!-- Modal content inside of table, since it needs to be in the context of this dataset -->
                                                            <a href='javascript:void(0)' onclick="$(this).blur(); window.NexusLIMSDetail.openModal('{generate-id(current())}-modal');"
                                                            data-bs-toggle='tooltip' data-bs-placement='left'
                                                            title="Click to view this dataset's unique metadata">
                                                                <i class='fa fa-tasks fa-border param-button' style='margin-left:0;'/>
                                                            </a>
                                                            <xsl:variable name="json-location-raw">
                                                                <xsl:choose>
                                                                    <xsl:when test="nx:preview">
                                                                        <xsl:value-of select="$previewBaseUrl"/>
                                                                        <xsl:value-of select="substring-before(nx:preview, '.thumb.png')"/>
                                                                        <xsl:text>.json</xsl:text>
                                                                    </xsl:when>
                                                                    <xsl:otherwise>
                                                                        <xsl:value-of select="$previewBaseUrl"/>
                                                                        <xsl:value-of select="nx:location"/>
                                                                        <xsl:text>.json</xsl:text>
                                                                    </xsl:otherwise>
                                                                </xsl:choose>
                                                            </xsl:variable>
                                                            <xsl:variable name="json-location" select="normalize-space($json-location-raw)"/>
                                                            <xsl:element name='a'>
                                                                <xsl:attribute name="href"><xsl:value-of select="$json-location"/></xsl:attribute>
                                                                <xsl:attribute name="onclick">
                                                                    $(this).blur()
                                                                </xsl:attribute>
                                                                <xsl:attribute name="target">_blank</xsl:attribute>
                                                                <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                                <xsl:attribute name="data-bs-placement">right</xsl:attribute>
                                                                <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                                                <xsl:attribute name="title">Click to download this dataset's metadata in JSON format</xsl:attribute>
                                                                <i class='fa fa-download fa-border param-button' style='margin-left:0;'/>
                                                            </xsl:element>
                                                            <div id="{generate-id(current())}-modal" class="nexuslims-modal dataset-meta-modal">
                                                                <div class="modal-content">
                                                                    <div class="container-fluid">
                                                                        <div class="d-flex justify-content-between align-items-start">
                                                                            <h5 class="modal-title"><xsl:value-of select="nx:name"/></h5>
                                                                            <i class="close-modal fas fa-times" onclick="window.NexusLIMSDetail.closeModal('{generate-id(current())}-modal')"/>
                                                                        </div>
                                                                        <xsl:if test="nx:description/text()">
                                                                            <div class="row">
                                                                                <div class='col-12' style=''>
                                                                                    <div style="font-size:15px">Dataset description:
                                                                                        <i><xsl:value-of select="nx:description"/></i>
                                                                                    </div>
                                                                                </div>
                                                                            </div>
                                                                        </xsl:if>
                                                                        <div class="row" style="justify-content: center;">
                                                                            <div class='col-12 meta-table-col' style="">
                                                                                <!-- Generate the table with setup conditions for each acquisition activity -->
                                                                                <table class="table table-sm table-hover meta-table compact text-start" border="1"><!-- style="" -->
                                                                                    <thead>
                                                                                        <tr>
                                                                                            <th>Metadata Parameter
                                                                                                <xsl:call-template name="help-tip">
                                                                                                    <xsl:with-param name="tip-placement">right</xsl:with-param>
                                                                                                    <xsl:with-param name="tip-text">The following metadata values are those (within an activity) that are unique to each dataset</xsl:with-param>
                                                                                                </xsl:call-template></th>
                                                                                            <th>Value</th>
                                                                                        </tr>
                                                                                    </thead>
                                                                                    <tbody>
                                                                                        <xsl:for-each select="nx:meta">
    <!--                                                                                        <xsl:sort select="@name"/>
                                                                                                Don't sort here because xsl is case-sensitive, which isn't what we want
    -->
                                                                                            <tr>
                                                                                                <!-- Populate table values with the metadata name and value -->
                                                                                                <td><b><xsl:value-of select="@name"/>
                                                                                                <xsl:if test="@unit">
                                                                                                    <xsl:text> (</xsl:text>
                                                                                                    <xsl:value-of select="@unit"/>
                                                                                                    <xsl:text>)</xsl:text>
                                                                                                </xsl:if></b>
                                                                                                <!-- If this parameter has a warning attribute, then add warning tooltip -->
                                                                                                <xsl:if test="@warning = 'true'"><xsl:text> </xsl:text>
                                                                                                    <xsl:call-template name="warning-tip">
                                                                                                        <xsl:with-param name="tip-placement">right</xsl:with-param>
                                                                                                        <xsl:with-param name="tip-text">This parameter is known to be unreliable, so use its value with caution</xsl:with-param>
                                                                                                    </xsl:call-template>
                                                                                                </xsl:if>
                                                                                                </td>
                                                                                                <td>
                                                                                                    <xsl:attribute name="class">
                                                                                                        <xsl:if test="@warning = 'true'">has-warning</xsl:if>
                                                                                                    </xsl:attribute>
                                                                                                    <xsl:choose>
                                                                                                        <!-- If metadata tag is "Data Type", then replace '_' with ' ' -->
                                                                                                        <xsl:when test="@name = 'Data Type'">
                                                                                                            <xsl:call-template name="string-replace-all">
                                                                                                                <xsl:with-param name="text"><xsl:value-of select="current()"/></xsl:with-param>
                                                                                                                <xsl:with-param name="replace" select="'_'" />
                                                                                                                <xsl:with-param name="by" select="' '" />
                                                                                                            </xsl:call-template>
                                                                                                        </xsl:when>
                                                                                                        <!-- If Creation Time, format more nicely -->
                                                                                                        <xsl:when test="@name = 'Creation Time'">
                                                                                                            <xsl:variable name="dt" select="string(current())"/>
                                                                                                            <xsl:value-of select="concat(
                                                                                                                substring($dt,1,10),' ',
                                                                                                                substring($dt,12,5))" />
                                                                                                        </xsl:when>
                                                                                                        <xsl:otherwise>
                                                                                                            <xsl:value-of select="current()"/>
                                                                                                        </xsl:otherwise>
                                                                                                    </xsl:choose>
                                                                                                </td>
                                                                                            </tr>
                                                                                        </xsl:for-each>
                                                                                    </tbody>
                                                                                </table>
                                                                            </div>
                                                                        </div>
                                                                        <div class='row'
                                                                             style="justify-content: center;">
                                                                            <div class='col-12 text-center mt-3 missing-metadata'>
                                                                                <xsl:element name='a'>
                                                                                    <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                                                    <xsl:attribute name="data-bs-placement">top</xsl:attribute>
                                                                                    <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                                                                    <xsl:attribute name="title">This table only shows metadata values unique to each dataset in this activity. All other metadata values that were common to all files in this activity can be viewed by clicking the "view metadata" button in the header for this activity (look for the <xsl:text disable-output-escaping="yes">&lt;i class="fa fa-tasks fa-border"&gt;&lt;/i&gt;</xsl:text> icon).</xsl:attribute>
                                                                                    <i class='fa fa-question-circle' style=''/>
                                                                                    Missing metadata?
                                                                                </xsl:element>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </td>
                                                        <td class='text-center aa-dl-col'>
                                                            <xsl:element name='a'>
                                                                <xsl:attribute name="href"><xsl:value-of select="$datasetBaseUrl"/><xsl:value-of select="nx:location"/></xsl:attribute>
                                                                <xsl:attribute name="onclick">
                                                                    $(this).blur()
                                                                </xsl:attribute>
                                                                <xsl:attribute name="download"/>
                                                                <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                                <xsl:attribute name="data-bs-placement">right</xsl:attribute>
                                                                <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                                                <xsl:attribute name="title">Click to download &#013;<xsl:value-of select='nx:name'/></xsl:attribute>
                                                                <i class='fa fa-download fa-border param-button' style='margin-left:0;'/>
                                                            </xsl:element>
                                                        </td>
                                                    </tr>
                                                </xsl:for-each>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            <!-- Generate unique modal box for each AA which contains the setup params, accessed via a button -->
                            <div id="{generate-id(current())}-modal" class="nexuslims-modal aa-setup-params-modal">
                                <div class="modal-content">
                                    <div class="container-fluid">
                                        <div class="d-flex justify-content-between align-items-start">
                                            <h5 class="modal-title">Experiment activity <xsl:value-of select="@seqno+1"/></h5>
                                            <i class="close-modal fas fa-times" onclick="window.NexusLIMSDetail.closeModal('{generate-id(current())}-modal')"/>
                                        </div>
                                        <div class="row">
                                            <div class='col-12' style=''>
                                                <div style="font-size:15px">Activity contents:
                                                    <i>
                                                        <xsl:call-template name="parse-activity-contents"></xsl:call-template>
                                                    </i>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row" style="justify-content: center;">
                                            <div class='col-12 meta-table-col' style="">
                                                <!-- Generate the table with setup conditions for each acquisition activity -->
                                                <table class="table table-sm table-hover meta-table compact text-start" border="1"><!-- style="" -->
                                                    <thead>
                                                        <tr>
                                                            <th>Setup Parameter
                                                            <xsl:call-template name="help-tip">
                                                                <xsl:with-param name="tip-placement">right</xsl:with-param>
                                                                <xsl:with-param name="tip-text">Setup parameters are defined as those metadata values that are common between all datasets within a given activity</xsl:with-param>
                                                            </xsl:call-template></th>
                                                            <th>Value</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        <tr>
                                                            <td><b>Start time</b></td>
                                                            <td>
                                                                <xsl:variable name="dt">
                                                                  <xsl:call-template name="tokenize-select">
                                                                  <xsl:with-param name="text" select="nx:startTime"/>
                                                                    <xsl:with-param name="delim">T</xsl:with-param>
                                                                    <xsl:with-param name="i" select="2"/>
                                                                  </xsl:call-template>
                                                                </xsl:variable>
                                                                <xsl:value-of select="substring($dt,1,8)" />
                                                            </td>
                                                        </tr>
                                                        <!-- Loop through each setup value under the 'param' heading -->
                                                        <xsl:for-each select="nx:setup/nx:param">
    <!--                                                        <xsl:sort select="@name"/>
                                                                Don't sort here because xsl is case-sensitive, which isn't what we want
    -->
                                                            <tr>
                                                                <!-- Populate setup table with parameter name and value -->
                                                                <td><b><xsl:value-of select="@name"/>
                                                                <xsl:if test="@unit">
                                                                    <xsl:text> (</xsl:text>
                                                                    <xsl:value-of select="@unit"/>
                                                                    <xsl:text>)</xsl:text>
                                                                </xsl:if></b>
                                                                <xsl:if test="@warning = 'true'"><xsl:text> </xsl:text>
                                                                    <xsl:call-template name="warning-tip">
                                                                        <xsl:with-param name="tip-placement">right</xsl:with-param>
                                                                        <xsl:with-param name="tip-text">This parameter is known to be unreliable, so use its value with caution</xsl:with-param>
                                                                    </xsl:call-template>
                                                                </xsl:if>
                                                                </td>
                                                                <td>
                                                                    <xsl:attribute name="class">
                                                                        <xsl:if test="@warning = 'true'">has-warning</xsl:if>
                                                                    </xsl:attribute>
                                                                    <!-- If metadata tag is "Data Type", then replace '_' with ' ' -->
                                                                    <xsl:choose>
                                                                        <xsl:when test="@name = 'Data Type'">
                                                                            <xsl:call-template name="string-replace-all">
                                                                                <xsl:with-param name="text"><xsl:value-of select="current()"/></xsl:with-param>
                                                                                <xsl:with-param name="replace" select="'_'" />
                                                                                <xsl:with-param name="by" select="' '" />
                                                                            </xsl:call-template>
                                                                        </xsl:when>
                                                                        <xsl:otherwise>
                                                                            <xsl:value-of select="current()"/>
                                                                        </xsl:otherwise>
                                                                    </xsl:choose></td>
                                                            </tr>
                                                        </xsl:for-each>
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                        <div class='row' style="justify-content: center;">
                                            <div class='col-12 text-center mt-3 missing-metadata'>
                                                <xsl:element name='a'>
                                                    <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                    <xsl:attribute name="data-bs-placement">top</xsl:attribute>
                                                    <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                                    <xsl:attribute name="title">This table only shows metadata values common to all files in this activity. For metadata specific to each dataset, click the metadata table button for that dataset in the table below (look for the <xsl:text disable-output-escaping="yes">&lt;i class="fa fa-tasks fa-border"&gt;&lt;/i&gt;</xsl:text> icon).</xsl:attribute>
                                                    <i class='fa fa-question-circle' style=''/>
                                                    Missing metadata?
                                                </xsl:element>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </xsl:for-each>
                   </xsl:otherwise>
               </xsl:choose>
               <xsl:if test="not($simpleDisplay)">

                  <div id="filelist-modal" class="nexuslims-modal">
                      <div class="modal-content" style="width: 65vw;">
                          <div class="modal-body">
                              <div class="d-flex justify-content-between align-items-start mb-2">
                                  <div>
                                  <strong>Complete filelisting for:</strong><br/>
                                  <span class='dl-modal-title'>
                                      <i class="far fa-file-alt results-icon"/>
                                      <xsl:value-of select="$expTitle"/>
                                  </span> - <span class='dl-modal-date'><xsl:value-of select="$date"/></span><br/>
                                  <span class='dl-modal-title' style="white-space: pre-line;">Root path:  </span><code id='filelist-rootpath'
                                      style="line-height: 1.25em; display: inline;"><a>
                                      <xsl:attribute name="href">
                                          <xsl:value-of select="$datasetBaseUrl"/>
                                      </xsl:attribute>
                                      <xsl:attribute name="download"/>
                                      <xsl:attribute name="target">_blank</xsl:attribute>
                                      <xsl:attribute name="class">help-tip</xsl:attribute>
                                      <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                      <xsl:attribute name="data-bs-placement">top</xsl:attribute>
                                      <xsl:attribute name="title">Click to view directory structure directly in the browser</xsl:attribute>
                                      <xsl:attribute name="onclick">this.blur()</xsl:attribute>
                                  </a></code>
                                  </div>
                                  <div class="d-flex align-items-center">
                                      <i class="help-filelist-modal fas fa-question-circle me-3">
                                          <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                          <xsl:attribute name="data-bs-placement">bottom</xsl:attribute>
                                          <xsl:attribute name="data-bs-container">.help-filelist-modal</xsl:attribute>
                                          <xsl:attribute name="title">
                                              <xsl:text>This window shows all the datasets identified as part of this record.&#10;&#10;</xsl:text>
                                              <xsl:text>Rows of the table can be selected by clicking anywhere within the row with the mouse. Multiple rows can be selected by holding shift while clicking.&#10;&#10;</xsl:text>
                                              <xsl:text>The files (and metadata) associated with the selected datasets can be downloaded by clicking on the "Download selected" or "Download all" button (warning, this may take some time for large amounts of data). You can close this dialogue (but not the browser tab!) while the download is processing without interrupting its progress. Do not navigate away from the page, or the download will cancel!&#10;&#10;</xsl:text>
                                              <xsl:text>The textual data from the selected rows (not the actual files) can also be exported to the clipboard, a CSV file, an Excel file, or printed to PDF by using the respective buttons as well.</xsl:text>
                                          </xsl:attribute>
                                      </i>
                                      <i class="close-modal fas fa-times" onclick="window.NexusLIMSDetail.closeModal('filelist-modal')"/>
                                  </div>
                              </div>
                              <!-- Download progressbar row ((hidden by default by jQuery) -->
                              <div id='progressbar-row' class='row g-0'>
                                  <div class='col-12'>
                                      <div class="progress mb-1" id="progress_bar">
                                          <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%">
                                              0%
                                          </div>
                                      </div>
                                  </div>
                              </div>
                              <!-- Download cancel button row (hidden by default by jQuery) -->
                              <div id='btn-cancel-row' class='row g-0'>
                                  <div class='col-12 mt-0 mb-0'>
                                      <button id="btn-cancel-dl" class="btn btn-danger" type="button"
                                              data-bs-toggle="tooltip" data-bs-placement="right"
                                              title="Canceling the download through the browser will not work, so be sure to use this button to actually stop the file transfer"><i class='fa fa-ban menu-fa' aria-hidden="true"/><span>Cancel download</span></button>
                                  </div>
                              </div>
                              <!-- Download result text row (hidden by default by jQuery) -->
                              <div id='dl-result-row' class='row g-0'>
                                  <div class='col-12 mt-0 mb-0'>
                                      <p id="download-result" class="mt-1 mb-1"></p>
                                  </div>
                              </div>
                              <!-- Download extra message row (hidden by default by jQuery) -->
                              <div id='dl-extra-row' class='row g-0'>
                                  <div class='col-12 mt-0 mb-0'>
                                      <p id="download-extra" class="mt-1 mb-1"></p>
                                  </div>
                              </div>
                              <div class="row g-0 mt-0">
                                  <div class='col-12 pt-0'>
                                      <!-- Generate the filelist table -->
                                      <table id="filelist-table"
                                             class="table table-sm table-hover filelist-table compact mt-0"
                                             width="100%"
                                             border="1"><!-- style="" -->
                                          <thead>
                                              <tr>
                                                  <th></th>
                                                  <th>
                                                      Dataset Name
                                                      <xsl:call-template name="help-tip">
                                                          <xsl:with-param name="tip-placement">top</xsl:with-param>
                                                          <xsl:with-param name="tip-text">The name given to the dataset (typically the filename)</xsl:with-param>
                                                      </xsl:call-template>
                                                  </th>
                                                  <th>
                                                      Path
                                                      <xsl:call-template name="help-tip">
                                                          <xsl:with-param name="tip-placement">top</xsl:with-param>
                                                          <xsl:with-param name="tip-text">The path (relative to root path, above) containing this dataset (click to view directly in browser)</xsl:with-param>
                                                      </xsl:call-template>
                                                  </th>
                                                  <th id='filelist-size-col'>
                                                      Size
                                                  </th>
                                                  <th id='filelist-type-col'>
                                                      Type
                                                      <xsl:call-template name="help-tip">
                                                          <xsl:with-param name="tip-placement">top</xsl:with-param>
                                                          <xsl:with-param name="tip-text">A label indicating the data type of this dataset (taken from a controlled list)</xsl:with-param>
                                                      </xsl:call-template>
                                                  </th>
                                                  <xsl:choose>
                                                      <xsl:when test="//nx:dataset/nx:format/text()">
                                                          <th id='filelist-format-col'>
                                                              Format
                                                              <xsl:call-template name="help-tip">
                                                                  <xsl:with-param name="tip-placement">top</xsl:with-param>
                                                                  <xsl:with-param name="tip-text">A string (can be a MIME type) indicating the format of the dataset (e.g. TIFF, DICOM, Excel)</xsl:with-param>
                                                              </xsl:call-template>
                                                          </th>
                                                      </xsl:when>
                                                  </xsl:choose>
                                                  <th class='text-center' id='filelist-json_dl-col'>Meta</th>
                                                  <th class='text-center' id='filelist-data_dl-col'>D/L</th>
                                              </tr>
                                          </thead>
                                          <tbody>
                                              <xsl:for-each select="//nx:dataset">
                                                  <tr>
                                                      <td></td>
                                                      <xsl:element name="td">
                                                          <xsl:value-of select="nx:name"/>
                                                      </xsl:element>
                                                      <td class='filepath'>
                                                          <code>
                                                              <a>
                                                                  <xsl:attribute name="href">
                                                                      <xsl:value-of select="$datasetBaseUrl"/>
                                                                  </xsl:attribute>
                                                                  <xsl:attribute name="download"/>
                                                                  <xsl:attribute name="target">_blank</xsl:attribute>
                                                                  <xsl:call-template name="get-path-of-file">
                                                                      <xsl:with-param name="absolute_filename">
                                                                          <xsl:value-of select="nx:location"/>
                                                                      </xsl:with-param>
                                                                  </xsl:call-template>
                                                              </a>
                                                          </code>
                                                      </td>
                                                      <td>

                                                      </td>
                                                      <xsl:variable name="dataset-type">
                                                          <xsl:choose>
                                                              <xsl:when test="string(@type) = 'SpectrumImage'">Spectrum Image</xsl:when>
                                                              <xsl:otherwise><xsl:value-of select="@type"/></xsl:otherwise>
                                                          </xsl:choose>
                                                      </xsl:variable>
                                                      <td><xsl:value-of select="$dataset-type"/></td>
                                                      <xsl:choose>
                                                          <xsl:when test="../nx:dataset/nx:format/text()">
                                                              <td><xsl:value-of select="nx:format/text()"/></td>
                                                          </xsl:when>
                                                      </xsl:choose>
                                                      <td class='text-center'>
                                                          <xsl:variable name="json-location-raw">
                                                              <xsl:choose>
                                                                  <xsl:when test="nx:preview">
                                                                      <xsl:value-of select="$previewBaseUrl"/>
                                                                      <xsl:value-of select="substring-before(nx:preview, '.thumb.png')"/>
                                                                      <xsl:text>.json</xsl:text>
                                                                  </xsl:when>
                                                                  <xsl:otherwise>
                                                                      <xsl:value-of select="$previewBaseUrl"/>
                                                                      <xsl:value-of select="nx:location"/>
                                                                      <xsl:text>.json</xsl:text>
                                                                  </xsl:otherwise>
                                                              </xsl:choose>
                                                          </xsl:variable>
                                                          <xsl:variable name="json-location" select="normalize-space($json-location-raw)"/>
                                                          <xsl:element name='a'>
                                                              <xsl:attribute name="href"><xsl:value-of select="$json-location"/></xsl:attribute>
                                                              <xsl:attribute name="onclick">
                                                                  $(this).blur()
                                                              </xsl:attribute>
                                                              <xsl:attribute name="target">_blank</xsl:attribute>
                                                              <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                              <xsl:attribute name="data-bs-placement">left</xsl:attribute>
                                                              <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                                              <xsl:attribute name="title">Click to download this dataset's metadata in JSON format</xsl:attribute>
                                                              <i class='fa fa-download fa-border param-button' style='margin-left:0;'/>
                                                          </xsl:element>
                                                      </td>
                                                      <td class='text-center'>
                                                          <xsl:element name='a'>
                                                              <xsl:attribute name='class'>filelisting-dl-cell</xsl:attribute>
                                                              <xsl:attribute name="href"><xsl:value-of select="$datasetBaseUrl"/><xsl:value-of select="nx:location"/></xsl:attribute>
                                                              <xsl:attribute name="onclick">
                                                                  $(this).blur()
                                                              </xsl:attribute>
                                                              <xsl:attribute name="download"/>
                                                              <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                                              <xsl:attribute name="data-bs-placement">left</xsl:attribute>
                                                              <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                                              <xsl:attribute name="title">Click to download &#013;<xsl:value-of select='nx:name'/></xsl:attribute>
                                                              <i class='fa fa-download fa-border param-button' style='margin-left:0;'/>
                                                          </xsl:element>
                                                      </td>
                                                  </tr>
                                              </xsl:for-each>
                                          </tbody>
                                      </table>
                                  </div>
                              </div>
                          </div>
                      </div>
                  </div>

               </xsl:if>
            </div>
            </div>

            <!-- Javascript which supports some capabilities on the generated page -->
        </div>
    </xsl:template>

    <!--
      - Format a date given in yyyy-mm-dd format to a text-based format
      - e.g. "2019-10-04" becomes "October 4, 2019"
      - @param date   the date to parse
      -->
    <xsl:template name="localize-date">
        <xsl:param name="date"/>
        <xsl:variable name="month-num">
            <xsl:call-template name="tokenize-select">
                <xsl:with-param name="text">
                    <xsl:value-of select="$date"/>
                </xsl:with-param>
                <xsl:with-param name="delim" select="'-'"/>
                <xsl:with-param name="i" select="2"/>
            </xsl:call-template>
        </xsl:variable>

        <!-- The 'for-each document' bit is required because keys only work in the context of the current
                 document in XSLT 1.0 (see https://stackoverflow.com/a/35327827/1435788) -->
        <xsl:for-each select="document('')">
            <xsl:value-of select="key('lookup.date.month', $month-num)"/>
        </xsl:for-each>
        <xsl:text> </xsl:text>
        <xsl:call-template name="tokenize-select">
            <xsl:with-param name="text">
                <xsl:value-of select="$date"/>
            </xsl:with-param>
            <xsl:with-param name="delim" select="'-'"/>
            <xsl:with-param name="i" select="3"/>
        </xsl:call-template>
        <xsl:text>, </xsl:text>
        <xsl:call-template name="tokenize-select">
            <xsl:with-param name="text">
                <xsl:value-of select="$date"/>
            </xsl:with-param>
            <xsl:with-param name="delim" select="'-'"/>
            <xsl:with-param name="i" select="1"/>
        </xsl:call-template>
    </xsl:template>

    <!--
        Tokenize a path that's forward-slash separated
        into progressively longer parts "/", "/first",
        "/first/second", etc.
    -->
    <xsl:template name="tokenize-path">
        <xsl:param name="path"/>
        <xsl:param name="separator" select="'/'"/>
        <xsl:param name="prepend" select="''"/>

        <xsl:choose>
            <xsl:when test="not(contains($path, $separator))">
                <item>
                    <xsl:value-of select="concat(concat($prepend, $separator), normalize-space($path))"/>
                </item>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="this-part" select="concat($prepend,  normalize-space(substring-before($path, $separator)))"/>
                <item>
                    <xsl:choose>
                        <xsl:when test="$this-part = ''">
                            <xsl:value-of select="$separator"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$this-part"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </item>
                <xsl:call-template name="tokenize-path">
                    <xsl:with-param name="path" select="substring-after($path, $separator)"/>
                    <xsl:with-param name="prepend" select="concat($this-part, $separator)"/>
                </xsl:call-template>
            </xsl:otherwise>
            </xsl:choose>
    </xsl:template>

    <!--
      - split a string by a given delimiter and then select out a given
      - element
      - @param text   the text to split
      - @param delim  the delimiter to split by (default: a single space)
      - @param i      the number of the element in the split array desired,
      -               where 1 is the first element (default: 1)
      -->
    <xsl:template name="tokenize-select">
      <xsl:param name="text"/>
      <xsl:param name="delim" select="' '"/>
      <xsl:param name="i" select="1"/>

      <xsl:choose>

        <!-- we want the first element; we can deliver it  -->
        <xsl:when test="$i=1">
          <xsl:choose>
            <xsl:when test="contains($text,$delim)">
              <xsl:value-of select="substring-before($text,$delim)"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$text"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>

        <!-- should not happen -->
        <xsl:when test="$i &lt;= 1"/>

        <!-- need an element that's not first one; strip off the first element
             and recurse into this function -->
        <xsl:otherwise>
          <xsl:call-template name="tokenize-select">
            <xsl:with-param name="text">
              <xsl:value-of select="substring-after($text,$delim)"/>
            </xsl:with-param>
            <xsl:with-param name="delim" select="$delim"/>
            <xsl:with-param name="i" select="$i - 1"/>
          </xsl:call-template>
        </xsl:otherwise>

      </xsl:choose>
    </xsl:template>

    <xsl:template name="get-unique-extensions">
        <xsl:param name="global" select="true()"/>
        <xsl:variable name="selection">
            <xsl:choose>
                <xsl:when test="$global">
                    <xsl:copy-of select="//nx:dataset/nx:location"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy-of select="nx:dataset/nx:location"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="extension-fragment">
            <xsl:element name="extensions">
                <xsl:for-each select="exslt:node-set($selection)/nx:location">
                    <xsl:call-template name="get-file-extension">
                        <xsl:with-param name="path">
                            <xsl:value-of select="."/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:element>
        </xsl:variable>

        <xsl:element name="extensionCount">
            <xsl:for-each select="exslt:node-set($extension-fragment)/extensions/ext[not(preceding::value = value)]">
                <xsl:sort select="value/text()"/>
                <xsl:variable name="thisExtension" select="value/text()"/>
                <xsl:variable name="thisCount" select="count(exslt:node-set($extension-fragment)/extensions/ext[value = $thisExtension])"/>
                <xsl:element name="extension">
                    <xsl:attribute name="count">
                        <xsl:value-of select="$thisCount"/>
                    </xsl:attribute>
                    <xsl:value-of select="$thisExtension"/>
                </xsl:element>
            </xsl:for-each>
        </xsl:element>
    </xsl:template>

    <xsl:template name="get-file-extension">
        <xsl:param name="path"/>
        <xsl:choose>
            <xsl:when test="contains($path, '/')">
                <xsl:call-template name="get-file-extension">
                    <xsl:with-param name="path" select="substring-after($path, '/')"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="contains($path, '.')">
                <xsl:call-template name="TEMP">
                    <xsl:with-param name="x" select="substring-after($path, '.')"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>No extension</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <xsl:template name="TEMP">
        <xsl:param name="x"/>
        <xsl:choose>
            <xsl:when test="contains($x, '.')">
                <xsl:call-template name="TEMP">
                    <xsl:with-param name="x" select="substring-after($x, '.')"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:element name="ext">
                    <xsl:element name="value">
                        <xsl:value-of select="$x"/>
                    </xsl:element>
                </xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="extensions-to-badges">
        <!--  needs to process an input like

<extensionCount>
  <extension count="12">tif</extension>
  <extension count="3">dm3</extension>
</extensionCount>

-->
        <xsl:param name="input"/>
        <xsl:for-each select="$input/extensionCount/extension">
            <span style="white-space:nowrap;">
                <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                <xsl:attribute name="data-bs-placement">bottom</xsl:attribute>
                <xsl:variable name="extension" select="./text()"/>
                <xsl:variable name="tooltip-row" select='$extension-to-tooltip-lookup/row[@ext = $extension]' />
                <xsl:attribute name="title">
                    <xsl:choose>
                        <xsl:when test="not($tooltip-row)">
                            <xsl:text>File extension</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$tooltip-row/@tooltip"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
                <span class="badge-left badge list-record-badge">
                    <xsl:value-of select="@count"/>
                </span>
                <span class="badge-right badge list-record-badge">
                    <xsl:value-of select="./text()"/>
                </span>
            </span>

        </xsl:for-each>

    </xsl:template>

    <xsl:template name="dedup-list">
        <!-- Cribbed from https://www.oxygenxml.com/archives/xsl-list/200412/msg00888.html -->
        <xsl:param name="input"/>
        <xsl:param name="to-keep"/>
        <xsl:choose>
            <!-- Our string contains a space, so there are more values to process -->
            <xsl:when test="contains($input, ' ')">
                <!-- Value to test is substring-before -->
                <xsl:variable name="firstWord" select="substring-before($input, ' ')"/>

                <xsl:choose>
                    <xsl:when test="not(contains($to-keep, $firstWord))">
                        <xsl:variable name="newString">
                            <xsl:choose>
                                <xsl:when test="string-length($to-keep) = 0">
                                    <xsl:value-of select="$firstWord"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="$to-keep"/>
                                    <xsl:text> </xsl:text>
                                    <xsl:value-of select="$firstWord"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:variable>
                        <xsl:call-template name="dedup-list">
                            <xsl:with-param name="input" select="substring-after($input, ' ')"/>
                            <xsl:with-param name="to-keep" select="$newString"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="dedup-list">
                            <xsl:with-param name="input" select="substring-after($input, ' ')"/>
                            <xsl:with-param name="to-keep" select="$to-keep"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="string-length($to-keep) = 0">
                        <xsl:value-of select="$input"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="contains($to-keep, $input)">
                                <xsl:value-of select="$to-keep"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$to-keep"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="$input"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="substring-after-last">
        <xsl:param name="string"/>
        <xsl:param name="char"/>

        <xsl:choose>
            <xsl:when test="contains($string, $char)">
                <xsl:call-template name="substring-after-last">
                    <xsl:with-param name="string" select="substring-after($string, $char)"/>
                    <xsl:with-param name="char" select="$char"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$string"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="get-path-of-file">
        <xsl:param name="absolute_filename"/>
        <xsl:variable name="just-filename">
            <xsl:call-template name="substring-after-last">
                <xsl:with-param name="char">/</xsl:with-param>
                <xsl:with-param name="string"><xsl:value-of select="$absolute_filename"/></xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <xsl:value-of select="substring($absolute_filename, 0, string-length($absolute_filename) - string-length($just-filename))"/>
    </xsl:template>

    <xsl:template name="help-tip">
        <xsl:param name="tip-text"/>
        <xsl:param name="tip-placement" select='"right"'></xsl:param>
        <xsl:element name="sup">
            <xsl:attribute name="class">help-tip</xsl:attribute>
            <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
            <xsl:attribute name="data-bs-placement"><xsl:value-of select="$tip-placement"/></xsl:attribute>
            <xsl:attribute name="title"><xsl:value-of select="$tip-text"/></xsl:attribute>
            <i class='fa fa-question-circle'/>
        </xsl:element>
    </xsl:template>

    <xsl:template name="warning-tip">
        <xsl:param name="tip-text"/>
        <xsl:param name="tip-placement" select='"right"'></xsl:param>
        <xsl:element name="sup">
            <xsl:attribute name="class">warning-tip</xsl:attribute>
            <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
            <xsl:attribute name="data-bs-placement"><xsl:value-of select="$tip-placement"/></xsl:attribute>
            <xsl:attribute name="title"><xsl:value-of select="$tip-text"/></xsl:attribute>
            <i class='fa fa-exclamation-triangle'/>
        </xsl:element>
    </xsl:template>

    <xsl:template name="parse-activity-contents">
        <xsl:choose>
            <xsl:when test="nx:setup/nx:param[@name='Data Type']">
                <xsl:call-template name="string-replace-all">
                    <xsl:with-param name="text" select="nx:setup/nx:param[@name='Data Type']/text()"/>
                    <xsl:with-param name="replace" select="'_'" />
                    <xsl:with-param name="by" select="' '" />
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="this-aa-data-types">
                    <xsl:for-each select="./nx:dataset/nx:meta[@name='Data Type']"><xsl:value-of select="."/><xsl:text> </xsl:text></xsl:for-each>
                </xsl:variable>
                <xsl:variable name="deduped-data-types">
                    <xsl:call-template name="dedup-list">
                        <xsl:with-param name="input">
                            <xsl:value-of select="$this-aa-data-types"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="comma-separated-list">
                    <xsl:call-template name="string-replace-all">
                        <xsl:with-param name="text" select="$deduped-data-types"/>
                        <xsl:with-param name="replace" select="' '" />
                        <xsl:with-param name="by" select="', '" />
                    </xsl:call-template>
                </xsl:variable>
                <xsl:call-template name="string-replace-all">
                    <xsl:with-param name="text" select="$comma-separated-list"/>
                    <xsl:with-param name="replace" select="'_'" />
                    <xsl:with-param name="by" select="' '" />
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Taken from http://geekswithblogs.net/Erik/archive/2008/04/01/120915.aspx -->
    <xsl:template name="string-replace-all">
        <xsl:param name="text" />
        <xsl:param name="replace" />
        <xsl:param name="by" />
        <xsl:choose>
            <xsl:when test="contains($text, $replace)">
                <xsl:value-of select="substring-before($text,$replace)" />
                <xsl:value-of select="$by" />
                <xsl:call-template name="string-replace-all">
                    <xsl:with-param name="text"
                        select="substring-after($text,$replace)" />
                    <xsl:with-param name="replace" select="$replace" />
                    <xsl:with-param name="by" select="$by" />
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="strip-tags">
        <xsl:param name="text"/>
        <xsl:comment>From https://ehikioya.com/remove-html-tags-xsl-value/</xsl:comment>
        <xsl:choose>
            <xsl:when test="contains($text, '&lt;')">
                <xsl:value-of select="substring-before($text, '&lt;')"/>
                <xsl:call-template name="strip-tags">
                    <xsl:with-param name="text" select="substring-after($text, '&gt;')"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- This template will take a value and detect if it is a link (simply
         if it starts with http). If so, it will return the value as an anchor
         element, if not, it will just return the value as text -->
    <xsl:template name="link-or-text">
        <xsl:param name='val'/>
        <xsl:choose>
            <xsl:when test="starts-with($val, 'http')">
                <xsl:element name="a">
                    <xsl:attribute name="href">
                        <xsl:value-of select="$val"/>
                    </xsl:attribute>
                    <xsl:attribute name="target">
                        _blank
                    </xsl:attribute>
                    <xsl:value-of select="$val"/>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$val"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- This template will convert a set of <element> nodes into a comma-separated
         list and add tooltips to each one for the atomic number and full element name -->
    <xsl:template name="elements-to-list">
        <xsl:param name='elements'/>
        <xsl:param name="tooltip-position" select="'top'"/>
        <xsl:for-each select="exslt:node-set($elements)/node()">
              <xsl:variable name="element-symbol">
                  <xsl:value-of select="local-name(./descendant-or-self::*)"/>
              </xsl:variable>
              <xsl:element name="span">
                  <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                  <xsl:attribute name="data-bs-placement"><xsl:value-of select="$tooltip-position"/></xsl:attribute>
                  <xsl:attribute name="title">
                      <!-- The 'for-each document' bit is required because keys only work
                           in the context of the current document in XSLT 1.0
                           (see https://stackoverflow.com/a/35327827/1435788) -->
                      <xsl:for-each select="document('')">
                          <xsl:value-of select="key('lookup.element.symbol', $element-symbol)"/>
                      </xsl:for-each>
                  </xsl:attribute>
                  <xsl:value-of select="local-name(.)"/>
              </xsl:element>
              <xsl:if test="position() != last()">
                  <xsl:text>, </xsl:text>
              </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="find-root-filepath">
        <!--
            This template analyzes all dataset locations and returns a value
            of the path that is common to all of them. It assumes file paths
            are foward-slash (/) separated and start with a forward slash,
        -->
        <xsl:variable name="path-parts">
        <!--
           $path-parts will be a fragment with /item nodes representing
           the parts of the path (starting with empty string "")
        -->
            <xsl:call-template name="tokenize-path">
                <xsl:with-param name="path">
                    <xsl:value-of select="(//nx:dataset/nx:location)[1]"/>
                </xsl:with-param>
                <xsl:with-param name="prepend"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable
            name="all-locations"
            select="//nx:dataset/nx:location"/>
        <xsl:variable name="path-counts">
        <!--
            $path-counts will be a fragment of the form
            <frag>
                <count>
                    <path>/</path>
                    <value>10</value>
                </count>
                <count>
                    <path>/first</path>
                    <value>10</value>
                </count>
                <count>
                    <path>/first/second</path>
                    <value>5</value>
                </count>
            </frag>
        -->
            <xsl:for-each select="exslt:node-set($path-parts)/item">
                <xsl:variable name="this-item" select="./text()"/>
                <count>
                    <path>
                        <xsl:value-of select="./text()"/>
                    </path>
                    <value>
                        <xsl:value-of select="count(($all-locations)[starts-with(./text(), $this-item)])"/>
                    </value>
                </count>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="filelist-rootpath">
            <xsl:variable name="max-count-paths" select="math:highest(exslt:node-set($path-counts)/count/value)/parent::node()"/>
            <xsl:for-each select="exslt:node-set($max-count-paths)">
                <xsl:sort select="string-length(path)" data-type="number" order="ascending"/>
                <xsl:if test="position()=last()">
                    <xsl:copy-of select="path"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <!-- return the value found for the rootpath -->
        <xsl:value-of select="$filelist-rootpath"/>
    </xsl:template>

    <!-- This template displays a "simple" table of all datasets for use when $simpleDisplay is true()
         It can later be converted to a DataTable for more interaction
    -->
    <xsl:template name="simple-filelist-table">
        <xsl:variable name="filelist-rootpath">
            <xsl:call-template name="find-root-filepath"/>
        </xsl:variable>
        <xsl:variable
            name="rootpath-weblink"
            select="concat($datasetBaseUrl, $filelist-rootpath)">
        </xsl:variable>
        <div style="font-size: medium;" class="mb-2">
            All file paths in the table below are relative to
            <code id='simple-filelist-rootpath'
                style="line-height: 1.25em; display: inline;"><a>
                    <xsl:attribute name="href">
                        <xsl:value-of
                            select="$rootpath-weblink"/>
                    </xsl:attribute>
                    <xsl:attribute name="download"/>
                    <xsl:attribute name="target">_blank</xsl:attribute>
                    <xsl:attribute name="class">help-tip</xsl:attribute>
                    <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                    <xsl:attribute name="data-bs-placement">top</xsl:attribute>
                    <xsl:attribute name="title">Click to view directory structure directly in the browser</xsl:attribute>
                    <xsl:variable name="decoded-rootpath">
                        <xsl:call-template name="decode">
                            <xsl:with-param
                                name="encoded"
                                select="$filelist-rootpath"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:value-of select="$decoded-rootpath"/>
            </a></code>
        </div>
        <table id="simple-filelist-table"
            class="table table-sm table-hover filelist-table compact mt-0"
            width="100%"
            border="1"><!-- style="" -->
            <thead>
                <tr>
                    <th id="simple-filelist-number-col">
                        Dataset #
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                            <xsl:with-param name="tip-text">The sequential number of this dataset in the Experiment</xsl:with-param>
                        </xsl:call-template>
                    </th>
                    <th id="simple-filelist-aa-col">
                        Activity #
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                            <xsl:with-param name="tip-text">The activity number containing this dataset</xsl:with-param>
                        </xsl:call-template>
                    </th>
                    <th id="simple-filelist-name-col">
                        Dataset Name
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                            <xsl:with-param name="tip-text">The name given to the dataset (typically the filename)</xsl:with-param>
                        </xsl:call-template>
                    </th>
                    <th id="simple-filelist-path-col">
                        Path
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                            <xsl:with-param name="tip-text">The path (relative to root path, above) containing this dataset (click to view directly in browser)</xsl:with-param>
                        </xsl:call-template>
                    </th>
                    <th id='simple-filelist-type-col'>
                        Type
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                            <xsl:with-param name="tip-text">A label indicating the data type of this dataset (taken from a controlled list)</xsl:with-param>
                        </xsl:call-template>
                    </th>
                    <th id='simple-filelist-preview_dl-col'>
                        Preview
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                            <xsl:with-param name="tip-text">Click to view this dataset's preview (if it exists)</xsl:with-param>
                        </xsl:call-template>
                    </th>
                    <th class='text-center' id='simple-filelist-json_dl-col'>
                        Meta
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                            <xsl:with-param name="tip-text">Click to download this dataset's extracted metadata</xsl:with-param>
                        </xsl:call-template>
                    </th>
                    <th class='text-center' id='simple-filelist-data_dl-col'>
                        D/L
                        <xsl:call-template name="help-tip">
                            <xsl:with-param name="tip-placement">top</xsl:with-param>
                            <xsl:with-param name="tip-text">Click to download this dataset</xsl:with-param>
                        </xsl:call-template>
                    </th>
                </tr>
            </thead>
            <tbody>
                <xsl:for-each select="//nx:dataset">
                    <tr>
                        <xsl:element name="td">
                            <xsl:element name="a">
                                <xsl:attribute name="class">dataset_anchor</xsl:attribute>
                                <xsl:attribute name="name">
                                    <xsl:value-of select="generate-id(current())"/>
                                </xsl:attribute>
                            </xsl:element>
                            <xsl:value-of select="position()"/>
                        </xsl:element>
                        <xsl:element name="td">
                            <xsl:value-of select="../@seqno + 1"/>
                        </xsl:element>
                        <xsl:element name="td">
                            <xsl:value-of select="nx:name"/>
                        </xsl:element>
                        <td class='filepath'>
                            <xsl:variable name="datasetLink">
                                <xsl:call-template name="get-path-of-file">
                                    <xsl:with-param name="absolute_filename">
                                        <xsl:value-of select="nx:location"/>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:variable>
                            <code>
                                <a>
                                    <xsl:attribute name="href">
                                        <xsl:value-of select="concat($datasetBaseUrl, $datasetLink)"/>
                                    </xsl:attribute>
                                    <xsl:attribute name="download"/>
                                    <xsl:attribute name="target">_blank</xsl:attribute>
                                    <xsl:call-template name="decode">
                                        <xsl:with-param
                                            name="encoded"
                                            select="substring-after($datasetLink, $filelist-rootpath)"/>
                                    </xsl:call-template>
                                </a>
                            </code>
                        </td>
                        <xsl:variable name="dataset-type">
                            <xsl:choose>
                                <xsl:when test="string(@type) = 'SpectrumImage'">Spectrum Image</xsl:when>
                                <xsl:otherwise><xsl:value-of select="@type"/></xsl:otherwise>
                            </xsl:choose>
                        </xsl:variable>
                        <td>
                            <!-- type -->
                            <xsl:value-of select="$dataset-type"/>
                        </td>
                        <td>
                            <!-- preview -->
                            <xsl:choose>
                                <xsl:when test="nx:preview">
                                    <xsl:variable
                                        name="preview-location"
                                        select="concat($previewBaseUrl, nx:preview/text())"/>
                                    <xsl:element name='a'>
                                        <xsl:attribute name="href"><xsl:value-of select="$preview-location"/></xsl:attribute>
                                        <xsl:attribute name="onclick">
                                            $(this).blur()
                                        </xsl:attribute>
                                        <xsl:attribute name="target">_blank</xsl:attribute>
                                        <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                        <xsl:attribute name="data-bs-placement">right</xsl:attribute>
                                        <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                        <xsl:attribute name="title">Click to download this dataset&apos;s preview image</xsl:attribute>
                                        <xsl:attribute name="style">position: relative;</xsl:attribute>
                                        <xsl:attribute name="class">
                                            simple-filelist-preview
                                        </xsl:attribute>
                                        <xsl:element name="img">
                                            <xsl:attribute name="src">
                                                <xsl:value-of select="$preview-location"/>
                                            </xsl:attribute>
                                            <xsl:attribute name="class">
                                                simple-filelist-preview
                                            </xsl:attribute>
                                        </xsl:element>
                                        <i class='fa fa-image fa-border preview-button' style='margin-left:0;'/>
                                    </xsl:element>
                                    <xsl:comment></xsl:comment>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:element name='a'>
                                       <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                        <xsl:attribute name="data-bs-placement">left</xsl:attribute>
                                        <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                        <xsl:attribute name="title">No preview available for this image</xsl:attribute>
                                        <xsl:attribute name="disabled"></xsl:attribute>
                                        <xsl:element name="i">
                                            <xsl:attribute name="class">fa fa-image fa-border param-button</xsl:attribute>
                                            <xsl:attribute name="style">margin-left: 0;</xsl:attribute>
                                            <xsl:attribute name="disabled"></xsl:attribute>
                                        </xsl:element>

                                    </xsl:element>
                                </xsl:otherwise>
                            </xsl:choose>
                        </td>
                        <td>
                            <!-- metadata -->
                            <xsl:variable name="json-location-raw">
                                <xsl:choose>
                                    <xsl:when test="nx:preview">
                                        <xsl:value-of select="$previewBaseUrl"/>
                                        <xsl:value-of select="substring-before(nx:preview, '.thumb.png')"/>
                                        <xsl:text>.json</xsl:text>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="$previewBaseUrl"/>
                                        <xsl:value-of select="nx:location"/>
                                        <xsl:text>.json</xsl:text>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:variable>
                            <xsl:variable name="json-location" select="normalize-space($json-location-raw)"/>
                            <xsl:element name='a'>
                                <xsl:attribute name="href"><xsl:value-of select="$json-location"/></xsl:attribute>
                                <xsl:attribute name="onclick">
                                    $(this).blur()
                                </xsl:attribute>
                                <xsl:attribute name="target">_blank</xsl:attribute>
                                <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                <xsl:attribute name="data-bs-placement">left</xsl:attribute>
                                <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                <xsl:attribute name="title">Click to download this dataset's metadata in JSON format</xsl:attribute>
                                <i class='fa fa-download fa-border param-button' style='margin-left:0;'/>
                            </xsl:element>
                        </td>
                        <td>
                            <!-- download link -->
                            <xsl:element name='a'>
                                <xsl:attribute name='class'>filelisting-dl-cell</xsl:attribute>
                                <xsl:attribute name="href"><xsl:value-of select="$datasetBaseUrl"/><xsl:value-of select="nx:location"/></xsl:attribute>
                                <xsl:attribute name="onclick">
                                    $(this).blur()
                                </xsl:attribute>
                                <xsl:attribute name="download"/>
                                <xsl:attribute name="data-bs-toggle">tooltip</xsl:attribute>
                                <xsl:attribute name="data-bs-placement">left</xsl:attribute>
                                <xsl:attribute name="data-bs-html">true</xsl:attribute>
                                <xsl:attribute name="title">Click to download &#013;<xsl:value-of select='nx:name'/></xsl:attribute>
                                <i class='fa fa-download fa-border param-button' style='margin-left:0;'/>
                            </xsl:element>
                        </td>
                    </tr>
                </xsl:for-each>
            </tbody>
        </table>
    </xsl:template>

    <xsl:template name="replace-string">
        <!-- taken from https://stackoverflow.com/a/27668220/1435788 -->
        <xsl:param name="text"/>
        <xsl:param name="replace"/>
        <xsl:param name="with"/>
        <xsl:choose>
            <xsl:when test="contains($text,$replace)">
                <xsl:value-of select="substring-before($text,$replace)"/>
                <xsl:value-of select="$with"/>
                <xsl:call-template name="replace-string">
                    <xsl:with-param name="text" select="substring-after($text,$replace)"/>
                    <xsl:with-param name="replace" select="$replace"/>
                    <xsl:with-param name="with" select="$with"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- The below URL decode template downloaded from https://skew.org/xml/stylesheets/url-encode/ -->
    <xsl:variable name="hex" select="'0123456789ABCDEF'"/>
    <xsl:variable name="ascii"> !"#$%&amp;'()*+,-./0123456789:;&lt;=&gt;?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~</xsl:variable>
    <xsl:variable name="latin1">&#160;&#161;&#162;&#163;&#164;&#165;&#166;&#167;&#168;&#169;&#170;&#171;&#172;&#173;&#174;&#175;&#176;&#177;&#178;&#179;&#180;&#181;&#182;&#183;&#184;&#185;&#186;&#187;&#188;&#189;&#190;&#191;&#192;&#193;&#194;&#195;&#196;&#197;&#198;&#199;&#200;&#201;&#202;&#203;&#204;&#205;&#206;&#207;&#208;&#209;&#210;&#211;&#212;&#213;&#214;&#215;&#216;&#217;&#218;&#219;&#220;&#221;&#222;&#223;&#224;&#225;&#226;&#227;&#228;&#229;&#230;&#231;&#232;&#233;&#234;&#235;&#236;&#237;&#238;&#239;&#240;&#241;&#242;&#243;&#244;&#245;&#246;&#247;&#248;&#249;&#250;&#251;&#252;&#253;&#254;&#255;</xsl:variable>
    <xsl:template name="decode">
        <xsl:param name="encoded"/>
        <xsl:choose>
            <xsl:when test="contains($encoded,'%')">
                <xsl:value-of select="substring-before($encoded,'%')"/>
                <xsl:variable name="hexpair" select="translate(substring(substring-after($encoded,'%'),1,2),'abcdef','ABCDEF')"/>
                <xsl:variable name="decimal" select="(string-length(substring-before($hex,substring($hexpair,1,1))))*16 + string-length(substring-before($hex,substring($hexpair,2,1)))"/>
                <xsl:choose>
                    <xsl:when test="$decimal &lt; 127 and $decimal &gt; 31">
                        <xsl:value-of select="substring($ascii,$decimal - 31,1)"/>
                    </xsl:when>
                    <xsl:when test="$decimal &gt; 159">
                        <xsl:value-of select="substring($latin1,$decimal - 159,1)"/>
                    </xsl:when>
                    <xsl:otherwise>?</xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="decode">
                    <xsl:with-param name="encoded" select="substring(substring-after($encoded,'%'),3)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$encoded"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>
