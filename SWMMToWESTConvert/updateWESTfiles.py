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
        fromM (str): Model origin e.g. ".Two_combiner7"
        toM (str): Model destination e.g. ".Icon44"
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

    fromVal = W_C.XML_SUBMOD + fromM + W_C.XML_INTERFACE_OUT
    toVal = W_C.XML_SUBMOD + toM + W_C.XML_INTERFACE_IN
    dataVal = W_C.XML_CONN_NAME + "=" + W_C.XML_QUOT + lineName + W_C.XML_QUOT + ' ' + W_C.XML_CONN_TYPE + "=" + W_C.XML_QUOT + W_C.XML_WATERLINE + W_C.XML_QUOT

    new_Link = ET.Element(W_C.XML_LINK, attrib={W_C.XML_NAME: linkName})
    props = ET.SubElement(new_Link, W_C.XML_PROPS)
    propF = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_FROM, W_C.XML_VAL: fromVal})
    propT = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_TO, W_C.XML_VAL: toVal})
    propType = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_TYPE, W_C.XML_VAL: W_C.XML_TYPEVAL_LINK})
    propData = ET.SubElement(props, W_C.XML_PROP, attrib={W_C.XML_NAME: W_C.XML_DATA, W_C.XML_VAL: dataVal})

    return new_Link

def setModelClass(submodel:ET.Element,modelClass:str):
    #TODO documentation

    submodel.find("./Props/Prop[@Name='ClassName']").set('Value', modelClass) # Always the same class

def getModelNames(submodel:ET.Element,typeNameSub:str):
    #TODO documentation 

    instName = submodel.find("./Props/Prop[@Name='InstanceName']").get('Value')
    
    try:
        iType = int(re.split("^" + typeNameSub, instName)[1])
    except Exception as e:
        raise Exception("The InstanceName of the sewer (XML) does not follow the expected naming convention (" + str(e) + ")")
        
    return iType, instName

def createsOrModifyQuantity(property,instName,XMLval,quant_XMLelem,root:ET.Element):

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
def modifySewerModel(root:ET.Element, quantities:ET.Element, submodel:ET.Element, sewerClass:str, props)->tuple[ET.Element,ET.Element,str]:
    """
        Modifies the class and properties of an existent model type SEWER in a WEST project
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        quantities (ET.Element) : All quantities in the WEST's .Layout.xml file 
        submodel (ET.Element): Model element to be modified
        sewerClass (str): Class to assign to the model 
        props (TODO): Properties to assign to the model
    Returns:
        tuple[ET.Element,ET.Element,str]: Updated root and quantities elements of the WEST's .Layout.xml file. InstanceName of the model 
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
                
    return root, quantities, instName

def modifyCatchmentModel(root:ET.Element, quantities:ET.Element, submodel:ET.Element, catchClass:str, props)->tuple[ET.Element,ET.Element,str]:
    """
        Modifies the class and properties of an existent model type CATCHMENT in a WEST project.
    Args:
        root (ET.Element): Root element of the WEST's .Layout.xml file 
        quantities (ET.Element) : All quantities in the WEST's .Layout.xml file 
        submodel (ET.Element): Model element to be modified
        catchClass (str): Class to assign to the model 
        props (TODO): Properties to assign to the model
    Returns:
        tuple[ET.Element,ET.Element,str]: Updated root and quantities elements of the WEST's .Layout.xml file. InstanceName of the model 
    """ 
    i = 1

    setModelClass(submodel,catchClass)
    iCatch,instName = getModelNames(submodel,W_C.XML_CATCH_NAMES)
    
    #Iterates the catchment properties to find the required one and allocate
    for catchM in props:
        
        if iCatch == i:
            
            #Sets the name
            submodel.find("./Props/Prop[@Name='"+ W_C.XML_MODEL_PROP_NAME + "']").set('Value', catchM[STW_C.NAME] ) 

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
            
    return root, quantities

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
   
    return root, quantities
#-------------Create Links ----------------------------------------------
def createLinks(root:ET.Element,namesDict:dict[str],propsCath:list[dict]):

        if catchM[STW_C.END]:



    return root

def setPropertiesAndClasses(xml:str,xmlOut:str,
                            sewerClass:str,propsSewer:str,
                            catchClass:str,propsCath:list[dict],
                            connClass:list[dict],connectorProps:list[dict]):
    #Props must be in order TODO documentation

    # Read the XML file
    tree = ET.parse(xml)
    root = tree.getroot()  

    submodels = root.findall('.//SubModel') 
    quantities = root.find('.//Quantities')

    print("Number of submodels found ",len(submodels))
    nSewers, nCatchments, nConnectors = 0,0,0 #count of sewers and catchments models found in the XML 
    namesDict = {}
    
    for submodel  in submodels: # Iterate over the SubModels
        
        if submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.SEWER: #if the model is a sewer
            root, quantities, instName = modifySewerModel(root, quantities, submodel, sewerClass, propsSewer)
            namesDict[instName] = submodel.attrib["Name"]
            nSewers += 1

        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.CATCHMENT: #if the model is a catchment
            root, quantities, instName = modifyCatchmentModel(root, quantities, submodel, catchClass, propsCath)
            namesDict[instName] = submodel.attrib["Name"]
            nCatchments += 1

        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.CONNECTOR: #if the model is a connector
            root, quantities, instName = modifyConnectorModel(root, quantities, submodel, connClass, connectorProps[1],connectorProps[0])
            namesDict[instName] = submodel.attrib["Name"]
            nConnectors += 1

    
    #Create the links
    createLinks(root,namesDict,propsCath)
           
    print("The number of sewers found were ", nSewers, ", catchments ", nCatchments, " and connectors ", nConnectors)
    
    # Save the modified XML to a new file
    ET.indent(tree, space="\t", level=0)
    tree.write(xmlOut)
 
    
