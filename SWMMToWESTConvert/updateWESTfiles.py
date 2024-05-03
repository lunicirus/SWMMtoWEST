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

def createLinkXML(linkName:str, fromM:str, toM:str, lineName:str, inflowSufix: str='')->ET.Element:
    """
        Create a new Link element for the Layout.xml 
    Args:
        linkName (str): Link name e.g. "Link997156"
        fromM (str): Model origin e.g. "Two_combiner7"
        toM (str): Model destination e.g. "Icon44"
        lineName (str): Line name e.g. "CustomOrthogonalLine31"
        inflowSufix (str): Number of the inflow. Used only for combiners. e.g. "1" , then the to value would be: sub_models.Icon44.interface.Inflow1
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
    toVal = W_C.XML_SUBMOD + "." + toM + W_C.XML_INTERFACE_IN + inflowSufix
    dataVal = W_C.XML_CONN_NAME + "=" + W_C.XML_QUOT + lineName + W_C.XML_QUOT + ' ' + W_C.XML_CONN_TYPE + "=" + W_C.XML_QUOT + W_C.XML_WATERLINE + W_C.XML_QUOT

    new_Link = ET.Element(W_C.XML_LINK, attrib={W_C.XML_NAME: linkName})
    props = ET.SubElement(new_Link, W_C.XML_PROPS)
    propF = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_FROM, W_C.XML_VAL: fromVal})
    propT = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_TO, W_C.XML_VAL: toVal})
    propType = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_TYPE, W_C.XML_VAL: W_C.XML_TYPEVAL_LINK})
    propData = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_DATA, W_C.XML_VAL: dataVal})

    return new_Link

def setModelClass(submodel:ET.Element,modelClass:str):
    """
        Modifies the ClassName propertie of a submodel.
    Args:
        submodel (ET.Element): Submodel from a WEST project (see example below)
        modelClass (str): Class of the submodel to be set.
    """    
    # Example of a submodel
    # <SubModel Name="Icon23">
    # <Props>
    # <Prop Name="InstanceName" Value="Connector_info_1"/>
    # <Prop Name="InstanceDisplayName" Value="Connector_info_1"/>
    # <Prop Name="ClassName" Value="ClassDefault"/>
    # <Prop Name="Desc" Value=""/>
    # <Prop Name="Unit" Value=""/>
    # <Prop Name="DefaultValue" Value=""/>
    # <Prop Name="LowerBound" Value=""/>
    # <Prop Name="UpperBound" Value=""/>
    # <Prop Name="PDF" Value=""/>
    # <Prop Name="Group" Value=""/>
    # <Prop Name="Hidden" Value="false"/>
    # <Prop Name="Fixed" Value="false"/>
    # <Prop Name="Manip" Value="false"/>
    # <Prop Name="IsFavorite" Value="false"/>
    # <Prop Name="IsInner" Value="false"/>
    # <Prop Name="IsOuter" Value="false"/>
    # <Prop Name="EnableCustomFavorites" Value="false"/>
    # <Prop Name="Data" Value=""/>
    # </Props>
    # <Favorites>
    # </Favorites>
    # </SubModel>

    submodel.find("./Props/Prop[@Name='ClassName']").set('Value', modelClass) 

def setDisplayName(submodel, name):
    """
        Modifies the InstanceDisplayName property of a submodel.
    Args:
        submodel (ET.Element): Submodel from a WEST project (see example in the setModelClass function)
        name (str): name of the submodel to be set.
    """
    submodel.find("./Props/Prop[@Name='"+ W_C.XML_MODEL_PROP_NAME + "']").set('Value', name)

def getInstanceName(submodel:ET.Element)->str:
    """
        Obtains the instance name of a WEST submodel.
    Args:
        submodel (ET.Element): submodel of a WEST project (see example in the setModelClass function).
    Returns:
        str: InstanceName of the submodel
    """    
    return submodel.find("./Props/Prop[@Name='InstanceName']").get('Value')

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

def createsOrModifyQuantity(value,instName,XMLpropName,quant_XMLelem:ET.Element,root:ET.Element):

    #Get the values to modify
    val = str(value) 
    valQuantityName = '.' + instName + XMLpropName
    valQuantity = root.find(".//Quantities/Quantity[@Name='"+ valQuantityName +"']")
                
    #if exists changes the value, if not then creates the XML
    if (valQuantity is None):
        valXML = createQuantityXML(valQuantityName, val)
        quant_XMLelem.append(valXML)
    else:
        valQuantity.find("./Props/Prop[@Name='Value']").set('Value', val)

    return quant_XMLelem,root

#-------------Modify models---------------------------------------------
def modifySewerModel(root:ET.Element, quantities:ET.Element, XMLSewers:dict[ET.Element], sewerSection:dict, namesDict:dict[str])->tuple[ET.Element,ET.Element,str]:
    """
        Modifies the properties of an existent model type SEWER in a WEST project
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        quantities (ET.Element) : All quantities in the WEST's .Layout.xml file 
        sewerSection (dict): Properties of the sewer section to be set.
        XMLSewers (dict[ET.Element]): All sewer sections XML submodels found in the WEST .Layout.xml file. Keys are the index of the element.
        namesDict (dict[str]): Dictionary of names between the display name and the model name. keys are the display names.
    Returns:
        tuple[ET.Element,ET.Element]: Updated root and quantities elements of the WEST's .Layout.xml file.
    """ 
    for tank in sewerSection[STW_C.TANK_INDEXES]: 

        XMLSewerTank = XMLSewers[tank] #Gets the XML element with the index as equal to the tank index
        instName = getInstanceName(XMLSewerTank)
    
        nameSewer=  sewerSection[STW_C.NAME] + "("+ str(tank - min(sewerSection[STW_C.TANK_INDEXES])) + ")" #is nameSewerSection(tankNumberWithinthePipeSection) e.g. "DOM_203 - DOM_508(3)"
        setDisplayName(XMLSewerTank, nameSewer) 
        namesDict[nameSewer] = XMLSewerTank.attrib["Name"] 

        for P, XMLval in zip(SEW_DICT_SET,SEW_XML_SET):
            
            if P in sewerSection:
                val = sewerSection[P]

                if ((val is not None) & (val != 0)):
                    quantities,root = createsOrModifyQuantity(val,instName,XMLval,quantities,root) 
            else:
                raise KeyError("The property '{}' should exist in all sewer dictionaries.".format(P))
                
    return root, quantities

def modifyCatchmentModel(root:ET.Element, quantities:ET.Element, XMLCatchment:ET.Element, props:list[dict], namesDict:dict[str])->tuple[ET.Element,ET.Element,str]:
    """
        Modifies the properties of an existent model type CATCHMENT in a WEST project.
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        quantities (ET.Element) : All quantities in the WEST's .Layout.xml file 
        XMLCatchment (ET.Element): XML model element to be modified
        props (list[dict]): Properties of the catchment to be set.
        namesDict (dict[str]): Dictionary of names between the display name and the model name. keys are the display names.
    Returns:
        tuple[ET.Element,ET.Element]: Updated root and quantities elements of the WEST's .Layout.xml file.
    """ 
    catchmentName = props[STW_C.NAME_CATCH]
    setDisplayName(XMLCatchment, catchmentName) 
    namesDict[catchmentName] = XMLCatchment.attrib["Name"]

    instName = getInstanceName(XMLCatchment)

    #For simple values
    for P, XMLval in zip(CATCH_DICT_SET, CATCH_XML_SET):

        if P in props:
            val = props[P]

            if ((val is not None) & (val != 0)):
                quantities,root = createsOrModifyQuantity(val,instName,XMLval,quantities,root)
            elif ((val is None) | (val == 0))  & ((P == STW_C.AREA) | (P == STW_C.N_PEOPLE)): #If no values are given the 
                val = 0 #Replace with zero in cas is None
                quantities,root = createsOrModifyQuantity(val,instName,XMLval,quantities,root)
        else:
            raise KeyError("The property '{}' should exist in all catchment dictionaries.".format(P))

            
    #For the time pattern
    if STW_C.TIMEPATTERN in props:
        if (props[STW_C.TIMEPATTERN] is not None):
            for h,vh in zip([f"{hour:02})" for hour in range(0,24)],props[STW_C.TIMEPATTERN]):

                quantities,root = createsOrModifyQuantity(vh,instName,W_C.XML_DWF_CUSTOMFLOWPATTERN + h,quantities,root)
    else:
        raise KeyError("The property '{}' should exist in all catchment dictionaries.".format(STW_C.TIMEPATTERN))


    return root, quantities

def modifyConnectorModel(root:ET.Element, quantities:ET.Element, XMLConnector:ET.Element, props:list[dict], namesDict:dict[str])->tuple[ET.Element,ET.Element]:
    """
        Modifies the properties of an existent model type CONNECTOR in a WEST project.
        CONNECTOR are usually placed between Catchment and sewer models to convert the data type.
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        XMLConnector (ET.Element): XML model element to be modified
        props (list[dict]): Properties of the connector to be set.
        namesDict (dict[str]): Dictionary of names between the display name and the model name. keys are the display names.
    Returns:
        tuple[ET.Element,ET.Element]: Updated root and quantities elements of the WEST's .Layout.xml file.
    """ 
    instName = getInstanceName(XMLConnector)
    namesDict[instName] = XMLConnector.attrib["Name"] #In this case the instance name and display name are the same

    nClasses = 10

    if (STW_C.VEL_MIN_CONN in props) and (STW_C.VEL_CLASSES_CONN in props):
        valMin = props[STW_C.VEL_MIN_CONN]
        velTSS = props[STW_C.VEL_CLASSES_CONN]
    else:
        raise KeyError("The property '{}' should exist in all connector dictionaries.".format(STW_C.TIMEPATTERN))

    if (valMin is not None):
        quantities, root = createsOrModifyQuantity(valMin,instName,W_C.XML_CONN_VELMINCLASS,quantities,root)

    for vi, vel in zip(range(0,nClasses,1),velTSS):
        velName = W_C.XML_CONN_VELCLASS + '(C'+ str(vi) +')'
        quantities, root = createsOrModifyQuantity(vel,instName,velName,quantities,root)
            
    return root, quantities

#-------------Create Links ----------------------------------------------
def createCatchmentLinksXML(linksXML:ET.Element,catchmentNames:dict[str],connectorNames:dict[str],combNames:dict[str],prevElement:str)->ET.Element:
    """
        Creates the links between a catchment and another element downstream. 
        If there is a previous element, a combiner is connected to it. Then, the catchment is connected to a connector (model) 
        and the connector to the combiner in the inflow 2.
    Args:
        linksXML (ET.Element): Links element of the WEST's .Layout.xml file.
        catchmentNames (dict[str]): Name of the cathment element in the xml, and names to be set for the link and connection associated. 
        connectorNames (dict[str]): Name of the connector model element in the xml, and names to be set for the link and connection associated. 
        combNames (dict[str]): Name of the combiner element in the xml, and names to be set for the link and connection associated. 
        prevElement (str): Name of the upstream element at which the catchment would be connected.
    Returns:
        ET.Element: the XML element describing the link.
    """
    if prevElement is not None:
        previousToComb = createLinkXML(catchmentNames[STW_C.LINK_NAME], prevElement,combNames[STW_C.ELE_NAME],
                    catchmentNames[STW_C.CONN_NAME],W_C.XML_INFLOW_SUFFIX1) #Previous element to combiner
        linksXML.append(previousToComb)
        
    catchToConn = createLinkXML(connectorNames[STW_C.LINK_NAME],catchmentNames[STW_C.ELE_NAME],connectorNames[STW_C.ELE_NAME],
                  connectorNames[STW_C.CONN_NAME]) #Cathment to connector
    ConnToComb = createLinkXML(combNames[STW_C.LINK_NAME],connectorNames[STW_C.ELE_NAME],combNames[STW_C.ELE_NAME],
                  combNames[STW_C.CONN_NAME],W_C.XML_INFLOW_SUFFIX2) #Connector to combiner
    
    linksXML.append(catchToConn)
    linksXML.append(ConnToComb)

    return linksXML

def connectCurrentCatchment(namesDict:dict[str], catchsList:list[dict], linksXML:ET.Element, linki:int, lastElement:str,
                            catchModelNames:dict[str], iCatch:int, iComb:int)->tuple[ET.Element,int,str,bool,str,dict[str],int]:
    """
        Connects the current catchment to the WEST model and gets the required values of the next catchment.
    Args:
        namesDict (dict[str]): Dictionary of names between the instance name and the model name. keys are the display names.
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
    nextEndConnection, catchNextiName, catchNextModelNames, iCatchN, iCombN = getNextCatchment(namesDict, catchsList, iCatch, iComb)

    return linksXML, linki, lastElement, nextEndConnection, catchNextiName, catchNextModelNames, iCatchN, iCombN

def getNextCatchment(namesDict:dict[str], catchsList:list[dict], iCatch:int, iComb:int)->tuple[bool, str, dict[str], int, int]:
    """
        Removes the next element from the list of catchments to model. Gets the position of the catchment (before or after the sewer section) 
        and the names of the associated connector and two combiner model.
    Args:
        namesDict (dict[str]): Dictionary of names between the instance name and the model name. keys are the instanceNames.
        catchsList (list[dict]): Catchments to be modeled in WEST and their characteristics.
        iCatch (int): The index of the next catchment to be connected to the network.
        iComb (int): The index of the next combiner to be connected to the network.
    Returns:
        tuple[bool, str, dict[str], int, int]: True if the catchment is connected at the end of the sewer, and false otherwise. 
                                         InstanceDisplayName of the catchment. Model names of the catchment. Index of the next catchment. Index of the next combiner.
    """    
    try:
        catchmenti = catchsList.pop(0)
        endConnection = catchmenti[STW_C.END]
        catchmentName = catchmenti[STW_C.NAME_CATCH]

        
        catchModelNames = {STW_C.CATCH_MOD_NAME: namesDict[catchmentName],
                    STW_C.CONN_MOD_NAME: namesDict[W_C.XML_CONN_NAMES + str(iCatch)],
                    STW_C.COMB_MOD_NAME: namesDict[W_C.XML_COMB_NAMES + str(iComb)]}
        iCatch += 1
        iComb += 1
    except:
        print("There are no more catchments.")
        endConnection, catchmentName, catchModelNames = None,None,None

    return endConnection, catchmentName, catchModelNames, iCatch, iComb

def connectCatchment(linksXML:ET.Element, linki:int, prevElement:str, catchModelNames:dict[str])->tuple[ET.Element, int, str]:
    """
        Creates the required links to connect to the WEST model: the last element to a two combiner, the catchment to a connector, and 
        the connector to a the combiner.
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
    tini= tanksIndexes[0]

    if lastElement is None: #If there is no previous element then starts with the first thank 
        lastElement = namesDict[name + "(0)"]
        tanksIndexes = tanksIndexes[1:]

    for t in tanksIndexes:
        tankName = namesDict[name + "(" + str(t-tini) + ")"]
        linksXML, linki, lastElement = addLink(linksXML, linki, lastElement, tankName)

    return linksXML, linki, lastElement

def addLink(linksXML:ET.Element, linki:int, fromElement:str, toElement:str, inSuffix:str = '')->tuple[ET.Element, int, str]:
    """
        Adds a new link to the links element of the model's XML layout file. 
        For this, creates the names of the link and connection. Creates the XML of a link, and adds it to the links element. 
    Args:
        linksXML (ET.Element): Links element of the WEST's .Layout.xml file.
        linki (int): Index of the next link in the WEST model.
        fromElement (str): Model name of the element where the link starts.
        toElement (str): Model name of the element where the link finishes.
        inSuffix (str): Number of the inflow. Used only for combiners. e.g. "1" , then the to value would be: sub_models.Icon44.interface.Inflow1
    Returns:
        tuple[ET.Element, int, str]: Updated links element. Updated index for the next link. Model name of the last element connected to the WEST model.
    """    
    nameL, nameC, linki = getLinkAndConnectionNames(linki)

    linkAux = createLinkXML(nameL,fromElement,toElement,nameC,inSuffix)
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

def connectBranchToCombiner(linksXML:ET.Element, lastBranchEle:str, iLink:int, XMLCombiners: dict[ET.Element], iComb:int)->tuple[ET.Element, int, int, str]:
    """
        Connects the last element of a branch with the next combiner available
    Args:
        linksXML (ET.Element): Links element of the WEST's '.Layout.xml' file 
        lastBranchEle (str): Name model of the last element of the branch 
        iLink (int): Index of the next link to be created for the model.
        XMLCombiners (dict[ET.Element]): All XML submodels of the type combiners. Keys are the index.
        iComb (int): Index of the next combiner to be created for the model.
    Returns:
        tuple[ET.Element, int, int, str]: Updated links element of the WEST's '.Layout.xml' file. Indexes of the next link and combiner. Model name of the connected combiner.
    """    
    combName = XMLCombiners[iComb].attrib["Name"]

    linksXML, iLink, lastElement = addLink(linksXML, iLink, lastBranchEle, combName, W_C.XML_INFLOW_SUFFIX1)
    assert lastElement == combName

    iComb += 1    
    return linksXML, iLink, iComb, combName

def createPathLinks(linksXML:ET.Element, namesDict:dict[str], catchments:list[dict], sewerSections:list[dict], iLink:int, 
                    iCatch:int, iComb:int, branches:dict[str])->tuple[ET.Element,str,int,int,int]:
    """
        Creates all the links of a path. Loops the sewer sections adding links between the tanks composing them and 
        links the catchments with the same name of the sewer section before or after the tank according to its position property.
        The element Links should exist in the WEST's '.Layout.xml' file
    Args:
        linksXML (ET.Element): Links element of the WEST's '.Layout.xml' file 
        namesDict (dict[str]): Dictionary of names between the display name and the model name. keys are the display names.
        catchments (list[dict]): All catchments of the model and their properties.
        sewerSections (list[dict]): All sewer sections of the model and their properties.
        linki (int): Index of the next link to be created for the model. 
        iCatch (int): Index of the next catchment to be created for the model.
        iComb (int): Index of the next combiner to be created for the model.
        branches (dict[str]): The relationship between the name of the branch and the name of the combiner at the end of it.
    Returns:
        tuple[ET.Element,str,int,int,int]: Updated links element of the WEST's '.Layout.xml' file. Last element connected in the path. 
                                      Indexes of the next link, catchment and combiner.
    """    
    #TODO check if the links exist already
    endConnection, catchiName, catchModelNames, iCatch, iComb = getNextCatchment(namesDict, catchments, iCatch, iComb)

    #If its the trunk then gets the first branch
    if branches is not None:
        branchesR = dict(reversed(branches.items()))
        branch = branchesR.popitem()
    else:
        branch = None

    linkiIni = iLink
    lastElement = None
    for p in sewerSections:

        sewerCatchiName = p[STW_C.NAME] + STW_C.SECTION_CATCHMENT
        sewerCatchPreviName = sewerCatchiName + STW_C.BEFORE_CATCHMENT
        seweriInputName = sewerCatchiName + STW_C.INPUT_CATCHMENT #the name of a catchment correspondant to an input associated to the i sewer section
        branchName = p[STW_C.NAME].split(STW_C.PIPE_SEC_NAM_SEP)[1]

        #if the catchment has the name of the sewer section and its not attached to the end, connects the catchment before the sewer section
        if (catchiName == sewerCatchPreviName) and (not endConnection):  
            linksXML, iLink, lastElement, endConnection, catchiName, catchModelNames, iCatch, iComb = connectCurrentCatchment(namesDict, catchments, linksXML, iLink, lastElement, catchModelNames, iCatch, iComb)

        #Connects the tanks of the sewer section 
        linksXML, iLink, lastElement = connectPipeSection(namesDict, linksXML, iLink, lastElement, p)

        #Connects a input catchment if exists. If there was another catchment attached to the pipe section (at the beggining or end) 
        #the catchmenti was updated and this will add another one for the input 
        if (catchiName == seweriInputName):
            linksXML, iLink, lastElement, endConnection, catchiName, catchModelNames, iCatch, iComb = connectCurrentCatchment(namesDict, catchments, linksXML, iLink, lastElement, catchModelNames, iCatch, iComb)

        #Connects the catchment if it connects to the end of the sewer section 
        if (catchiName == sewerCatchiName)  and endConnection:
            linksXML, iLink, lastElement, endConnection, catchiName, catchModelNames, iCatch, iComb = connectCurrentCatchment(namesDict, catchments, linksXML, iLink, lastElement, catchModelNames, iCatch, iComb)

        #Joins the branch
        if (branch is not None) and (branch[0] == branchName):
            linksXML, iLink, lastElement = addLink(linksXML, iLink, lastElement, branch[1], W_C.XML_INFLOW_SUFFIX2)
            branch = branchesR.popitem() if len(branchesR) > 0 else None

    print("The number of created links was ", iLink-linkiIni)

    return linksXML, lastElement, iLink, iCatch, iComb

def getModelsByTypeAndSetClasses(root:ET.Element, modelClasses:dict[str], nBranches:int, nTanks:int)->dict[dict[ET.Element]]:
    """
        Separates all the submodels in the layout XML file of the WEST model in ditionaries by their type, 
        sets their class (all the same for the same type) and checks that the number of submodels is consistent.
    Args:
        root (ET.Element): root element of the layout XML file of the WEST model.
        modelClasses (dict[str]): Classes to be set to the submodels by type. Keys are type of model i.e. Sewer, Catchment.
        nBrances (int): Number of branches in the WEST model
        nTanks (int): Number of tanks in the WEST model i.e. number of sewer submodels to be expected
    Returns:
        dict[dict[ET.Element]]: Using as key the type e.g., STW_C.SEWERS, obtains a dictionary with all submodels of the type (i.e.,
        Sewer, Catchment, Connector, and Combiner), the internal dictionary uses as key the index (per type).
    """        
    XMLSewers, XMLCatchments, XMLConnectors, XMLCombiners = {},{},{},{}

    submodels = root.findall('.//SubModel') 
    print("Number of submodels found ",len(submodels))

    for submodel in submodels:

        if submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.SEWER: #if the model is a sewer
            setClassAndAddToDictionary(modelClasses[STW_C.SEWER_CLASS], XMLSewers, submodel, W_C.XML_SEWER_NAMES)

        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.CATCHMENT: #if the model is a catchment
            setClassAndAddToDictionary(modelClasses[STW_C.CATCH_CLASS], XMLCatchments, submodel, W_C.XML_CATCH_NAMES)

        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.CONNECTOR: #if the model is a connector
            setClassAndAddToDictionary(modelClasses[STW_C.CONN_CLASS], XMLConnectors, submodel, W_C.XML_CONN_NAMES)

        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.COMBINER: #if the model is a combiner
            setClassAndAddToDictionary(modelClasses[STW_C.COMB_CLASS], XMLCombiners, submodel, W_C.XML_COMB_NAMES)


    nSewers, nCatchments, nConnectors, nCombiners = len(XMLSewers), len(XMLCatchments), len(XMLConnectors), len(XMLCombiners) 
    print("The number of sewers found were ", nSewers, ", catchments ", nCatchments, ", connectors ", nConnectors, " and combiners ", nCombiners)
    assert nCatchments == nConnectors , f"The number of catchments and connectors model instances are not equal"
    assert nCombiners == nCatchments + nBranches, f"The number of combiners is not equal to the number of catchments plus the number of branches"
    assert nSewers == nTanks, f"The number of sewer models is not equal to the number of tank in series ({nTanks})"

    XMLElements = {}
    XMLElements[STW_C.SEWERS] = XMLSewers
    XMLElements[STW_C.CATCHMENTS] = XMLCatchments
    XMLElements[STW_C.CONNECTORS] = XMLConnectors
    XMLElements[STW_C.COMBINERS] = XMLCombiners
     
    return XMLElements

def setClassAndAddToDictionary(modelClass:str, XMLElements:dict[ET.Element], submodel:ET.Element, nameSuffix:str)->int:
    """
        Sets the class of the submodel and adds it to the dictionary using as key the index of its instance name.
    Args:
        modelClass (str): Class to be set to the submodel.
        XMLElements (dict[ET.Element]): Dictionary where the submodel is to be stored.
        submodel (ET.Element): Submodel from the layout XML file of the WEST model to be modified.
    """    
    setModelClass(submodel, modelClass)

    instName = getInstanceName(submodel)
    iElement = getModelNameIndex(nameSuffix, instName)

    XMLElements[iElement] = submodel

def setPathElementsProp(root:ET.Element, attrSewer:list[dict], attrCatch:list[dict], attrConn:list[dict],
                        XMLsByType: dict[dict[ET.Element]], iCatch:int, iComb:int)->tuple[ET.Element,dict[str],int,int]:                      
    """
        Set the properties of all the elements of a path.
    Args:
        root (ET.Element): Root element of the layout XML file of the WEST model.
        attrSewer (list[dict]): Attributes of the sewers. Sewers are assumed to be in order e.i., the first properties belong to sewer 1.
        attrCatch (list[dict]): Attributes of the catchments. Catchments are assumed to be in order.
        attrConn (list[dict]): Attributes of the connectors. All connectors have the same properties.
        XMLsByType (dict[dict[ET.Element]]): The XMLs of the elements by type. Key is the type of element e.g. STW_C.SEWERS. Then, keys are the
                                             index of element by type i.e., from 1 to the number of sewers in the Layout.xml file.
        iCatch (int): Index of the next catchment to set the properties to.
        iComb (int): Index of the next combiner to be connected to the network.
    Returns:
        tuple[ET.Element, dict[str], int, int]: Updated root element of the xml file. Dictionary of names between display name (key) and 
                                                model name. Updated index of catchments and combiners.
    """    
    quantities = root.find('.//Quantities')

    namesDict = {}
    iCatchN = iCatch
    XMLSewers, XMLCatchments, XMLConnectors, XMLCombiners = XMLsByType[STW_C.SEWERS], XMLsByType[STW_C.CATCHMENTS], XMLsByType[STW_C.CONNECTORS], XMLsByType[STW_C.COMBINERS]

    for sewSec in attrSewer:
        root, quantities = modifySewerModel(root, quantities, XMLSewers, sewSec, namesDict)
    
    for catch in attrCatch:
        root, quantities = modifyCatchmentModel(root, quantities, XMLCatchments[iCatchN], catch, namesDict)
        iCatchN += 1
    
    iCatchN = iCatch
    for conn in attrConn:
        root, quantities = modifyConnectorModel(root, quantities, XMLConnectors[iCatchN], conn, namesDict)
        iCatchN += 1
    
    iCombN = iComb + len(attrCatch)
    for c in range(iComb, iCombN): 
        combinerXML = XMLCombiners[c]
        namesDict[W_C.XML_COMB_NAMES + str(c)] = combinerXML.attrib["Name"]
      
    return root, namesDict, iCatchN, iCombN
    
def updateWESTLayoutFile(layoutXMLPath:str, layoutXMLPath_MOD:str, modelClasses:dict[str], trunkModels:list[list[dict]],
                         branchesModels:dict[dict[list[dict]]], connAttributes:dict[list[dict]]):
    """
        Updates the classes and atributes of all elements on a network, creating links between all elements.
    Args:
        layoutXMLPath (str): Path to the XML file with the layout of the WEST model.
        layoutXMLPath_MOD (str): Path to where the modified layout file will be saved.
        modelClasses (dict[str]): Classes to be set to each type of model. Using Constants as keys e.g. STW_C.SEWER_CLASS, STW_C.CATCH_CLASS.
        trunkModels (list[list[dict]]): Two lists reprenting the trunk of the network. One list has all sewer sections (as dictionaries) and the other all catchments. 
        branchesModels (dict[dict[list[dict]]]): The keys are the name of the pipe that connects the branch and the trunk, the values are the attributes of the elements
                                           in the branch. Each branch dictionary has two elements one list of sewers, one list of the catchments (CONSTANTS as keys).
        connAttributes (list): Attributes of the connectors. all connectors have the same properties.
    """        
    iLink, iCatch, iComb = 1, 1, 1

    tree = ET.parse(layoutXMLPath) # Read the XML file
    root = tree.getroot()  
    linksXML = root.find('.//Links')

    nTanks = branchesModels[list(branchesModels.keys())[-1]][STW_C.PATH][-1][STW_C.TANK_INDEXES][-1] #The last tank of the last branch
    XMLsByType = getModelsByTypeAndSetClasses(root, modelClasses, len(branchesModels), nTanks)
    combiners = {}
    
    for br in branchesModels.keys():

        # Adds the properties of the elements within the branch
        branch = branchesModels[br]

        iLink, iCatch, iComb, root, linksXML, lastPathElement = addPathToLayoutFile(connAttributes[br], branch[STW_C.PATH], branch[STW_C.WCATCHMENTS], 
                                                                                    iLink, iCatch, iComb, root, linksXML, XMLsByType)
        linksXML, iLink, iComb, combName = connectBranchToCombiner(linksXML, lastPathElement, iLink, XMLsByType[STW_C.COMBINERS], iComb)

        combiners[br] = combName
        
    # Trunk
    iLink, iCatch, iComb, root, linksXML, lastPathElement = addPathToLayoutFile(connAttributes[STW_C.TRUNK], trunkModels[0], trunkModels[1], 
                                                                                iLink, iCatch, iComb, root, linksXML, XMLsByType,combiners)

    print("The last element in the network was ", lastPathElement)

    # Save the modified XML to a new file
    ET.indent(tree, space="\t", level=0)
    tree.write(layoutXMLPath_MOD)

def addPathToLayoutFile(connectors:list[dict], sewerSect:list[dict], catchments:list[dict], iLink:int, iCatch:int, iComb:int,
                         root:ET.Element, linksXML:ET.Element, XMLsByType:dict[str,dict[str,ET.Element]], 
                         branches:dict[str,str]=None)->tuple[int,int,int,ET.Element,ET.Element,str]:
    """
        Creates or updates the properties of the elements on the path and create the links between all its elements.
    Args:
        connectors (list[dict]): Attributes of all connectors in the path.
        sewerSect (list[dict]): Attributes of all pipe sections in the path. Are assumed to be in order.
        catchments (list[dict]): Attributes of all catchments in the path. Are assumed to be in order.
        iLink (int): Index of the next link to create.
        iCatch (int): Index of the next catchment to update.
        iComb (int): Index of the next combiner to update
        root (ET.Element): Root element of the layout XML file of the WEST model.
        linksXML (ET.Element): Links element of the WEST's '.Layout.xml' file.
        XMLsByType (dict[str,dict[str,ET.Element]]): The XMLs of the elements by type. Key is the type of element e.g. STW_C.SEWERS. Then, keys are the
                                         index of element by type i.e., from 1 to the number of sewers in the Layout.xml file.
        branches (dict[str,str], optional): The relationship between the name of the branch and the name of the combiner at the end of it. Defaults to None.
    Returns:
        tuple[int,int,int,ET.Element,ET.Element,str]: Indexes of the next link, catchment, and combiner updated. 
                                                    Updated root and links element of the layout XML file of the WEST model.
                                                    Name of the last submodel connected to the network. 
    """    
    assert len(catchments) == len(connectors), f"The number of catchments and connectors in the branch are not the same."

    root, namesDict, iCatchN, iCombN = setPathElementsProp(root, sewerSect, catchments, connectors, XMLsByType, iCatch, iComb)
    linksXML, lastPathElement, iLink, iCatch, iComb = createPathLinks(linksXML, namesDict, catchments, 
                                                                      sewerSect, iLink, iCatch, iComb, branches)
    
    assert iCatch == iCatchN, f"The number of updated catchments in the properties and the path are not the same"
    assert iComb == iCombN, f"The number of updated combiners in the properties and the path are not the same"

    return iLink, iCatch, iComb, root, linksXML, lastPathElement
    
