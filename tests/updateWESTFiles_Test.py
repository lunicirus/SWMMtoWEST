import pytest
import xml.etree.ElementTree as ET

from SWMMToWESTConvert import updateWESTfiles as uf

@pytest.fixture
def sample_Links():

    tree = ET.parse('tests/xmlTEST.xml')
    root = tree.getroot()  
    linksXML = root.find('.//Links')
    
    return linksXML, tree

@pytest.fixture
def sample_Elements():

    tree = ET.parse('tests/xmlTESTShortConf.xml')
    root = tree.getroot()  
    
    return root, tree

@pytest.fixture
def names_Dict():

    namesDict = {"PipeSect1(1)": "Icon00008", "PipeSect1(2)": "Icon1","PipeSect1(3)": "Icon3", "Catchment_2": "Icon2",
                 "Catchment_1":"Icon22","Connector_info_1":"Icon23","Well_1":"Two_combiner"}
    
    return namesDict

@pytest.fixture
def names_Dict_Conf():

    names = {}

    sewers = {"Sew{}({})".format(i,j): "Icon{}".format(j)  for i,j in zip([1,1,1,1,2,2,2,3,3,3],range(1, 11))}
    catchments = { "Sew{}(Catch){}{}".format(i,j,h): "Icon{}".format(k) for i, j, k, h in zip([1,1,2,2,3],
                                                                                          ['','','','[input]',''],
                                                                                          range(11, 16),
                                                                                          ['[previous]','','','','']
                                                                                          )}
    connectors = {"Connector_info_{}".format(j): "Icon{}".format(i) for i, j in zip(range(16, 21), range(1, 6))}
    combiners = {"Well_{}".format(j):"Icon{}".format(i) for i, j in zip(range(21, 26), range(1, 6))}

    names.update(sewers)     
    names.update(catchments)     
    names.update(connectors)     
    names.update(combiners)     
    
    return names

@pytest.fixture
def names_Dict_Conf1():

    names = {}

    sewers = {"Sew{}({})".format(i,j): "Icon{}".format(j)  for i,j in zip([1,1,1,2,2,2,3,3,3,3],range(1, 11))}
    catchments = { "Sew{}(Catch){}{}".format(i,j,h): "Icon{}".format(k) for i, j, k, h in zip([1,2,2,2,3],
                                                                                          ['','','','[input]',''],
                                                                                          range(11, 16),
                                                                                          ['','[previous]','','','[previous]']
                                                                                          )}
    connectors = {"Connector_info_{}".format(j): "Icon{}".format(i) for i, j in zip(range(16, 21), range(1, 6))}
    combiners = {"Well_{}".format(j):"Icon{}".format(i) for i, j in zip(range(21, 26), range(1, 6))}

    names.update(sewers)     
    names.update(catchments)     
    names.update(connectors)     
    names.update(combiners)     
    
    return names

@pytest.fixture
def names_Dict_Conf2():

    names = {}

    sewers = {"Sew{}({})".format(i,j): "Icon{}".format(j)  for i,j in zip([1,2,2,2,2,2,3,4,4,4],range(1, 11))}
    catchments = { "Sew{}(Catch){}{}".format(i,j,h): "Icon{}".format(k) for i, j, k, h in zip([2,2,3,4,4],
                                                                                          ['','[input]','','','[input]'],
                                                                                          range(11, 16),
                                                                                          ['[previous]','','','','']
                                                                                          )}
    connectors = {"Connector_info_{}".format(j): "Icon{}".format(i) for i, j in zip(range(16, 21), range(1, 6))}
    combiners = {"Well_{}".format(j):"Icon{}".format(i) for i, j in zip(range(21, 26), range(1, 6))}

    names.update(sewers)     
    names.update(catchments)     
    names.update(connectors)     
    names.update(combiners)     
    
    return names

@pytest.fixture
def elements():

    sewers = [{'PipeName': 'Sew1','tanksIndexes': [1,2,3,4]},
              {'PipeName': 'Sew2','tanksIndexes': [5,6,7]},
              {'PipeName': 'Sew3','tanksIndexes': [8,9,10]}]
    catchments = [{'CatchmentName': 'Sew1(Catch)[previous]','EndNode': False},
                  {'CatchmentName': 'Sew1(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew2(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew2(Catch)[input]','EndNode': True},
                  {'CatchmentName': 'Sew3(Catch)','EndNode': True}]

    return sewers, catchments

@pytest.fixture
def elements1():

    sewers = [{'PipeName': 'Sew1','tanksIndexes': [1,2,3]},
              {'PipeName': 'Sew2','tanksIndexes': [4,5,6]},
              {'PipeName': 'Sew3','tanksIndexes': [7,8,9,10]}]
    catchments = [{'CatchmentName': 'Sew1(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew2(Catch)[previous]','EndNode': False},
                  {'CatchmentName': 'Sew2(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew2(Catch)[input]','EndNode': True},
                  {'CatchmentName': 'Sew3(Catch)[previous]','EndNode': False}]

    return sewers, catchments

@pytest.fixture
def elements2():

    sewers = [{'PipeName': 'Sew1','tanksIndexes': [1]},
              {'PipeName': 'Sew2','tanksIndexes': [2,3,4,5,6]},
              {'PipeName': 'Sew3','tanksIndexes': [7]},
              {'PipeName': 'Sew4','tanksIndexes': [8,9,10]}]
    catchments = [{'CatchmentName': 'Sew2(Catch)[previous]','EndNode': False},
                  {'CatchmentName': 'Sew2(Catch)[input]','EndNode': True},
                  {'CatchmentName': 'Sew3(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew4(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew4(Catch)[input]','EndNode': True}]

    return sewers, catchments

@pytest.fixture
def pipeSectionsAndDict():

    pipeSections = [{"PipeName": "UNI_5277 - UNI_602608", "tanksIndexes": [1, 2, 3]},
                    {"PipeName": "UNI_602607 - UNI_18252", "tanksIndexes": [4, 5, 6]},
                    {"PipeName": "UNI_18251 - DOM_35983", "tanksIndexes": [7, 8, 9]}]
    
    namesDict = {
                    "UNI_5277 - UNI_602608(1)": "Icon1",
                    "UNI_5277 - UNI_602608(2)": "Icon2",
                    "UNI_5277 - UNI_602608(3)": "Icon3",
                    "UNI_602607 - UNI_18252(4)": "Icon4",
                    "UNI_602607 - UNI_18252(5)": "Icon5",
                    "UNI_602607 - UNI_18252(6)": "Icon6",
                    "UNI_18251 - DOM_35983(7)": "Icon7",
                    "UNI_18251 - DOM_35983(8)": "Icon8",
                    "UNI_18251 - DOM_35983(9)": "Icon9"
                }
    return pipeSections, namesDict

#---------------------------Utils-------------------------
def checkLink(xml,linkName,fromM,toM,connName):

    linkC = xml.find(".//Link[@Name='"+ linkName +"']")
    assert linkC is not None, "Link with name " + linkName + " was not found." 
    assert linkC.find(".Props/Prop[@Name='From'][@Value='sub_models."+ fromM +".interface.Outflow']") is not None # Assert that the "prop" element with name "From" and value "Catchment1" exists inside the props element
    assert linkC.find(".Props/Prop[@Name='To'][@Value='sub_models."+ toM +".interface.Inflow']") is not None 
    assert linkC.find(".Props/Prop[@Name='Type'][@Value='Connect']") is not None 
    assert linkC.find(".Props/Prop[@Name='Data'][@Value='ConnectionName=&quot;"+ connName +"&quot; ConnectionType=&quot;WaterLine&quot;']") is not None 

#---------------------------Utils-------------------------

def test_connectCatchment(sample_Links):

    linksXML = sample_Links[0]
    tree = sample_Links[1]
    catchmentNames = {"LinkName": "linkCatch1", "ElementName": "Catchment1", "ConnectionName": "connCatch1"}
    connectorNames = {"LinkName": "linkConn1", "ElementName": "Connection1", "ConnectionName": "connConn1"}
    combNames = {"LinkName": "linkComb1", "ElementName": "Combiner1", "ConnectionName": "connComb1"}
    prevElement = "Sewer1"

    result = uf.createCatchmentLinksXML(linksXML, catchmentNames, connectorNames, combNames, prevElement)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod.xml')

    assert isinstance(result, ET.Element) 
    assert len(list(result)) == 5, "Incorrect final number of links"  # Ensure that three links were appended to the linksXML element

    #Check the values of the link between the previous element and the catchment -----------------------------------------------------
    checkLink(result, catchmentNames["LinkName"], prevElement, catchmentNames["ElementName"], catchmentNames["ConnectionName"])
    #Check the values of the link between catchment and the connection-----------------------------------------------------
    checkLink(result, connectorNames["LinkName"], catchmentNames["ElementName"],connectorNames["ElementName"], connectorNames["ConnectionName"])
    #Check the values of the link between connection and the combiner-----------------------------------------------------
    checkLink(result, combNames["LinkName"], connectorNames["ElementName"], combNames["ElementName"], combNames["ConnectionName"])
    
def test_connectCatchment_lastElement_none(sample_Links):

    linksXML = sample_Links[0]
    tree = sample_Links[1]
    catchmentNames = {"LinkName": "linkCatch1", "ElementName": "Catchment1", "ConnectionName": "connCatch1"}
    connectorNames = {"LinkName": "linkConn1", "ElementName": "Connection1", "ConnectionName": "connConn1"}
    combNames = {"LinkName": "linkComb1", "ElementName": "Combiner1", "ConnectionName": "connComb1"}
    prevElement = None

    result = uf.createCatchmentLinksXML(linksXML, catchmentNames, connectorNames, combNames, prevElement)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod.xml')

    assert isinstance(result, ET.Element) 
    assert len(list(result)) == 4, "Incorrect final number of links"  # Ensure that three links were appended to the linksXML element

    #Check the values of the link between catchment and the connection-----------------------------------------------------
    checkLink(result, connectorNames["LinkName"], catchmentNames["ElementName"],connectorNames["ElementName"], connectorNames["ConnectionName"])
    #Check the values of the link between connection and the combiner-----------------------------------------------------
    checkLink(result, combNames["LinkName"], connectorNames["ElementName"], combNames["ElementName"], combNames["ConnectionName"])

def test_connectPipeSection(sample_Links,names_Dict):

    linksXML = sample_Links[0]
    tree = sample_Links[1]
    linki = 3
    lastElement = "Icon22"
    pipeSection = {"tanksIndexes":[1, 2, 3],"PipeName":"PipeSect1"}

    result_linksXML, result_linki, result_lastElement = uf.connectPipeSection(names_Dict, linksXML, linki, lastElement, pipeSection)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')
    
    assert result_linki == 6, "Incorrect next link index" # Expected updated index for the next link
    assert len(list(result_linksXML)) == 5, "Incorrect final number of links"  # Ensure that two links were appended to the linksXML element
    assert result_lastElement == "Icon3", "Incorrect last element" # Expected updated name of the last element connected

    checkLink(result_linksXML,"Link3","Icon22","Icon00008","CustomOrthogonalLine3")
    checkLink(result_linksXML,"Link4","Icon00008","Icon1","CustomOrthogonalLine4")
    checkLink(result_linksXML,"Link5","Icon1","Icon3","CustomOrthogonalLine5")
    
def test_connectPipeSection_with_lastElement_none(sample_Links,names_Dict):

    linksXML = sample_Links[0]
    tree = sample_Links[1]
    linki = 3
    lastElement = None
    pipeSection = {"tanksIndexes":[1, 2, 3],"PipeName":"PipeSect1"}

    result_linksXML, result_linki, result_lastElement = uf.connectPipeSection(names_Dict, linksXML, linki, lastElement, pipeSection)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')
    
    assert result_linki == 5, "Incorrect next link index" # Expected updated index for the next link
    assert len(list(result_linksXML)) == 4, "Incorrect final number of links"  # Ensure that two links were appended to the linksXML element
    assert result_lastElement == "Icon3", "Incorrect last element" # Expected updated name of the last element connected

    checkLink(result_linksXML,"Link3","Icon00008","Icon1","CustomOrthogonalLine3")
    checkLink(result_linksXML,"Link4","Icon1","Icon3","CustomOrthogonalLine4")

def test_createLinks_conf1(sample_Elements,names_Dict_Conf,elements):

    root = sample_Elements[0]
    tree = sample_Elements[1]
    sewerSections = elements[0]
    catchments = elements[1]

    result_root, lastElement, linki = uf.createLinks(root, names_Dict_Conf, catchments, sewerSections, None, 1)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')

    assert isinstance(result_root, ET.Element) # Assert the result
    links_element = result_root.find(".//Links")
    assert links_element is not None, "Links element not found in the result"
    assert len(list(links_element)) == 24, "Incorrect final number of links"
    
    checkLink(links_element,"Link1","Icon11","Icon16","CustomOrthogonalLine1") #Catch 1 to Conn 1
    checkLink(links_element,"Link2","Icon16","Icon21","CustomOrthogonalLine2") #Conn 1 to Comb 1
    checkLink(links_element,"Link3","Icon21","Icon1","CustomOrthogonalLine3") #Comb 1 to sewer 1

    checkLink(links_element,"Link4","Icon1","Icon2","CustomOrthogonalLine4") #Sew 1 to sew 2
    checkLink(links_element,"Link5","Icon2","Icon3","CustomOrthogonalLine5")
    checkLink(links_element,"Link6","Icon3","Icon4","CustomOrthogonalLine6")
    
    checkLink(links_element,"Link7","Icon4","Icon12","CustomOrthogonalLine7") #Sewer 4 to catch 2
    checkLink(links_element,"Link8","Icon12","Icon17","CustomOrthogonalLine8") #catch 2 to conn 2
    checkLink(links_element,"Link9","Icon17","Icon22","CustomOrthogonalLine9") #Conn 2 to comb 2
    checkLink(links_element,"Link10","Icon22","Icon5","CustomOrthogonalLine10") #Comb 2 to sew 5

    checkLink(links_element,"Link11","Icon5","Icon6","CustomOrthogonalLine11") #sew5 to sew 6
    checkLink(links_element,"Link12","Icon6","Icon7","CustomOrthogonalLine12")

    checkLink(links_element,"Link13","Icon7","Icon13","CustomOrthogonalLine13") #sew 7 to catch 3
    checkLink(links_element,"Link14","Icon13","Icon18","CustomOrthogonalLine14") #catch 3 to conn 3
    checkLink(links_element,"Link15","Icon18","Icon23","CustomOrthogonalLine15") #conn 3 to comb 3

    checkLink(links_element,"Link16","Icon23","Icon14","CustomOrthogonalLine16") #comb 3 to catch 4
    checkLink(links_element,"Link17","Icon14","Icon19","CustomOrthogonalLine17") #catch 4 to conn 4
    checkLink(links_element,"Link18","Icon19","Icon24","CustomOrthogonalLine18") #conn 4 to comb 4
    checkLink(links_element,"Link19","Icon24","Icon8","CustomOrthogonalLine19") #comb 4 to sew 8
    
    checkLink(links_element,"Link20","Icon8","Icon9","CustomOrthogonalLine20") #sew 8 to sew 9
    checkLink(links_element,"Link21","Icon9","Icon10","CustomOrthogonalLine21")

    checkLink(links_element,"Link22","Icon10","Icon15","CustomOrthogonalLine22") #sew 10 to catch 5
    checkLink(links_element,"Link23","Icon15","Icon20","CustomOrthogonalLine23") #catch 5 to conn 5
    checkLink(links_element,"Link24","Icon20","Icon25","CustomOrthogonalLine24") #conn 5 to comb 5

def test_createLinks_conf2(sample_Elements,names_Dict_Conf1,elements1):

    root = sample_Elements[0]
    tree = sample_Elements[1]
    sewerSections = elements1[0]
    catchments = elements1[1]

    result_root, lastElement, linki  = uf.createLinks(root, names_Dict_Conf1, catchments, sewerSections,None,1)

    ET.indent(tree, space="\t", level=0)
    tree.write('tests/xmlTEST_Mod1.xml')

    assert isinstance(result_root, ET.Element) # Assert the result
    links_element = result_root.find(".//Links")
    assert links_element is not None, "Links element not found in the result"
    assert len(list(links_element)) == 24, "Incorrect final number of links"
    
    checkLink(links_element,"Link1","Icon1","Icon2","CustomOrthogonalLine1") 
    checkLink(links_element,"Link2","Icon2","Icon3","CustomOrthogonalLine2") 
    checkLink(links_element,"Link3","Icon3","Icon11","CustomOrthogonalLine3") 

    checkLink(links_element,"Link4","Icon11","Icon16","CustomOrthogonalLine4") 
    checkLink(links_element,"Link5","Icon16","Icon21","CustomOrthogonalLine5")
    checkLink(links_element,"Link6","Icon21","Icon12","CustomOrthogonalLine6")
    checkLink(links_element,"Link7","Icon12","Icon17","CustomOrthogonalLine7") 
    checkLink(links_element,"Link8","Icon17","Icon22","CustomOrthogonalLine8") 
    checkLink(links_element,"Link9","Icon22","Icon4","CustomOrthogonalLine9") 

    checkLink(links_element,"Link10","Icon4","Icon5","CustomOrthogonalLine10") 
    checkLink(links_element,"Link11","Icon5","Icon6","CustomOrthogonalLine11")
    
    checkLink(links_element,"Link12","Icon6","Icon13","CustomOrthogonalLine12") 
    checkLink(links_element,"Link13","Icon13","Icon18","CustomOrthogonalLine13") 
    checkLink(links_element,"Link14","Icon18","Icon23","CustomOrthogonalLine14") 
    checkLink(links_element,"Link15","Icon23","Icon14","CustomOrthogonalLine15") 
    checkLink(links_element,"Link16","Icon14","Icon19","CustomOrthogonalLine16") 
    checkLink(links_element,"Link17","Icon19","Icon24","CustomOrthogonalLine17") 
    checkLink(links_element,"Link18","Icon24","Icon15","CustomOrthogonalLine18") 
    checkLink(links_element,"Link19","Icon15","Icon20","CustomOrthogonalLine19") 
    checkLink(links_element,"Link20","Icon20","Icon25","CustomOrthogonalLine20")
    checkLink(links_element,"Link21","Icon25","Icon7","CustomOrthogonalLine21") 

    checkLink(links_element,"Link22","Icon7","Icon8","CustomOrthogonalLine22") 
    checkLink(links_element,"Link23","Icon8","Icon9","CustomOrthogonalLine23") 
    checkLink(links_element,"Link24","Icon9","Icon10","CustomOrthogonalLine24") 

def test_createLinks_conf3(sample_Elements,names_Dict_Conf2,elements2):

    root = sample_Elements[0]
    tree = sample_Elements[1]
    sewerSections = elements2[0]
    catchments = elements2[1]

    result_root, lastElement, linki  = uf.createLinks(root, names_Dict_Conf2, catchments, sewerSections,None,1)

    ET.indent(tree, space="\t", level=0)
    tree.write('tests/xmlTEST_Mod1.xml')

    assert isinstance(result_root, ET.Element) # Assert the result
    links_element = result_root.find(".//Links")
    assert links_element is not None, "Links element not found in the result"
    assert len(list(links_element)) == 24, "Incorrect final number of links"
    
    checkLink(links_element,"Link1","Icon1","Icon11","CustomOrthogonalLine1") 

    checkLink(links_element,"Link2","Icon11","Icon16","CustomOrthogonalLine2") 
    checkLink(links_element,"Link3","Icon16","Icon21","CustomOrthogonalLine3") 
    checkLink(links_element,"Link4","Icon21","Icon2","CustomOrthogonalLine4") 

    checkLink(links_element,"Link5","Icon2","Icon3","CustomOrthogonalLine5")
    checkLink(links_element,"Link6","Icon3","Icon4","CustomOrthogonalLine6")
    checkLink(links_element,"Link7","Icon4","Icon5","CustomOrthogonalLine7") 
    checkLink(links_element,"Link8","Icon5","Icon6","CustomOrthogonalLine8") 
    checkLink(links_element,"Link9","Icon6","Icon12","CustomOrthogonalLine9") 

    checkLink(links_element,"Link10","Icon12","Icon17","CustomOrthogonalLine10") 
    checkLink(links_element,"Link11","Icon17","Icon22","CustomOrthogonalLine11")
    checkLink(links_element,"Link12","Icon22","Icon7","CustomOrthogonalLine12") 

    checkLink(links_element,"Link13","Icon7","Icon13","CustomOrthogonalLine13") 
    checkLink(links_element,"Link14","Icon13","Icon18","CustomOrthogonalLine14") 
    checkLink(links_element,"Link15","Icon18","Icon23","CustomOrthogonalLine15") 

    checkLink(links_element,"Link16","Icon23","Icon8","CustomOrthogonalLine16") 
    checkLink(links_element,"Link17","Icon8","Icon9","CustomOrthogonalLine17") 
    checkLink(links_element,"Link18","Icon9","Icon10","CustomOrthogonalLine18") 
    checkLink(links_element,"Link19","Icon10","Icon14","CustomOrthogonalLine19") 
    checkLink(links_element,"Link20","Icon14","Icon19","CustomOrthogonalLine20")
    checkLink(links_element,"Link21","Icon19","Icon24","CustomOrthogonalLine21") 

    checkLink(links_element,"Link22","Icon24","Icon15","CustomOrthogonalLine22") 
    checkLink(links_element,"Link23","Icon15","Icon20","CustomOrthogonalLine23") 
    checkLink(links_element,"Link24","Icon20","Icon25","CustomOrthogonalLine24") 

def test_getLastTankModelName(pipeSectionsAndDict):
    
    lastPipe = "UNI_18252"  # Assuming the last pipe is in the second pipe section
    result = uf.getLastTankModelName(pipeSectionsAndDict[0], lastPipe, pipeSectionsAndDict[1]) 

    assert result == "Icon6" 

def test_getLastTankModelName_exception(pipeSectionsAndDict):

    lastPipe = "UnknownPipe"  # Assuming the last pipe is not in any pipe section

    with pytest.raises(Exception) as excinfo: # Call the function and assert the exception
        uf.getLastTankModelName(pipeSectionsAndDict[0], lastPipe, pipeSectionsAndDict[1])

    assert "The tank name was not found" in str(excinfo.value) # Assert the exception message

