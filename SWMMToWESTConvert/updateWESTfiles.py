import xml.etree.ElementTree as ET
import re


import SWMMToWESTConvert.WESTConstants as W_C
import SWMMToWESTConvert.SWMMtoWESTConstants as STW_C


#Variables and their translation ---------------------------------------
SEW_DICT_SET = [STW_C.AREATANK,STW_C.VMAX,STW_C.K]
SEW_XML_SET = [W_C.XML_AREA_SEWER,W_C.XML_VMAX_SEWER,W_C.XML_K_SEWER]


CATCH_DICT_SET = [STW_C.AREA,STW_C.N_PEOPLE,STW_C.FLOWRPERPERSON,STW_C.DF_BASELINE]
CATCH_XML_SET = [W_C.XML_AREA_CATCH,W_C.XML_DWF_NPEOPLE,W_C.XML_DWF_QPERPERSON,W_C.XML_DWF_Q_INDUSTRY]


def createQuantityXML(qName:str, qValue:str)-> ET.Element:
    """
        Create a new Quantity element for the Layout.xml 
    Args:
        qName (str): Quantity name e.g. ".Catchment_1.DWF.Infiltration"
        qValue (str): Quantity value e.g. "0.25"
    Returns:
        ET.Element: Quantity element to be added to an XML
    """  
    # Example of a Quantity element:
    # <Quantity Name=".Catchment_1.DWF.Infiltration">
    #     <Props>
    #         <Prop Name="Value" Value="0.25"/>
    #         <Prop Name="DisplayUnit" Value=""/>
    #     </Props>
    # </Quantity>
    
    new_quantity = ET.Element(W_C.XML_QUANTIY, attrib={W_C.XML_NAME: qName})
    props = ET.SubElement(new_quantity, W_C.XML_PROPS)
    prop = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_VAL, W_C.XML_VAL: qValue})
    
    return new_quantity

def createLinkXML(linkName:str, fromM:str, toM:str, lineName:str)->ET.Element:
    """
        Create a new Link element for the Layout.xml 
    Args:
        linkName (str): Link name e.g. "Link997156"
        fromM (str): Model origin e.g. "Two_combiner7"
        toM (str): Model destination e.g. "Icon44"
        lineName (str): Line name e.g. "CustomOrthogonalLine31"
    Returns:
        ET.Element: Link element to be added to an XML
    """  
    # Example of a link element:
    # <Link Name="Link997156">
    #     <Props>
    #         <Prop Name="From" Value="sub_models.Two_combiner7.interface.Outflow"/>
    #         <Prop Name="To" Value="sub_models.Icon44.interface.Inflow"/>
    #         <Prop Name="Type" Value="Connect"/>
    #         <Prop Name="Data" Value="ConnectionName=&quot;CustomOrthogonalLine31&quot; ConnectionType=&quot;WaterLine&quot;"/>
    #     </Props>
    # </Link> 
    fromVal = W_C.XML_SUBMOD + "." + fromM + W_C.XML_INTERFACE_OUT
    toVal = W_C.XML_SUBMOD + "." + toM + W_C.XML_INTERFACE_IN
    dataVal = W_C.XML_CONN_NAME + "=" + W_C.XML_QUOT + lineName + W_C.XML_QUOT + ' ' + W_C.XML_CONN_TYPE + "=" + W_C.XML_QUOT + W_C.XML_WATERLINE + W_C.XML_QUOT

    new_Link = ET.Element(W_C.XML_LINK, attrib={W_C.XML_NAME: linkName})
    props = ET.SubElement(new_Link, W_C.XML_PROPS)
    propF = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_FROM, W_C.XML_VAL: fromVal})
    propT = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_TO, W_C.XML_VAL: toVal})
    propType = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_TYPE, W_C.XML_VAL: W_C.XML_TYPEVAL_LINK})
    propData = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_DATA, W_C.XML_VAL: dataVal})

    return new_Link

def setModelClass(submodel:ET.Element,modelClass:str):
    """_summary_

    Args:
        submodel (ET.Element): _description_
        modelClass (str): _description_
    """    
    #TODO documentation

    submodel.find("./Props/Prop[@Name='ClassName']").set('Value', modelClass) # Always the same class

def getModelNames(submodel:ET.Element,nameSufix:str)->tuple[int,str]:
    """
        Gets the InstanceName of a model and its name index.
    Args:
        submodel (ET.Element): The XML representing a submodel in the WEST layout.xml file
        nameSufix (str): Name sufix of the model depending on its type e.g. for tank in series it is 'SEW_'.
    Raises:
        Exception: If the name does not follow the expected pattern e.g. <<nameSufix>>_<<nameIndex>>
    Returns:
        tuple[int,str]: Name index of the model. Instance name of the model.
    """    
    instName = submodel.find("./Props/Prop[@Name='InstanceName']").get('Value')
    
    iType = getModelNameIndex(nameSufix, instName)
        
    return iType, instName

def getModelNameIndex(nameSufix:str, instName:str)->int:
    """
        Gets the name index of the model. Does not apply to CatchmentModels with suffix [input] (TODO change this!).
    Args:
        nameSufix (str): Name sufix of the model depending on its type e.g. for tank in series it is 'SEW_'.
        instName (str): Instance name of the model.
    Raises:
        Exception: If the name does not follow the expected pattern e.g. <<nameSufix>>_<<nameIndex>>
    Returns:
        int: Name index of the model.
    """    
    try:
        iType = int(re.split("^" + nameSufix, instName)[1])
    except Exception as e:
        raise Exception("The InstanceName of the sewer (XML) does not follow the expected naming convention (" + str(e) + ")")
    return iType

def createsOrModifyQuantity(property,instName,XMLval,quant_XMLelem:ET.Element,root:ET.Element):

    #Get the values to modify
    val = str(property) 
    valQuantityName = '.' + instName + XMLval
    valQuantity = root.find(".//Quantities/Quantity[@Name='"+ valQuantityName +"']")
                
    #if exists changes the value, if not then creates the XML
    if (valQuantity is None):
        valXML = createQuantityXML(valQuantityName, val)
        quant_XMLelem.append(valXML)
    else:
        valQuantity.find("./Props/Prop[@Name='Value']").set('Value', val)

    return quant_XMLelem,root

#-------------Modify models---------------------------------------------
def modifySewerModel(root:ET.Element, quantities:ET.Element, submodel:ET.Element, sewerClass:str, props:list[dict])->tuple[ET.Element,ET.Element,str]:
    """
        Modifies the class and properties of an existent model type SEWER in a WEST project
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        quantities (ET.Element) : All quantities in the WEST's .Layout.xml file 
        submodel (ET.Element): Model element to be modified
        sewerClass (str): Class to assign to the model 
        props (list[dict]): List of sewer sections of the model and their properties.
    Returns:
        tuple[ET.Element,ET.Element,str]: Updated root and quantities elements of the WEST's .Layout.xml file. InstanceDisplayName of the model 
    """ 
    setModelClass(submodel,sewerClass)
    iSewer,instName = getModelNames(submodel,W_C.XML_SEWER_NAMES)

    for sectP in props: #Iterates the sewer section properties to find the required one and allocate

        if iSewer in sectP[STW_C.TANK_INDEXES]: # if the sewer section properties apply to the current index!!! (IMPORTANT) 
            
            nameSewer=  sectP[STW_C.NAME] + "("+ str(iSewer - min(sectP[STW_C.TANK_INDEXES])) + ")"
            submodel.find("./Props/Prop[@Name='"+ W_C.XML_MODEL_PROP_NAME + "']").set('Value', nameSewer) 

            for P,XMLval in zip(SEW_DICT_SET,SEW_XML_SET):
                
                val = sectP[P]

                if ((val is not None) & (val != 0)):
                    quantities,root = createsOrModifyQuantity(val,instName,XMLval,quantities,root) 
                
    return root, quantities, nameSewer

def modifyCatchmentModel(root:ET.Element, quantities:ET.Element, submodel:ET.Element, catchClass:str, props:list[dict])->tuple[ET.Element,ET.Element,str]:
    """
        Modifies the class and properties of an existent model type CATCHMENT in a WEST project.
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        quantities (ET.Element) : All quantities in the WEST's .Layout.xml file 
        submodel (ET.Element): Model element to be modified
        catchClass (str): Class to assign to the model 
        props (list[dict]): List of catchments and their properties
    Returns:
        tuple[ET.Element,ET.Element,str]: Updated root and quantities elements of the WEST's .Layout.xml file. InstanceDisplayName of the model 
    """ 
    i = 1
    setModelClass(submodel,catchClass)
    iCatch,instName = getModelNames(submodel,W_C.XML_CATCH_NAMES)
    
    for catchM in props: #Iterates the catchment properties to find the required one and allocate
        
        if iCatch == i:
            
            pos = STW_C.BEFORE_CATCHMENT if catchM[STW_C.END] else ''
            catchName = catchM[STW_C.NAME] + STW_C.SECTION_CATCHMENT + pos
            submodel.find("./Props/Prop[@Name='"+ W_C.XML_MODEL_PROP_NAME + "']").set('Value', catchName) #Sets the name

            #For simple values
            for P,XMLval in zip(CATCH_DICT_SET,CATCH_XML_SET):

                val = catchM[P]

                if ((val is not None) & (val != 0)):
                    quantities,root = createsOrModifyQuantity(val,instName,XMLval,quantities,root)
                elif ((val is None) | (val == 0))  & ((P == STW_C.AREA) | (P == STW_C.N_PEOPLE)): #If no values are given the 
                    val = 0 #Replace with zero in cas is None
                    quantities,root = createsOrModifyQuantity(val,instName,XMLval,quantities,root)
            
            #For the time pattern
            if (catchM[STW_C.TIMEPATTERN] is not None):
                for h,vh in zip([f"{hour:02})" for hour in range(0,24)],catchM[STW_C.TIMEPATTERN]):

                    quantities,root = createsOrModifyQuantity(vh,instName,W_C.XML_DWF_CUSTOMFLOWPATTERN + h,quantities,root)
            
        i+=1
            
    return root, quantities, catchName

def modifyConnectorModel(root:ET.Element, quantities:ET.Element, submodel:ET.Element, connClass:str, velTSS, velMin)->tuple[ET.Element,ET.Element,str]:
    """
        Modifies the class and properties of an existent model type CONNECTOR in a WEST project.
        CONNECTOR are usually placed between Catchment and sewer models to convert the data type.
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        submodel (ET.Element): Model element to be modified
        connClass (str): Class to assign to the model 
        velTSS (TODO): 
        velMin (TODO): 
    Returns:
        tuple[ET.Element,ET.Element,str]: Updated root and quantities elements of the WEST's .Layout.xml file. InstanceName of the model 
    """ 
    nClasses = 10

    setModelClass(submodel,connClass)
    iConnector,instName = getModelNames(submodel,W_C.XML_CONN_NAMES)
    
    #if exists changes the value, if not then creates the XML
    #Assumes if one of the properties exist the others do too
    velMinName = '.' + instName + W_C.XML_CONN_VELMINCLASS 
    velMinVal = root.find(".//Quantities/Quantity[@Name='"+ velMinName +"']")
    if (velMinVal is None):
        
        #Create the xml tags using as dictionaries
        velMinXML = createQuantityXML(velMinName, str(velMin))
        quantities.append(velMinXML)
        
        for vi, vel in zip(range(0,nClasses,1),velTSS):
            
            #Create the xml tags using as dictionaries
            velName = '.' + instName + W_C.XML_CONN_VELCLASS + '(C'+ str(vi) +')'
            velXML = createQuantityXML(velName, str(vel)) 
            quantities.append(velXML)
                                     
    else:
        velMinVal.find("./Props/Prop[@Name='Value']").set('Value', str(velMin))
        
        for vi, vel in zip(range(0,nClasses,1),velTSS):
            
            velName = '.' + instName + W_C.XML_CONN_VELCLASS + '(C'+ str(vi) +')'
            velVal= root.find(".//Quantities/Quantity[@Name='"+ velName +"']")
            velVal.find("./Props/Prop[@Name='Value']").set('Value', str(vel))
   
    return root, quantities, instName

def modifyCombinerModel(root:ET.Element, submodel:ET.Element, combClass:str)->tuple[ET.Element,ET.Element,str]:
    """
        Modifies the class of an existent model type TWO COMBINER in a WEST project.
        COMBINER are placed between Connector after a catchment to connect to the rest of the network.
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        submodel (ET.Element): Model element to be modified
        combClass (str): Class to assign to the model 
    Returns:
        tuple[ET.Element,ET.Element,str]: Updated root of the WEST's '.Layout.xml' file. InstanceName of the model 
    """ 

    setModelClass(submodel,combClass)
    iConnector,instName = getModelNames(submodel,W_C.XML_COMB_NAMES)
    
    return root,instName


#-------------Create Links ----------------------------------------------
def createCatchmentLinksXML(linksXML:ET.Element,catchmentNames:dict[str],connectorNames:dict[str],combNames:dict[str],prevElement:str)->ET.Element:
    """
        Creates the links between a catchment and another element downstream. 
        If there is a previous element, the catchemnt is connected to it. Then, the catchment is connected to a connector (model) and the connector to a combiner.
    Args:
        linksXML (ET.Element): Links element of the WEST's .Layout.xml file.
        catchmentNames (dict[str]): Name of the cathment element in the xml, and names to be set for the link and connection associated. 
        connectorNames (dict[str]): Name of the connector model element in the xml, and names to be set for the link and connection associated. 
        combNames (dict[str]): Name of the combiner element in the xml, and names to be set for the link and connection associated. 
        prevElement (str): Name of the upstream element at which the catchment would be connected.
        TODO return doc
    """
    if prevElement is not None:
        previousToCatch = createLinkXML(catchmentNames[STW_C.LINK_NAME], prevElement,catchmentNames[STW_C.ELE_NAME],
                    catchmentNames[STW_C.CONN_NAME]) #Previous element to catchment
        linksXML.append(previousToCatch)
        
    catchToConn = createLinkXML(connectorNames[STW_C.LINK_NAME],catchmentNames[STW_C.ELE_NAME],connectorNames[STW_C.ELE_NAME],
                  connectorNames[STW_C.CONN_NAME]) #Cathment to connector
    ConnToComb = createLinkXML(combNames[STW_C.LINK_NAME],connectorNames[STW_C.ELE_NAME],combNames[STW_C.ELE_NAME],
                  combNames[STW_C.CONN_NAME]) #Connector to combiner
    
    linksXML.append(catchToConn)
    linksXML.append(ConnToComb)

    return linksXML

def connectCurrentCatchment(namesDict:dict[str], catchsList:list[dict], linksXML:ET.Element, linki:int, lastElement:str,
                            catchModelNames:dict[str],catchi:int)->tuple[ET.Element,int,str,bool,str,dict[str],int]:
    """
        Connects the current catchment to the WEST model and gets the required values of the next catchment.
    Args:
        namesDict (dict[str]): Dictionary of names between the instance name and the model name. keys are the instanceNames.
        catchsList (list[dict]): Catchments to be modeled in WEST and their characteristics.
        linksXML (ET.Element):  Links element of the WEST's .Layout.xml file.
        linki (int): Index of the next link in the WEST model.
        lastElement (str): Model name of the last element connected in the WEST model
        catchModelNames (dict[str]): Names of the catchment,connector and two combiner models.
        catchi (int): Index of the next catchment in the WEST model.
    Returns:
        tuple[ET.Element,int,str,bool,str,dict[str],int]:  Updated XML element of links. Updated index for the next link. 
                                                       Model name of the last element connected to the WEST model.
                                                       True if the next catchment is connected at the end of the sewer, and false otherwise.
                                                       InstanceName of the next catchment. Model names of the next catchment. Index of the next catchment.
    """    
    linksXML, linki, lastElement = connectCatchment(linksXML, linki, lastElement, catchModelNames)
    nextEndConnection, catchNextiName, catchNextModelNames, catchi = getNextCatchment(namesDict, catchsList, catchi)

    return linksXML, linki, lastElement, nextEndConnection, catchNextiName, catchNextModelNames, catchi

def getNextCatchment(namesDict:dict[str], catchsList:list[dict], iCatchment:int)->tuple[bool, str, dict[str]]:
    """
        Removes the next element from the list of catchments to model. Gets the position of the catchment (before or after the sewer section) 
        and the names of the associated connector and two combiner model.
    Args:
        namesDict (dict[str]): Dictionary of names between the instance name and the model name. keys are the instanceNames.
        catchsList (list[dict]): Catchments to be modeled in WEST and their characteristics.
    Returns:
        tuple[bool, str, dict[str],int]: True if the catchment is connected at the end of the sewer, and false otherwise. 
                                         InstanceDisplayName of the catchment. Model names of the catchment. Index of the next catchment.
    """    
    try:
        catchmenti = catchsList.pop(0)
        endConnection = catchmenti[STW_C.END]
        catchmentName = catchmenti[STW_C.NAME_CATCH]
        
        catchModelNames = {STW_C.CATCH_MOD_NAME:namesDict[catchmentName],
                    STW_C.CONN_MOD_NAME:namesDict[W_C.XML_CONN_NAMES + str(iCatchment)],
                    STW_C.COMB_MOD_NAME:namesDict[W_C.XML_COMB_NAMES + str(iCatchment)]}
        iCatchment += 1
    except:
        print("There are no more catchments.")
        endConnection, catchmentName, catchModelNames, iCatchment = None,None,None,None

    return endConnection, catchmentName, catchModelNames, iCatchment

def connectCatchment(linksXML:ET.Element, linki:int, prevElement:str, catchModelNames:dict[str])->tuple[ET.Element, int, str]:
    """
        Creates the required links to connect to the WEST model: the last element to the catchment, the catchment to a connector, and 
        the connector to a two combiner.
    Args:
        linksXML (ET.Element): Links element of the WEST's .Layout.xml file.
        linki (int): Index of the next link in the WEST model.
        prevElement (str): Model name of the last element connected in the WEST model.
        catchModelNames (dict[str]): Model name associated to the catchment to be connected. i.e, catchment, connector, and combiner model names.
    Returns:
        tuple[ET.Element, int, str]: Updated XML element of links. Updated index for the next link. 
                                     Model name of the last element connected to the WEST model.
    """    
    catchModelName = catchModelNames[STW_C.CATCH_MOD_NAME]
    connName = catchModelNames[STW_C.CONN_MOD_NAME]
    combName = catchModelNames[STW_C.COMB_MOD_NAME]

    if prevElement is not None:
        nameL, nameC, linki = getLinkAndConnectionNames(linki)
        catchmentN = {STW_C.ELE_NAME:catchModelName,STW_C.LINK_NAME:nameL,STW_C.CONN_NAME:nameC}
    else:
        catchmentN = {STW_C.ELE_NAME:catchModelName}

    nameL, nameC, linki = getLinkAndConnectionNames(linki)
    connN = {STW_C.ELE_NAME:connName,STW_C.LINK_NAME:nameL,STW_C.CONN_NAME:nameC}
                
    nameL, nameC, linki = getLinkAndConnectionNames(linki)
    combN = {STW_C.ELE_NAME:combName,STW_C.LINK_NAME:nameL,STW_C.CONN_NAME:nameC}

    linksXML = createCatchmentLinksXML(linksXML,catchmentN,connN,combN,prevElement)
    
    return linksXML, linki, combName

def connectPipeSection(namesDict:dict[str], linksXML:ET.Element, linki:int, lastElement:str, 
                                                                            pipeSect:dict[str])->tuple[ET.Element, int, str]:
    """
        Connects all the tanks in series representing a pipe section between each other. Starts by connecting the last element to the first tank.  
        Then, first to second, until n-1 to n. If there last element in the network is None, then starts in 1 to 2.
    Args:
        namesDict (dict[str]): Dictionary of names between the instance name and the model name. keys are the instanceNames.
        linksXML (ET.Element): Links element of the WEST's .Layout.xml file.
        linki (int): Index of the next link in the WEST model.
        lastElement (str): Model name of the last element connected in the WEST model.
        pipeSect (dict[str]): The attributes of the pipe section.
    Returns:
        tuple[ET.Element,int,str]: The updated XML element of links. Updated index for the next link. The updated name of the last element connected.
    """    
    tanksIndexes = pipeSect[STW_C.TANK_INDEXES]
    name = pipeSect[STW_C.NAME]

    if lastElement is None:
        lastElement = namesDict[name + "(" + str(tanksIndexes[0]) + ")"]
        tanksIndexes = tanksIndexes[1:]

    for t in tanksIndexes:
        tankName = namesDict[name + "(" + str(t) + ")"]
        linksXML, linki, lastElement = addLink(linksXML, linki, lastElement, tankName)

    return linksXML, linki, lastElement

def addLink(linksXML:ET.Element, linki:int, fromElement:str, toElement:str)->tuple[ET.Element, int, str]:
    """
        Adds a new link to the links element of the model's XML layout file. 
        For this, creates the names of the link and connection. Creates the XML of a link, and adds it to the links element. 
    Args:
        linksXML (ET.Element): Links element of the WEST's .Layout.xml file.
        linki (int): Index of the next link in the WEST model.
        fromElement (str): Model name of the element where the link starts.
        toElement (str): Model name of the element where the link finishes.
    Returns:
        tuple[ET.Element, int, str]: Updated links element. Updated index for the next link. Model name of the last element connected to the WEST model.
    """    
    nameL, nameC, linki = getLinkAndConnectionNames(linki)

    linkAux = createLinkXML(nameL,fromElement,toElement,nameC)
    linksXML.append(linkAux)

    return linksXML, linki, toElement

def getLinkAndConnectionNames(linki:int)->tuple[str, str, int]:
    """
        Creates new link and connection names and increases the index of the links in the WEST model.
    Args:
        linki (int): Index of the next link in the WEST model.
    Returns:
        tuple[str,str,int]: Name of the link. Name of the connection. Updated index for the next link.
    """    
    nameL = STW_C.LINK_NAME_SUFFIX + str(linki)
    nameC = STW_C.CONNECTION_NAME_SUFFIX + str(linki)
    linki += 1

    return nameL, nameC, linki

def createLinks(root:ET.Element, namesDict:dict[str], catchments:list[dict], sewerSections:list[dict])->ET.Element:
    """
        Creates all the links of the model. Loops the sewer sections adding links between the tanks composing them and 
        links the catchments with the same name of the sewer section before or after the tank according to its position property.
        The element Links should exist in the WEST's '.Layout.xml' file
    Args:
        root (ET.Element): Root element of the WEST's '.Layout.xml' file 
        namesDict (dict[str]): Dictionary of names between the instance name and the model name. keys are the instanceNames.
        catchments (list[dict]): All catchments of the model and their properties.
        sewerSections (list[dict]): All sewer sections of the model and their properties.
    Returns:
        ET.Element: updated root element of the WEST's '.Layout.xml' file
    """    
    #TODO check if the links exist already

    linksXML = root.find('.//Links')

    linki, catchi = 1, 1
    lastElement = None
    endConnection, catchiName, catchModelNames, catchi = getNextCatchment(namesDict, catchments,catchi)

    for p in sewerSections:

        sewerCatchiName = p[STW_C.NAME] + STW_C.SECTION_CATCHMENT
        sewerCatchPreviName = p[STW_C.NAME] + STW_C.SECTION_CATCHMENT + STW_C.BEFORE_CATCHMENT
        seweriInputName = sewerCatchiName + STW_C.INPUT_CATCHMENT #the name of a catchment correspondant to an input associated to the i sewer section

        #if the catchment has the name of the sewer section and its not attached to the end, connects the catchment before the sewer section
        if (catchiName == sewerCatchPreviName) and (not endConnection):  
            linksXML, linki, lastElement, endConnection, catchiName, catchModelNames, catchi = connectCurrentCatchment(namesDict, catchments, linksXML, linki, lastElement, catchModelNames, catchi)

        #Connects the tanks of the sewer section 
        linksXML, linki, lastElement = connectPipeSection(namesDict, linksXML, linki, lastElement, p)

        #Connects the catchment if it connects to the end of the sewer section 
        if (catchiName == sewerCatchiName)  and endConnection:
            linksXML, linki, lastElement, endConnection, catchiName, catchModelNames, catchi = connectCurrentCatchment(namesDict, catchments, linksXML, linki, lastElement, catchModelNames, catchi)

        #Connects a input catchment if exists. If there was another catchment attached to the pipe section (at the beggining or end) 
        #the catchmenti was updated and this will add another one for the input 
        if (catchiName == seweriInputName):
            linksXML, linki, lastElement, endConnection, catchiName, catchModelNames, catchi = connectCurrentCatchment(namesDict, catchments, linksXML, linki, lastElement, catchModelNames, catchi)

    return root

def setPropertiesAndClasses(xml:str,xmlOut:str,
                            sewerClass:str,propsSewer:str,
                            catchClass:str,combClass:str,propsCath:list[dict],
                            connClass:list[dict],connectorProps:list[dict]):
    #Props must be in order TODO documentation

    # Read the XML file
    tree = ET.parse(xml)
    root = tree.getroot()  

    submodels = root.findall('.//SubModel') 
    quantities = root.find('.//Quantities')

    print("Number of submodels found ",len(submodels))
    nSewers, nCatchments, nConnectors, nCombiners = 0,0,0,0 #count of sewers and catchments models found in the XML 
    namesDict = {}
    
    for submodel  in submodels: # Iterate over the SubModels
        
        if submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.SEWER: #if the model is a sewer
            root, quantities, displayName = modifySewerModel(root, quantities, submodel, sewerClass, propsSewer)
            namesDict[displayName] = submodel.attrib["Name"]
            nSewers += 1

        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.CATCHMENT: #if the model is a catchment
            root, quantities, displayName = modifyCatchmentModel(root, quantities, submodel, catchClass, propsCath)
            namesDict[displayName] = submodel.attrib["Name"]
            nCatchments += 1

        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.CONNECTOR: #if the model is a connector
            root, quantities, displayName = modifyConnectorModel(root, quantities, submodel, connClass, connectorProps[1],connectorProps[0])
            namesDict[displayName] = submodel.attrib["Name"]
            nConnectors += 1

        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.COMBINER: #if the model is a combiner
            root, quantities, displayName = modifyCombinerModel(root, quantities, submodel, combClass)
            namesDict[displayName] = submodel.attrib["Name"]
            nCombiners += 1

    
    #Create the links
    createLinks(root,namesDict,propsCath,propsSewer)
           
    print("The number of sewers found were ", nSewers, ", catchments ", nCatchments, " and connectors ", nConnectors)
    
    # Save the modified XML to a new file
    ET.indent(tree, space="\t", level=0)
    tree.write(xmlOut)
 
    
