<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema"
  xmlns:nx="https://data.nist.gov/od/dm/nexus/experiment/v1.0" 
  xmlns:exslt="http://exslt.org/common" extension-element-prefixes="exslt"
  version="1.0">
  <xsl:output method="html" indent="yes" encoding="UTF-8"/>

  <xsl:param name="detail_url" select="'#'"/>
  <xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>
  <xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>

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
    
    <style>
      .tooltip {
      z-index: 20000;
      position: fixed; 
      }
    </style>
    <div class='a-result'>
     <div>
       <xsl:element name="a">
         <xsl:attribute name="href">
           <xsl:value-of select="$detail_url"/>
         </xsl:attribute>
         <span class="list-record-title">
             <i class="fas fa-file-alt results-icon"/>
           <xsl:choose>
             <xsl:when test="$title = 'No matching calendar event found'">
               <xsl:text>Untitled experiment</xsl:text>
             </xsl:when>
             <xsl:otherwise>
               <xsl:value-of select="$title"/>
             </xsl:otherwise>
           </xsl:choose>
         </span>
       </xsl:element>
       <xsl:text> </xsl:text>
       <xsl:variable name="instr-pid">
         <xsl:value-of select="string(nx:summary/nx:instrument/@pid)"/>
       </xsl:variable>
       <span class="badge list-record-badge">
         <xsl:attribute name="style">background-color:<xsl:for-each select="document('')">
             <xsl:value-of select="key('lookup.instr.color', $instr-pid)"/>
           </xsl:for-each> !important;</xsl:attribute>
         <xsl:value-of select="nx:summary/nx:instrument"/>
       </span>
       <span class="badge list-record-badge">
         <xsl:value-of select="count(//nx:dataset)"/> data files in <xsl:value-of select="count(//nx:acquisitionActivity)"/> activit<xsl:choose>
           <xsl:when test="count(//nx:acquisitionActivity) = 1">y</xsl:when>
           <xsl:otherwise>ies</xsl:otherwise>
         </xsl:choose> </span>
        <i class="fa fa-cubes filetypes-icon" style="margin-left:0.75em; font-size: small;"
            data-toggle="tooltip" data-placement="top" title="Filetypes present in record"/><span style="font-size: small;"><xsl:text>: </xsl:text></span>
       
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
       <span class="list-record-date">
         <i>
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
         </i>
       </span>
     </div>
      <xsl:choose>
        <xsl:when test="nx:summary/nx:motivation/text()">
          <div class="motivation-text">
            <span style="font-style:italic;">Motivation: </span><xsl:value-of select="nx:summary/nx:motivation"/>
          </div>
        </xsl:when>
      </xsl:choose>
     
        <!-- Javascript which supports some capabilities on the generated page -->
        <script language="javascript">
            <![CDATA[
            $('.a-result').click(function() {
                window.location = $(this).find('a').attr('href');
                return false;
            });
            
            // Shepherd tutorial code
            function create_tour() {
                var topScrollHandler = function(element){
                    if (element) {
                        var $element = $(element);
                        var topOfElement = $element.offset().top;
                        var heightOfElement = $element.height() + 75;
                        $('html, body').animate({
                            scrollTop: topOfElement - heightOfElement
                        },{
                            duration: 500
                        });
                    }
                };

                var list_tour = new Shepherd.Tour({
                    useModalOverlay: true,
                    defaultStepOptions: {
                        when: { show() { showStepNumber() } },
                        scrollTo: true,
                        scrollToHandler: topScrollHandler
                    }
                });
            
                showStepNumber = () => {
                    $("<span style='font-size: small'></span>")
                        .insertAfter('.shepherd-footer .btn-default')
                        .html(`${list_tour.steps.indexOf(list_tour.currentStep) + 1}/${list_tour.steps.length}`);
                }
                
                end_button = {
                    text: 'End',
                    classes: 'btn btn-danger',
                    action: list_tour.next,
                    label: 'End'
                }
                
                next_button = {
                    text: 'Next <i class="fa fa-arrow-right menu-fa"></i>',
                    classes: 'btn btn-primary',
                    action: list_tour.next,
                    label: 'Next'
                }
                
                var back_button = (enabled) => {
                    return {
                        text: '<i class="fa fa-arrow-left menu-fa"></i> Back',
                        classes: 'btn btn-default',
                        disabled: (! enabled),
                        action: list_tour.back,
                        label: 'Back'}
                }
            
                list_tour.addStep({
                    id: 'tut-welcome',
                    title: 'This is the record explorer page',
                    text: 'The <em>explore</em> page allows you to browse and search through the records contained in the NexusLIMS repository. Click <em>Next</em> for a brief tour of the features of this page. You can also use the keyboard arrow keys to navigate through the tutorial.',
                    buttons: [
                        back_button(false),
                        next_button
                    ],
                });
            
                list_tour.addStep({
                    id: 'tut-search-field',
                    title: 'The search bar',
                    text: 'Use the search box to do a full-text search on all the records (can search by username, date, instrument, etc.). Leave the box empty to return all results from the database.',
                    attachTo: {
                        element: '#search-field',
                        on: 'bottom'
                    },
                    buttons: [
                        back_button(true),
                        next_button
                    ],
                });
            
                list_tour.addStep({
                    id: 'tut-example-record',
                    title: 'An example record listing',
                    text: 'Each listing in the results area represents one record in the database and provides some basic summary information about the record\'s contents. Click anywhere on the listing to view the record details.',
                    attachTo: {
                        element: '#example-record',
                        on: 'bottom'
                    },
                    scrollTo: false,
                    buttons: [
                        back_button(true),
                        next_button
                    ],
                });
            
                
            
                list_tour.addStep({
                    id: 'tut-result-button-filter',
                    title: 'Record sorting',
                    text: 'By default, the records are sorted with the most recently added records first. Use this sort button to change the sorting order.',
                    attachTo: {
                        element: '#result-button-filter0',
                        on: 'left'
                    },
                    scrollTo: false,
                    buttons: [
                        back_button(true),
                        $('.pagination-container').length > 0 ? next_button : end_button
                    ],
                    modalOverlayOpeningPadding: 15,
                    popperOptions: {
                        modifiers: [{
                            name: 'offset',
                            options: {
                                offset: [0, 15]
                            }
                        }]
                    }
                });
            
                if ( $('.pagination-container').length > 0 ) {
                    list_tour.addStep({
                        id: 'tut-pagination-container',
                        title: 'Browsing many records',
                        text: 'If your search returns more items than fit on one page, use the paging controls at the bottom to browse through the records',
                        attachTo: {
                            element: '#pagination-container',
                            on: 'bottom'
                        },
                        when: { show() { showStepNumber() } },
                        buttons: [
                            back_button(true),
                            end_button
                        ]
                    });
                }
            
                var scroll_to_start = function() {
                    $('html, body').animate(
                        {scrollTop: cur_pos}, 
                        {duration: 500}
                    );
                }
            
                let cur_pos = $(document).scrollTop();
                list_tour.on('complete', scroll_to_start)
                list_tour.on('cancel', scroll_to_start)
                list_tour.on('hide', scroll_to_start)
                $('.shepherd-modal-overlay-container').on('click', () => list_tour.cancel());
                list_tour.start()
            }              

            $( document ).ready(function() {
                $('[data-toggle="tooltip"]').tooltip(
                    {container:'body'}); // toggle all tooltips with default
              
                // add IDs for use with intro.js
                $('.a-result').first().attr('id', 'example-record');
                $('input#id_keywords ~ ul').attr('id', 'search-field');
                $('.pagination-container').attr('id', 'pagination-container');
            });
            ]]>
        </script>
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
      <xsl:when test="$i = 1">
        <xsl:choose>
          <xsl:when test="contains($text, $delim)">
            <xsl:value-of select="substring-before($text, $delim)"/>
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
            <xsl:value-of select="substring-after($text, $delim)"/>
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
        <xsl:attribute name="data-toggle">tooltip</xsl:attribute>
        <xsl:attribute name="data-placement">bottom</xsl:attribute>
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
  
</xsl:stylesheet>
