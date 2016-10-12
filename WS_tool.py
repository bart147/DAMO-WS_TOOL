#-------------------------------------------------------------------------------
# Name:        WS_tool damo
# Purpose:     Beheren van velden en domeinen in DAMO.
# Versie:      1.2
#
# Author:      Bart Kropf
# Created:     08-04-2016
# Copyright:   None
# Site:        www.bkgis.nl
#-------------------------------------------------------------------------------

# v1.1 notes
# 01-09-2016, B. Kropf
# Aanpassing waardoor ook originele damo domeinen gecontroleerd worden die zijn uitgebreid met eigen 900+ waarden.
# Bug: "del srow1" stond op verkeerde plek waardoor deze soms verwijderd wordt terwijl hij niet bestaat (en dus fout geeft).
# variabele "lst_domeinen" veranderd in "lst_domeinen_uit_tabVelden" want is duidelijker.

# v1.2 notes
# 12-10-2016, B. Kropf
# Schrijfwijze veldnaam niet langer verplicht met 'WS_' maar geeft nu waarschuwing i.p.v. raise exception.
# reden is dat nu ook bestaande damo velden kunnen worden ingevuld en worden voorzien gekoppeld aan een eigen domein.
# funcion main() in een try-except loop gezet.


# import geoprocessor
import arceditor, arcpy

# import system modules
import sys, os, logging, time
from datetime import datetime, date


def start_timer():
    '''Start timer'''
    fTimeStart = time.time()
    sBericht = '\nStarting ... (%s)\n' % time.asctime(time.localtime(fTimeStart))
    print_log (sBericht,"i")
    return fTimeStart

def end_timer(fTimeStart):
    '''End timer'''
    fTimeEnd = time.time()
    sBericht = '\nEnding ..... (%s)' % time.asctime(time.localtime(fTimeEnd))
    print_log (sBericht,"i")
    fTimePassed = round(fTimeEnd - fTimeStart) # in gehele secs
    tTimePassed = time.gmtime(fTimePassed) # as a tuple
    if tTimePassed.tm_hour >= 1:
        sBericht = time.strftime('(%H hrs, %M mins, %S secs have passed)\n', tTimePassed)
    elif tTimePassed.tm_min >= 1:
        sBericht = time.strftime('(%M mins, %S secs have passed)\n', tTimePassed)
    else:
        sBericht = time.strftime('(%S secs have passed)\n', tTimePassed)
    print_log (sBericht,"i")

def BlokjeLog(strTITEL,logType):
    print_log("\n" + \
             "---------------------------------------------------------------------------------------------------------\n" + \
             "------ " + str(strTITEL) + "\t\t" + time.asctime() + "\n" + \
             "---------------------------------------------------------------------------------------------------------\n" + \
             "\n", logType)

def print_log(txt,logType):
    arcpy.AddMessage(txt)
    print (txt)
    if logType == "d": # debug
        logging.info(txt)
    elif logType == "i": # info
        logging.info(txt)
    elif logType == "w": # warning
        logging.warning(txt)
    elif logType == "e": # error
        logging.error(txt)
    elif logType == "c": # critical
        logging.critical(txt)


def create_d_fields():
    # veldenlijst maken
    d_fields = {}

    flds = ["volgorde","fc","domein","veldnaam","veldtype","precisie","schaal","lengte","alias","nullable","required","opmerking"]

    # veldenlijst maken
    scur = arcpy.SearchCursor(tbl_velden)
    for srow in scur:
        nr = srow.getValue("volgorde")
        if nr != None:
            d_fields[str(int(nr)).zfill(4)] = {
            "fc": srow.getValue("fc"),
            "domein": srow.getValue("domein"),
            "veldnaam": srow.getValue("veldnaam"),
            "veldtype": srow.getValue("veldtype"),
            "precisie": srow.getValue("precisie"),
            "schaal": srow.getValue("schaal"),
            "lengte": srow.getValue("lengte"),
            "alias": srow.getValue("alias"),
            "nullable": srow.getValue("nullable"),
            "required": srow.getValue("required"),
            "opmerking": srow.getValue("opmerking")
            }
    del scur, srow

    for fieldnr,f in sorted(d_fields.iteritems()):
        print_log("%s:\t%s, %s, %s, %s"%(fieldnr,f["fc"],f["veldnaam"],f["veldtype"],f["domein"]),"i") # print veldnr: volgorde,fc, etc...

    print_log("\naantal velden is %i\n"%len(d_fields),"i")

    return d_fields


def add_fields(d_fields):
    # lijsten maken van damo_fields dict om efficienter te testen.
    print_log ("Controleer of domeinen zijn toegewezen bij velden in damo_fields.xls...","i")
    l_fc_fld = [] # tuple met (fc,veldnaam)
    l_fc = [] # fc (unieke waardes) lijst met alleen fc's
    for fieldnr,f in sorted(d_fields.iteritems()):
        l_fc_fld.append( (f["fc"],f["veldnaam"]) )
        if not f["fc"] in l_fc:
            l_fc.append(f["fc"])

    # check of veldnamen wel correct zijn (WS_)
    print_log ("Controleer of feature classes bestaan in damo...","i")
    for fc in l_fc:
        if not arcpy.Exists(fc):
            raise Exception("fc (%s) komt niet voor in damo!"%fc)

    # check of alle fc's in damo wel bestaan
    print_log ("Controleer of velden correct zijn ingevuld met WS_...","i")
    for fc, fld in l_fc_fld:
        if not "WS_" in fld:
            print_log('Veldnaam %s onjuist! Moet met "WS_" beginnen'%fld,"w")
##            raise Exception('Veldnaam %s onjuist! Moet met "WS_" beginnen'%fld)
        if fld.upper() != fld:
            print_log('Veldnaam %s onjuist! Veldnaam moet in UPPERCASE...'%fld,"w")
##            raise Exception('Veldnaam %s onjuist! Veldnaam moet in UPPERCASE, enzo...'%fld)

    # lijsten maken van velden in damo database
    print_log ("Damo-velden ophalen...","i")
    l_fld_damo = [] # velden die al in damo bestaan per fc
    l_fld_damo_domein = [] # velden die al in damo bestaan per fc + domein
    for fc in l_fc:
        for fld in arcpy.ListFields(fc,"WS_*"):
            l_fld_damo.append((fc,fld.name))
            l_fld_damo_domein.append((fc,fld.name,fld.domain))

    # velden toevoegen als deze nog niet bestaan
    for fieldnr,f in sorted(d_fields.iteritems()):
        if not (f["fc"],f["veldnaam"].upper()) in l_fld_damo:
            print_log("add %s to %s..."%(f["veldnaam"],f["fc"]),"i")
            arcpy.AddField_management(f["fc"],f["veldnaam"],f["veldtype"],f["precisie"],f["schaal"],f["lengte"],f["alias"],f["nullable"],f["required"],f["domein"])




def create_domains(d_fields):
    # lijst met domeinen uit damo_fields.xls, tabblad velden.
    if arcpy.Exists(tabel):
        #MakeTableView_management <in_table> <out_view> {where_clause} {workspace} {field_info}
        arcpy.MakeTableView_management (tbl_velden, "velden_view")
    else:
        print_log("%s niet gevonden"%tbl_velden,"e")

    lst_domeinen_uit_tabVelden = []# lijst met domeinen in excel die gekoppeld zijn in velden.
    scur = arcpy.SearchCursor("velden_view") #,'"fc"='+"'"+fc+"'") #,whereclause)
    for srow in scur:
        domein = srow.getValue("domein")
        if domein <> None and domein not in lst_domeinen_uit_tabVelden:
            lst_domeinen_uit_tabVelden.append(domein)
    del scur, srow

    # Controleer of domeinen zijn opgegeven bij tabblad "velden" en of niet al bestaan
    # in damo. Zo ja: maak dan de nieuwe domeinen aan.

    # check existing domains
    desc = arcpy.Describe(sde)
    l_domains_damo = desc.domains


    lst_range_domeinen = [] # lijst met ranged domains
    lst_coded_domeinen = [] # lijst met coded domains
    lst_domein_te_vullen = [] # lijst met domains die nog niet voorkomen in damo
    ##l_domain_tables = [] # lijst met weggeschreven domain tabellen die al wel voorkomen in damo en gecontroleerd moeten worden.
    l_damo_domeinwaarden = [] # lijst met alle domeinwaarden uit damo in tuple (domein,coded_value,description)

    # domains lijsten vullen uit excel 'domeinen'
    scur = arcpy.SearchCursor(tbl_domeinen) #,whereclause)
    for srow in scur:
        domein = srow.getValue("domein")
        if domein != None:
            if domein in lst_domeinen_uit_tabVelden: # controleer of domein uit tabblad "domeinen" ook is opgegeven in tabblad "velden"
                domein_type = srow.getValue("domain_type")
                field_type = srow.getValue("field_type")
                domein_besch = srow.getValue("domein_beschrijving")
                if domein_type == "CODED":
                    lst_coded_domeinen.append(domein)
                elif domein_type == "RANGE":
                    lst_range_domeinen.append(domein)
                else:
                    print_log(domein+" type niet gevonden","i")
                if domein not in l_domains_damo and domein != None and field_type != None:
                    # dit worden de nieuwe domeinen
                    lst_domein_te_vullen.append(domein)
                    arcpy.CreateDomain_management (sde, domein, domein_besch, field_type, domein_type)
                    print_log("domein gemaakt: "+domein,'i')
                elif domein in l_domains_damo and domein != None and field_type != None:
                    # zijn de domeinen uit damo_fields.xls die zijn gekoppeld aan velden en die al bestaan in damo.
                    # controleer nu of de waarden ook kloppen!

                    # set workspace op temp_gdb en overwriteOutput = True
                    arcpy.env.workspace = temp_gdb
                    arcpy.env.overwriteOutput = True

                    print_log("ophalen waarden uit damo voor domein %s..."%domein,'i')
                    domain_table = os.path.join(temp_gdb,domein.strip().replace(" ","_"))
                    ##l_domain_tables.append(domain_table)
                    # damo domeinen wegschrijven naar tabel
                    arcpy.DomainToTable_management (sde, domein, domain_table, "coded_values", "description")
                    # domeintabelwaarden aan lijst l_damo_domeinwaarden toevoegen voor inhoudelijke controle helemaal onderaan deze functie
                    scur1 = arcpy.SearchCursor(domain_table)
                    for srow1 in scur1:
                        try:
                            coded_value = str(int(srow1.getValue("coded_values")))
                        except:
                            coded_value = str(srow1.getValue("coded_values"))
                        regel = [domein, coded_value, srow1.getValue("description")]
                        l_damo_domeinwaarden.append(regel)
                        del srow1
                    del scur1

                    # set workspace terug naar sde en overwriteOutput = False
                    arcpy.env.workspace = sde
                    arcpy.env.overwriteOutput = False
    del scur, srow

    # domeinlijst met waardes maken uit tabel die vanuit damo is weggeschreven.
    scur = arcpy.SearchCursor(tbl_domeinwaarden) #,whereclause)

    domeinwaarden = [] # lijst met alle domeinwaarden [domein,code,code_beschrijving]
    for srow in scur:
        regel = [srow.getValue("domein"),srow.getValue("code"),srow.getValue("code_beschrijving")]
        domeinwaarden.append(regel)
    del scur, srow

    print_log("domeinwaarden: %i"%len(domeinwaarden),'i')
    print_log("coded domains: %i"%+len(lst_coded_domeinen),'i')
    print_log("range domains: %i"%len(lst_range_domeinen),"i")

    if len(lst_domein_te_vullen)>0:
        print_log(lst_domein_te_vullen,'i')
    else:
        print_log("Geen nieuwe domeinen aangetroffen (die nog niet in damo staan)\n","i")

    # waarden toevoegen aan nieuwe domeinen of checken of waarden voorkomen in bestaande domeinen
    i = 0
    for domein, code, beschrijving in domeinwaarden:
        if domein in lst_domein_te_vullen:
            if len(lst_coded_domeinen) > 0:
                if domein in lst_coded_domeinen:
                    print_log("append to "+domein+":   "+code+" , "+ beschrijving,"i")
                    arcpy.AddCodedValueToDomain_management (sde, domein, code, beschrijving)  # sneller is waarschijnlijk om hier tabel 2 domain te gebruiken
            elif len(lst_range_domeinen) > 0:
                if domein in lst_range_domeinen:
                    print_log("append to "+domein+":   "+code+" , "+ beschrijving,"i")
                    if beschrijving == "Min value":
                        min_value = code
                    elif beschrijving == "Max value":
                        max_value = code
                        print_log("set range for "+domein+" to "+min_value+" , "+max_value)
                        arcpy.SetValueForRangeDomain_management (sde, domein, min_value, max_value)
        elif domein in lst_domeinen_uit_tabVelden: # alleen controleren als domeinen ook toegewezen zijn in tabblad velden van damo_fields.xls
            # check hier of de waarden overeenkomen
            if not [domein,code,beschrijving] in l_damo_domeinwaarden:
                print_log("%s: (%s, %s) uit damo_fields.xls komt niet voor in damo"%(domein,code,beschrijving),'i')
                i+=1
    print_log("\n%i domeinwaarden uit damo_fields.xls niet in damo gevonden\n"%i,'i')

    # andersom checken of alle bestaande domeinwaarden in damo voorkomen in damo_fields.xls domeinwaarden.
    i = 0
    for domein, code, beschrijving in l_damo_domeinwaarden:
        if not [domein,code,beschrijving] in domeinwaarden and domein in lst_domeinen_uit_tabVelden:
            i+=1
            print_log("%s: (%s, %s) uit damo komt niet voor in damo_fields.xls"%(domein,code,beschrijving),'i')
    print_log("\n%i domeinwaarden uit damo niet in damo_fields.xls gevonden\n"%i,'i')


def assign_domains(d_fields):

    l_fc_fld = [] # tuple met (fc,veldnaam)
    l_fc = [] # fc (unieke waardes) lijst met alleen fc's
    for fieldnr,f in sorted(d_fields.iteritems()):
        l_fc_fld.append( (f["fc"],f["veldnaam"]) )
        if not f["fc"] in l_fc:
            l_fc.append(f["fc"])

    # check of de domeinen wel zijn toegewezen.
    # ververs de damo veldenlijst
    l_fld_damo = [] # velden die al in damo bestaan per fc
    l_fld_damo_domein = [] # velden die al in damo bestaan per fc + domein
    for fc in l_fc:
        for fld in arcpy.ListFields(fc,"WS_*"):
            l_fld_damo.append((fc,fld.name))
            l_fld_damo_domein.append((fc,fld.name,fld.domain))

    print_log('\nControleer of alle WS_domeinen in damo overeenkomen met die in damo_fields.xls...',"i")
    for fieldnr,f in sorted(d_fields.iteritems()):
        if not (f["fc"],f["veldnaam"],f["domein"]) in l_fld_damo_domein and f["domein"] != None:
            print_log("\n%s [%s] (%s)"%(f["domein"],f["veldnaam"],f["fc"]),"i")
            try:
                print_log("\tprobeer te koppelen...","i")
                arcpy.AssignDomainToField_management (f["fc"], f["veldnaam"], f["domein"])
                print_log("\tsucces!","i")

            except Exception as e:
                print_log(e,"e")

    #check voor WS_velden die wel in damo voorkomen maar niet in de lijst.
    print_log('\nControleer of alle WS_domeinen in damo_fields overeenkomen met die in damo...',"i")
    for fc in l_fc:
        fld_lst = arcpy.ListFields(fc,"WS_*")
        for fld in fld_lst: # WS_velden bekijken voor fc in damo
            if not (fc,fld.name) in l_fc_fld:
                print_log("Let op! %s gevonden in %s, maar komt niet voor in WS_veldenlijst"%(fld.name,fc),"w")

#-------------------------------------------------------------------------------
# Purpose: main function
# Note:
#-------------------------------------------------------------------------------
def main():

    BlokjeLog("Start de damo add_fields tool, gemaakt door Bart Kropf: www.bkgis.nl","i")
    # start timer
    fTimeStart = start_timer()

    # print logfile locatie
    print_log ("Logfile: %s"%logFile,"i")
    print_log ("Connectie: %s"%sde,"i")

    # create d_fields{}
    d_fields = create_d_fields()

    # add the fields to damo
    if check_fields == 'true':
        BlokjeLog("Start met controleren en toevoegen van velden","i")
        add_fields(d_fields)

    # check domains
    if check_domain == 'true':
        BlokjeLog("Start met controleren en toevoegen van domeinen","i")
        create_domains(d_fields)

    # assign domains
    assign_domains(d_fields)


    # end timer
    BlokjeLog("Damo add_fields tool succesvol verlopen!","i")
    end_timer(fTimeStart)

if __name__ == '__main__':
    # variables
    sde = sys.argv[1]
    check_fields = sys.argv[2] # wel of niet velden controleren
    check_domain = sys.argv[3] # wel of niet domein controleren

    # bepaal rootfolder
    rootfolder = os.path.dirname(os.path.dirname(sys.argv[0]))

    # connection file
    if sde == '#':
        # geef hier eventueel een sde connectie file op.
        sde = r'PadNaar...\Connectionfiles\DAMO_W@DAMOPLT.sde'
    elif '.gdb' in sde:
        sde = os.path.join(rootfolder,'gdb',sde)

    # logging
    logFileName = 'WS_tool_'+datetime.strftime(datetime.now(),"%Y%m%d-%H.%M")+'.log'
    logFile = os.path.join(rootfolder,'log',logFileName)
    logging.basicConfig(filename=logFile, level=logging.DEBUG)

    # input damo_fields.xlsx
    tabel = logFile = os.path.join(rootfolder,'input','Damo_fields.xlsx')
    tbl_velden = tabel+"\\velden$"
    tbl_domeinen = tabel+"\\domeinen$"
    tbl_domeinwaarden = tabel+"\\domeinwaarden$"

    # temp gdb
    temp_gdb = os.path.join(rootfolder,'tmp_data','domains.gdb')

    # set workspace
    arcpy.env.workspace = sde

    # run main
    try:
        main()
    except Exception as e:
        print_log(e,"\ne")
        print_log("\nscript afgebroken","i")
