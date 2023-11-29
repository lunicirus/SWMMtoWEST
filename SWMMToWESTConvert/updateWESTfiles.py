import xml.etree.ElementTree as ET
import re


import SWMMToWESTConvert.WESTConstants as W_C
import SWMMToWESTConvert.SWMMtoWESTConstants as STW_C


#Utils of Xml files
XML_MODEL_PROP_NAME = 'InstanceDisplayName'
XML_QUANTIY = 'Quantity'


#Variables and their translation ---------------------------------------
SEW_DICT_SET = [STW_C.AREATANK,STW_C.VMAX,STW_C.K]
SEW_XML_SET = [W_C.XML_AREA_SEWER,W_C.XML_VMAX_SEWER,W_C.XML_K_SEWER]


CATCH_DICT_SET = [STW_C.AREA,STW_C.N_PEOPLE,STW_C.FLOWRPERPERSON,STW_C.DF_BASELINE]
CATCH_XML_SET = [W_C.XML_AREA_CATCH,W_C.XML_DWF_NPEOPLE,W_C.XML_DWF_QPERPERSON,W_C.XML_DWF_Q_INDUSTRY]


def getQuantityXML(qName, qValue):
    
    # Create a new Quantity element and its sub-elements
    new_quantity = ET.Element(XML_QUANTIY, attrib={'Name': qName})
    props = ET.SubElement(new_quantity, 'Props')
    prop = ET.SubElement(props, 'Prop', attrib={'Name': 'Value', 'Value': qValue})
    
    return new_quantity

#sets the class of the model and obtains the i (name) of its type
def getNameAndSetClass(submodel,classSub,typeNameSub):
    
    submodel.find("./Props/Prop[@Name='ClassName']").set('Value', classSub) # Always the same class
    instName = submodel.find("./Props/Prop[@Name='InstanceName']").get('Value')
            
    try:
        iType = int(re.split("^" + typeNameSub, instName)[1])

    except Exception as e:
        raise Exception("The InstanceName of the sewer (XML) does not follow the expected naming convention (" + str(e) + ")")
        
    return iType, instName

def createsOrModifyQuantity(property,instName,XMLval,quant_XMLelem,root):

    #Get the values to modify
    val = str(property) 
    valQuantityName = '.' + instName + XMLval
    valQuantity = root.find(".//Quantities/Quantity[@Name='"+ valQuantityName +"']")
                
    #if exists changes the value, if not then creates the XML
    if (valQuantity is None):

        valXML = getQuantityXML(valQuantityName, val)
        quant_XMLelem.append(valXML)
                    
    else:
        valQuantity.find("./Props/Prop[@Name='Value']").set('Value', val)

    return quant_XMLelem,root

def modifySewerModel(sewerClass, root, submodel, props):
    
    iSewer,instName = getNameAndSetClass(submodel,sewerClass,W_C.XML_SEWER_NAMES)

    #Iterates the sewer section properties to find the required one and allocate
    for sectP in props:

        # if the sewer section properties apply to the current index!!! (IMPORTANT) 
        if iSewer in sectP[STW_C.TANK_INDEXES]: 
            
            #Sets the name
            nameSewer=  sectP[STW_C.NAME] + "("+ str(iSewer - min(sectP[STW_C.TANK_INDEXES])) + ")"
            submodel.find("./Props/Prop[@Name='InstanceDisplayName']").set('Value', nameSewer) 
            quantities_elem = root.find('.//Quantities')

            for P,XMLval in zip(SEW_DICT_SET,SEW_XML_SET):
                
                val = sectP[P]

                if ((val is not None) & (val != 0)):
                    quantities_elem,root = createsOrModifyQuantity(val,instName,XMLval,quantities_elem,root) 
                
    return root


#the number of people was calculated using the DWFs of the SWMM model
def modifyCatchmentModel(catchClass, root, submodel, props):
    
    iCatch,instName = getNameAndSetClass(submodel,catchClass,W_C.XML_CATCH_NAMES)
    i = 1
    
    #Iterates the catchment properties to find the required one and allocate
    for catchM in props:
        
        if iCatch == i:
            
            #Sets the name
            pos = "(After)" if catchM[STW_C.END] == True else "(Before)"
            name = catchM[STW_C.NAME] + pos
            submodel.find("./Props/Prop[@Name='InstanceDisplayName']").set('Value', name) 

            quantities_elem = root.find('.//Quantities')

            #For simple values
            for P,XMLval in zip(CATCH_DICT_SET,CATCH_XML_SET):

                val = catchM[P]

                if ((val is not None) & (val != 0)):
                    quantities_elem,root = createsOrModifyQuantity(val,instName,XMLval,quantities_elem,root)
                elif ((val is None) | (val == 0))  & ((P == STW_C.AREA) | (P == STW_C.N_PEOPLE)): #If no values are given the 
                    val = 0 #Replace with zero in cas is None
                    quantities_elem,root = createsOrModifyQuantity(val,instName,XMLval,quantities_elem,root)
            
            #For the time pattern
            if (catchM[STW_C.TIMEPATTERN] is not None):
                for h,vh in zip([f"{hour:02})" for hour in range(0,24)],catchM[STW_C.TIMEPATTERN]):

                    quantities_elem,root = createsOrModifyQuantity(vh,instName,W_C.XML_DWF_CUSTOMFLOWPATTERN + h,quantities_elem,root)
            
        i+=1
            
    return root

def modifyConnectorModel(connClass, root, submodel,velTSS,velMin):
    
    nClasses = 10
    
    iConnector,instName = getNameAndSetClass(submodel,connClass,W_C.XML_CONN_NAMES)
    
    #if exists changes the value, if not then creates the XML
    #Assumes if one of the properties exist the others do too
    velMinName = '.' + instName + W_C.XML_CONN_VELMINCLASS 
    velMinVal = root.find(".//Quantities/Quantity[@Name='"+ velMinName +"']")
    if (velMinVal is None):
        
        quantities_elem = root.find('.//Quantities')
        
        #Create the xml tags using as dictionaries
        velMinXML = getQuantityXML(velMinName, str(velMin))
        quantities_elem.append(velMinXML)
        
        for vi, vel in zip(range(0,nClasses,1),velTSS):
            
            #Create the xml tags using as dictionaries
            velName = '.' + instName + W_C.XML_CONN_VELCLASS + '(C'+ str(vi) +')'
            velXML = getQuantityXML(velName, str(vel)) 
            quantities_elem.append(velXML)
                                     
    else:
        velMinVal.find("./Props/Prop[@Name='Value']").set('Value', str(velMin))
        
        for vi, vel in zip(range(0,nClasses,1),velTSS):
            
            velName = '.' + instName + W_C.XML_CONN_VELCLASS + '(C'+ str(vi) +')'
            velVal= root.find(".//Quantities/Quantity[@Name='"+ velName +"']")
            velVal.find("./Props/Prop[@Name='Value']").set('Value', str(vel))
   
    return root

#Props must be in order
def setSewerSectionsVals(xml,xmlOut,sewerClass,propsSewer,catchClass,propsCath,connClass,connectorProps):

    # Read the XML file
    tree = ET.parse(xml)
    root = tree.getroot()  
    submodels = root.findall('.//SubModel') 
    
    print("Number of submodels found ",len(submodels))
     
    #count of sewers and catchments models found in the XML 
    nSewers, nCatchments, nConnectors = 0,0,0
    
    # Iterate over the SubModels
    for submodel  in submodels:
                
        #if the model is a sewer
        if submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.SEWER: 
            root= modifySewerModel(sewerClass, root, submodel, propsSewer)
            nSewers += 1
        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.CATCHMENT:
            root= modifyCatchmentModel(catchClass, root, submodel, propsCath)
            nCatchments += 1
        elif submodel.find("./Props/Prop[@Name='Desc']").get('Value') ==  W_C.CONNECTOR:
            root= modifyConnectorModel(connClass, root, submodel,connectorProps[1],connectorProps[0])
            nConnectors += 1
           
    print("The number of sewers found were ", nSewers, ", catchments ", nCatchments, " and connectors ", nConnectors)
    
    # Save the modified XML to a new file
    ET.indent(tree, space="\t", level=0)
    tree.write(xmlOut)
 
    
