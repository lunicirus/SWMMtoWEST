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
def sample_Submodel():

    tree = ET.parse('tests/xmlTEST.xml')
    root = tree.getroot()  
    submodel = root.findall('.//SubModel')[0]
    
    return submodel, tree

@pytest.fixture
def sample_Elements():

    tree = ET.parse('tests/xmlTESTShortConf.xml')
    root = tree.getroot()  
    
    return root, tree

@pytest.fixture
def names_Dict():

    namesDict = {"PipeSect1(0)": "Icon00008", "PipeSect1(1)": "Icon1","PipeSect1(2)": "Icon3", "Catchment_2": "Icon2",
                 "Catchment_1":"Icon22","Connector_info_1":"Icon23","Well_1":"Two_combiner"}
    
    return namesDict

@pytest.fixture
def names_Dict_Conf():

    names = {}

    sewers = {"Sew_{}i - Sew_{}f({})".format(i,i,j): "Icon{}".format(k)  for i,j,k in zip([1,1,1,1,2,2,2,3,3,3],
                                                                                          [0,1,2,3,0,1,2,0,1,2],
                                                                                          range(1,11))}
    catchments = { "Sew_{}i - Sew_{}f(Catch){}{}".format(i,i,j,h): "Icon{}".format(k) for i, j, k, h in zip([1,1,2,2,3],
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

    sewers = {"Sew_{}i - Sew_{}f({})".format(i,i,j): "Icon{}".format(k)  for i,j,k in zip([1,1,1,2,2,2,3,3,3,3],
                                                                                        [0,1,2,0,1,2,0,1,2,3],
                                                                                        range(1,11))}
    catchments = { "Sew_{}i - Sew_{}f(Catch){}{}".format(i,i,j,h): "Icon{}".format(k) for i, j, k, h in zip([1,2,2,2,3],
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

    sewers = {"Sew_{}i - Sew_{}f({})".format(i,i,j): "Icon{}".format(k)  for i,j,k in zip([1,2,2,2,2,2,3,4,4,4],
                                                                                        [0,0,1,2,3,4,0,0,1,2],
                                                                                        range(1,11))}
    catchments = { "Sew_{}i - Sew_{}f(Catch){}{}".format(i,i,j,h): "Icon{}".format(k) for i, j, k, h in zip([2,2,3,4,4],
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

    sewers = [{'PipeName': 'Sew_1i - Sew_1f','tanksIndexes': [1,2,3,4]},
              {'PipeName': 'Sew_2i - Sew_2f','tanksIndexes': [5,6,7]},
              {'PipeName': 'Sew_3i - Sew_3f','tanksIndexes': [8,9,10]}]
    catchments = [{'CatchmentName': 'Sew_1i - Sew_1f(Catch)[previous]','EndNode': False},
                  {'CatchmentName': 'Sew_1i - Sew_1f(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew_2i - Sew_2f(Catch)[input]','EndNode': True},
                  {'CatchmentName': 'Sew_2i - Sew_2f(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew_3i - Sew_3f(Catch)','EndNode': True}]

    return sewers, catchments

@pytest.fixture
def elements1():

    sewers = [{'PipeName': 'Sew_1i - Sew_1f','tanksIndexes': [1,2,3]},
              {'PipeName': 'Sew_2i - Sew_2f','tanksIndexes': [4,5,6]},
              {'PipeName': 'Sew_3i - Sew_3f','tanksIndexes': [7,8,9,10]}]
    catchments = [{'CatchmentName': 'Sew_1i - Sew_1f(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew_2i - Sew_2f(Catch)[previous]','EndNode': False},
                  {'CatchmentName': 'Sew_2i - Sew_2f(Catch)[input]','EndNode': True},
                  {'CatchmentName': 'Sew_2i - Sew_2f(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew_3i - Sew_3f(Catch)[previous]','EndNode': False}]

    return sewers, catchments

@pytest.fixture
def elements2():

    sewers = [{'PipeName': 'Sew_1i - Sew_1f','tanksIndexes': [1]},
              {'PipeName': 'Sew_2i - Sew_2f','tanksIndexes': [2,3,4,5,6]},
              {'PipeName': 'Sew_3i - Sew_3f','tanksIndexes': [7]},
              {'PipeName': 'Sew_4i - Sew_4f','tanksIndexes': [8,9,10]}]
    catchments = [{'CatchmentName': 'Sew_2i - Sew_2f(Catch)[previous]','EndNode': False},
                  {'CatchmentName': 'Sew_2i - Sew_2f(Catch)[input]','EndNode': True},
                  {'CatchmentName': 'Sew_3i - Sew_3f(Catch)','EndNode': True},
                  {'CatchmentName': 'Sew_4i - Sew_4f(Catch)[input]','EndNode': True},
                  {'CatchmentName': 'Sew_4i - Sew_4f(Catch)','EndNode': True}]

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

@pytest.fixture(scope='session')
def initialXML():
    
    XMLfilePath = 'tests/xmlTESTLongConfM.xml'
    tree = ET.parse('tests/xmlTESTBlank.xml') 
    submodels = tree.getroot().find('.//SubModels')

    iconIndex = 1

    # Add new sewers
    for i in range(1, 25):
        submodel = ET.Element('SubModel', {'Name': f'Icon{iconIndex}'})
        props = ET.SubElement(submodel, 'Props')
        ET.SubElement(props, 'Prop', {'Name': f'InstanceName', 'Value': f'Sew_{i}'})
        ET.SubElement(props, 'Prop', {'Name': f'InstanceDisplayName', 'Value': 'PipeSectionX'})
        ET.SubElement(props, 'Prop', {'Name': f'ClassName', 'Value': 'genericClass'})
        ET.SubElement(props, 'Prop', {'Name': f'Desc', 'Value': 'Sewer'})
        ET.SubElement(props, 'Prop', {'Name': f'Unit', 'Value': ''})
        favorites = ET.SubElement(submodel, 'Favorites')
        submodels.append(submodel)
        iconIndex += 1

    #Add the catchments
    for i in range(1, 8):
        submodel = ET.Element('SubModel', {'Name': f'Icon{iconIndex}'})
        props = ET.SubElement(submodel, 'Props')
        ET.SubElement(props, 'Prop', {'Name': f'InstanceName', 'Value': f'Catchment_{i}'})
        ET.SubElement(props, 'Prop', {'Name': f'InstanceDisplayName', 'Value': 'PipeSectionX(Catch)'})
        ET.SubElement(props, 'Prop', {'Name': f'ClassName', 'Value': 'genericClass'})
        ET.SubElement(props, 'Prop', {'Name': f'Desc', 'Value': 'Catchment'})
        ET.SubElement(props, 'Prop', {'Name': f'Unit', 'Value': ''})
        favorites = ET.SubElement(submodel, 'Favorites')
        submodels.append(submodel)
        iconIndex += 1

    #Add the connectors
    for i in range(1, 8):
        submodel = ET.Element('SubModel', {'Name': f'Icon{iconIndex}'})
        props = ET.SubElement(submodel, 'Props')
        ET.SubElement(props, 'Prop', {'Name': f'InstanceName', 'Value': f'Connector_info_{i}'})
        ET.SubElement(props, 'Prop', {'Name': f'InstanceDisplayName', 'Value': f'Connector_info_{i}'})
        ET.SubElement(props, 'Prop', {'Name': f'ClassName', 'Value': 'genericClass'})
        ET.SubElement(props, 'Prop', {'Name': f'Desc', 'Value': 'Connector_info'})
        ET.SubElement(props, 'Prop', {'Name': f'Unit', 'Value': ''})
        favorites = ET.SubElement(submodel, 'Favorites')
        submodels.append(submodel)
        iconIndex += 1
    
    #Add the combiners
    for i in range(1, 11):
        submodel = ET.Element('SubModel', {'Name': f'Icon{iconIndex}'})
        props = ET.SubElement(submodel, 'Props')
        ET.SubElement(props, 'Prop', {'Name': f'InstanceName', 'Value': f'Well_{i}'})
        ET.SubElement(props, 'Prop', {'Name': f'InstanceDisplayName', 'Value': f'Well_{i}'})
        ET.SubElement(props, 'Prop', {'Name': f'ClassName', 'Value': 'genericClass'})
        ET.SubElement(props, 'Prop', {'Name': f'Desc', 'Value': 'Two combiner'})
        ET.SubElement(props, 'Prop', {'Name': f'Unit', 'Value': ''})
        favorites = ET.SubElement(submodel, 'Favorites')
        submodels.append(submodel)
        iconIndex += 1

    # Write back to the XML file
    ET.indent(tree, space="\t", level=0)
    tree.write(XMLfilePath, encoding='utf-8', xml_declaration=True)

    return XMLfilePath

@pytest.fixture(scope='session')
def dictForWEST():

    listTrunk = [] 
    listSewersTrunk = []
    listCatchTrunk = []
    
    for s, tanks in zip(range(1,6),[[1,2,3,4],[5,6,7,8],[9,10],[11,12],[13]]):
        name = 'pipe' + str(s) + '00' + ' - ' + 'pipe' + str(s) + '01' 
        valArea = str(s + 10)
        sew = createMockSewerDict(name, valArea, tanks)
        listSewersTrunk.append(sew)

    namesCatchs = ['pipe100 - pipe101(Catch)[previous]','pipe100 - pipe101(Catch)','pipe200 - pipe201(Catch)','pipe400 - pipe401(Catch)'] 
    for c,name,end in zip(range(1,5), namesCatchs,[False,True,True,True]):
        area = str(c + 10)
        catch = createMockCatchDict(name, area, end)
        listCatchTrunk.append(catch)

    listTrunk.append(listSewersTrunk)
    listTrunk.append(listCatchTrunk)

    # --------------- Branches ----------------------------------------------
    branches = {}
    
    #---------------branch 1---------------------------------------------------------
    listb = {} 
    sew = createMockSewerDict('pipe600 - pipe601', '60', [14,15,16])
    catch = createMockCatchDict('pipe600 - pipe601(Catch)[previous]', '60', False)
    listb['PathTankInSeries'] = [sew]
    listb['WESTCatchments'] = [catch]
    branches['pipe101']= listb
    #---------------branch 2---------------------------------------------------------
    listb2 = {} 
    sew = createMockSewerDict('pipe700 - pipe701', '70', [17,18])
    sew2 = createMockSewerDict('pipe800 - pipe801', '80', [19,20,21,22])
    catch = createMockCatchDict('pipe700 - pipe701(Catch)', '70', True)
    listb2['PathTankInSeries'] = [sew,sew2]
    listb2['WESTCatchments'] = [catch]
    branches['pipe301']= listb2
    #---------------branch 3---------------------------------------------------------
    listb3 = {} 
    sew = createMockSewerDict('pipe900 - pipe901', '90', [23,24])
    catch = createMockCatchDict('pipe900 - pipe901(Catch)', '90', True)
    listb3['PathTankInSeries'] = [sew]
    listb3['WESTCatchments'] = [catch]
    branches['pipe401']= listb3

    #--------------Connectors-----------------------------------------------
    connectorsDict = {}
    for b, indexes in zip(['Trunk','pipe101','pipe301','pipe401'],[range(1,5),[5],[6],[7]]):
        connectors= []
        for c in indexes:
            conn = createMockConnector(str(c)+'1')
            connectors.append(conn)
        connectorsDict[b] = connectors

    return listTrunk, branches, connectorsDict

@pytest.fixture(scope='session')
def modelClasses():

    modelClasses = {'Sewers Class': 'ClassTEST_SEW',
                    'Catchments Class': 'ClassTEST_CATH',
                    'Connectors Class': 'ClassTEST_CON',
                    'Two Way Combiners Class': 'ClassTEST_COMB'}
    
    return modelClasses

#---------------------------Utils-------------------------¸
def createMockSewerDict(name: str, valArea: str, listIndexes: list[int]):

    ssDict = {'PipeName': name,
              'AreaTank': valArea,
              'Volmax': 10,
              'k':0.2,
              'tanksIndexes': listIndexes}
    
    return ssDict

def createMockCatchDict(name: str, valArea: str, isEnd: bool):

    ssDict = {'CatchmentName': name,
              'AreaCatchment': valArea,
              'NumberPeople': 300,
              'FlowPerPerson': 40,
              'DirectFBaseline':5,
              'TimePattern':None,
              'EndNode': isEnd}
    
    return ssDict

def createMockConnector(velMin: int):

    conDict = {'VelMinima': velMin,
               'VelClasses':[6,7,8,9,10,11,12,13,14,15]}
    return conDict

def checkProperty(root,quantity,valquantity):

    quantityExpression = ".//Quantity[@Name='" + quantity + "']/Props/Prop[@Name='Value'][@Value='" + valquantity + "']"

    quantities = root.findall(quantityExpression)

    assert quantities , f"The quantity {quantity} was not updated"

def checkLink(xml:ET.Element,linkName:str,fromM:str,toM:str,connName:str,inflowNumber:str=''):

    linkC = xml.find(".//Link[@Name='"+ linkName +"']")
    assert linkC is not None, f"Link with name " + linkName + " was not found." 
    assert linkC.find(".Props/Prop[@Name='From'][@Value='sub_models."+ fromM +".interface.Outflow']") is not None, f"The property 'From' of the link " + linkName + " was not correct" 
    assert linkC.find(".Props/Prop[@Name='To'][@Value='sub_models."+ toM +".interface.Inflow" + inflowNumber + "']") is not None, f"The property 'To' of the link " + linkName + " was not correct"
    assert linkC.find(".Props/Prop[@Name='Type'][@Value='Connect']") is not None, f"The property 'Type' of the link " + linkName + " was not correct"
    assert linkC.find(".Props/Prop[@Name='Data'][@Value='ConnectionName=&quot;"+ connName +"&quot; ConnectionType=&quot;WaterLine&quot;']") is not None, f"The property 'ConnectionName' of the link " + linkName + " was not correct"

#---------------------------Utils-------------------------
def test_setModelClass(sample_Submodel):

    submodel=sample_Submodel[0]
    tree = sample_Submodel[1]
    uf.setModelClass(submodel, "NewModelClass")

    assert submodel.find("./Props/Prop[@Name='ClassName']").get('Value') == "NewModelClass"
    
    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')

def test_setDisplayName(sample_Submodel):

    submodel=sample_Submodel[0]
    tree = sample_Submodel[1]
    uf.setDisplayName(submodel, "NewName")

    assert submodel.find("./Props/Prop[@Name='InstanceDisplayName']").get('Value') == "NewName"
    
    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')

def test_getInstanceName(sample_Submodel):

    submodel=sample_Submodel[0]
    insName = uf.getInstanceName(submodel)

    assert insName == "Sew_1"

def test_setClassAndAddToDictionary(sample_Submodel):
    
    XMLDictEle = {}
    submodel=sample_Submodel[0]
    tree = sample_Submodel[1]
    
    uf.setClassAndAddToDictionary("NewModelClass1", XMLDictEle, submodel, "Sew_")

    # Assert that the model class has been set correctly
    assert submodel.find("./Props/Prop[@Name='ClassName']").get('Value') == "NewModelClass1", f"The class was not set correctly"

    # Assert that the submodel has been added to the dictionary with the correct key
    assert len(XMLDictEle) == 1

    print(list(XMLDictEle.keys()))
    assert 1 in XMLDictEle
    assert XMLDictEle[1] == submodel

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

    #Check the values of the link between the previous element and the combiner -----------------------------------------------------
    checkLink(result, catchmentNames["LinkName"], prevElement, combNames["ElementName"], catchmentNames["ConnectionName"],"1")
    #Check the values of the link between catchment and the connection-----------------------------------------------------
    checkLink(result, connectorNames["LinkName"], catchmentNames["ElementName"],connectorNames["ElementName"], connectorNames["ConnectionName"])
    #Check the values of the link between connection and the combiner-----------------------------------------------------
    checkLink(result, combNames["LinkName"], connectorNames["ElementName"], combNames["ElementName"], combNames["ConnectionName"],"2")
    
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
    checkLink(result, combNames["LinkName"], connectorNames["ElementName"], combNames["ElementName"], combNames["ConnectionName"],"2")

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
    linksEle = root.find(".//Links")
    sewerSections = elements[0]
    catchments = elements[1]

    result_links, lastElement, linki, catchi, comb1 = uf.createPathLinks(linksEle, names_Dict_Conf, catchments, sewerSections, 1, 1, 1, None)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')

    assert isinstance(result_links, ET.Element) # Assert the result
    assert len(list(result_links)) == 24, "Incorrect final number of links"
    
    checkLink(result_links,"Link1","Icon11","Icon16","CustomOrthogonalLine1") #Catch 1 to Conn 1
    checkLink(result_links,"Link2","Icon16","Icon21","CustomOrthogonalLine2","2") #Conn 1 to Comb 1
    
    checkLink(result_links,"Link3","Icon21","Icon1","CustomOrthogonalLine3") #Comb 1 to sewer 1
    checkLink(result_links,"Link4","Icon1","Icon2","CustomOrthogonalLine4") #Sew 1 to sew 2
    checkLink(result_links,"Link5","Icon2","Icon3","CustomOrthogonalLine5")
    checkLink(result_links,"Link6","Icon3","Icon4","CustomOrthogonalLine6") #Sew 3 to sew 4
    
    checkLink(result_links,"Link7","Icon4","Icon22","CustomOrthogonalLine7","1") #Sewer 4 to comb 2
    checkLink(result_links,"Link8","Icon12","Icon17","CustomOrthogonalLine8") #catch 2 to conn 2
    checkLink(result_links,"Link9","Icon17","Icon22","CustomOrthogonalLine9","2") #Conn 2 to comb 2

    checkLink(result_links,"Link10","Icon22","Icon5","CustomOrthogonalLine10") #Comb 2 to sew 5
    checkLink(result_links,"Link11","Icon5","Icon6","CustomOrthogonalLine11") #sew5 to sew 6
    checkLink(result_links,"Link12","Icon6","Icon7","CustomOrthogonalLine12")

    checkLink(result_links,"Link13","Icon7","Icon23","CustomOrthogonalLine13","1") #sew 7 to comb 3
    checkLink(result_links,"Link14","Icon13","Icon18","CustomOrthogonalLine14") #catch 3 to conn 3
    checkLink(result_links,"Link15","Icon18","Icon23","CustomOrthogonalLine15","2") #conn 3 to comb 3

    checkLink(result_links,"Link16","Icon23","Icon24","CustomOrthogonalLine16","1") #comb 3 to comb 4
    checkLink(result_links,"Link17","Icon14","Icon19","CustomOrthogonalLine17") #catch 4 to conn 4
    checkLink(result_links,"Link18","Icon19","Icon24","CustomOrthogonalLine18","2") #conn 4 to comb 4
    checkLink(result_links,"Link19","Icon24","Icon8","CustomOrthogonalLine19") #comb 4 to sew 8
    
    checkLink(result_links,"Link20","Icon8","Icon9","CustomOrthogonalLine20") #sew 8 to sew 9
    checkLink(result_links,"Link21","Icon9","Icon10","CustomOrthogonalLine21")

    checkLink(result_links,"Link22","Icon10","Icon25","CustomOrthogonalLine22","1") #sew 10 to comb 5
    checkLink(result_links,"Link23","Icon15","Icon20","CustomOrthogonalLine23") #catch 5 to conn 5
    checkLink(result_links,"Link24","Icon20","Icon25","CustomOrthogonalLine24","2") #conn 5 to comb 5

def test_createLinks_conf2(sample_Elements,names_Dict_Conf1,elements1):

    root = sample_Elements[0]
    tree = sample_Elements[1]
    links_element = root.find(".//Links")
    sewerSections = elements1[0]
    catchments = elements1[1]

    result_links, lastElement, linki, catchi, comb1  = uf.createPathLinks(links_element, names_Dict_Conf1, catchments, sewerSections,1,1,1,None)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')

    assert isinstance(result_links, ET.Element) # Assert the result
    assert len(list(links_element)) == 24, "Incorrect final number of links"
    
    checkLink(links_element,"Link1","Icon1","Icon2","CustomOrthogonalLine1") 
    checkLink(links_element,"Link2","Icon2","Icon3","CustomOrthogonalLine2") 
    checkLink(links_element,"Link3","Icon3","Icon21","CustomOrthogonalLine3","1") 

    checkLink(links_element,"Link4","Icon11","Icon16","CustomOrthogonalLine4") 
    checkLink(links_element,"Link5","Icon16","Icon21","CustomOrthogonalLine5","2")
    checkLink(links_element,"Link6","Icon21","Icon22","CustomOrthogonalLine6","1")
    checkLink(links_element,"Link7","Icon12","Icon17","CustomOrthogonalLine7") 
    checkLink(links_element,"Link8","Icon17","Icon22","CustomOrthogonalLine8","2") 
    checkLink(links_element,"Link9","Icon22","Icon4","CustomOrthogonalLine9") 

    checkLink(links_element,"Link10","Icon4","Icon5","CustomOrthogonalLine10") 
    checkLink(links_element,"Link11","Icon5","Icon6","CustomOrthogonalLine11")
    
    checkLink(links_element,"Link12","Icon6","Icon23","CustomOrthogonalLine12","1") 
    checkLink(links_element,"Link13","Icon13","Icon18","CustomOrthogonalLine13") 
    checkLink(links_element,"Link14","Icon18","Icon23","CustomOrthogonalLine14","2") 
    checkLink(links_element,"Link15","Icon23","Icon24","CustomOrthogonalLine15","1") 
    checkLink(links_element,"Link16","Icon14","Icon19","CustomOrthogonalLine16") 
    checkLink(links_element,"Link17","Icon19","Icon24","CustomOrthogonalLine17","2") 
    checkLink(links_element,"Link18","Icon24","Icon25","CustomOrthogonalLine18","1") 
    checkLink(links_element,"Link19","Icon15","Icon20","CustomOrthogonalLine19") 
    checkLink(links_element,"Link20","Icon20","Icon25","CustomOrthogonalLine20","2")
    checkLink(links_element,"Link21","Icon25","Icon7","CustomOrthogonalLine21") 

    checkLink(links_element,"Link22","Icon7","Icon8","CustomOrthogonalLine22") 
    checkLink(links_element,"Link23","Icon8","Icon9","CustomOrthogonalLine23") 
    checkLink(links_element,"Link24","Icon9","Icon10","CustomOrthogonalLine24") 

def test_createLinks_conf3(sample_Elements,names_Dict_Conf2,elements2):

    root = sample_Elements[0]
    tree = sample_Elements[1]
    links_element = root.find(".//Links")
    sewerSections = elements2[0]
    catchments = elements2[1]

    result_links, lastElement, linki, catchi, comb1  = uf.createPathLinks(links_element, names_Dict_Conf2, catchments, sewerSections,1,1,1,None)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')

    assert isinstance(result_links, ET.Element) # Assert the result
    assert len(list(result_links)) == 24, f"Incorrect final number of links"
    
    checkLink(links_element,"Link1","Icon1","Icon21","CustomOrthogonalLine1","1") 

    checkLink(links_element,"Link2","Icon11","Icon16","CustomOrthogonalLine2") 
    checkLink(links_element,"Link3","Icon16","Icon21","CustomOrthogonalLine3","2") 
    checkLink(links_element,"Link4","Icon21","Icon2","CustomOrthogonalLine4") 

    checkLink(links_element,"Link5","Icon2","Icon3","CustomOrthogonalLine5")
    checkLink(links_element,"Link6","Icon3","Icon4","CustomOrthogonalLine6")
    checkLink(links_element,"Link7","Icon4","Icon5","CustomOrthogonalLine7") 
    checkLink(links_element,"Link8","Icon5","Icon6","CustomOrthogonalLine8") 
    checkLink(links_element,"Link9","Icon6","Icon22","CustomOrthogonalLine9","1") 

    checkLink(links_element,"Link10","Icon12","Icon17","CustomOrthogonalLine10") 
    checkLink(links_element,"Link11","Icon17","Icon22","CustomOrthogonalLine11","2")
    checkLink(links_element,"Link12","Icon22","Icon7","CustomOrthogonalLine12") 

    checkLink(links_element,"Link13","Icon7","Icon23","CustomOrthogonalLine13","1") 
    checkLink(links_element,"Link14","Icon13","Icon18","CustomOrthogonalLine14") 
    checkLink(links_element,"Link15","Icon18","Icon23","CustomOrthogonalLine15","2") 

    checkLink(links_element,"Link16","Icon23","Icon8","CustomOrthogonalLine16") 
    checkLink(links_element,"Link17","Icon8","Icon9","CustomOrthogonalLine17") 
    checkLink(links_element,"Link18","Icon9","Icon10","CustomOrthogonalLine18") 
    checkLink(links_element,"Link19","Icon10","Icon24","CustomOrthogonalLine19","1") 
    checkLink(links_element,"Link20","Icon14","Icon19","CustomOrthogonalLine20")
    checkLink(links_element,"Link21","Icon19","Icon24","CustomOrthogonalLine21","2") 

    checkLink(links_element,"Link22","Icon24","Icon25","CustomOrthogonalLine22","1") 
    checkLink(links_element,"Link23","Icon15","Icon20","CustomOrthogonalLine23") 
    checkLink(links_element,"Link24","Icon20","Icon25","CustomOrthogonalLine24","2") 

def test_getModelsByTypeAndSetClasses(initialXML,modelClasses):

    tree = ET.parse(initialXML)
    root = tree.getroot()

    allXMLSubmodels = uf.getModelsByTypeAndSetClasses(root,modelClasses,3,24)

    keysXMLModels = ['Sewers','Catchments','Connectors','Combiners']
    keysModelClasses = ['Sewers Class', 'Catchments Class', 'Connectors Class', 'Two Way Combiners Class']

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_RESUKT.xml')

    for typeM, classType, numPerType in zip(keysXMLModels,keysModelClasses,[24,7,7,10]):
        
        modelsElement = allXMLSubmodels[typeM]

        assert len(modelsElement) == numPerType, f"Incorrect final number of {typeM}"

        for key in modelsElement:
            submodel= modelsElement[key]
            assert submodel.find("./Props/Prop[@Name='ClassName']").get('Value') == modelClasses[classType], f"The class was not set correctly for {submodel}"

def test_setPathElementsProp(initialXML,modelClasses,dictForWEST):

    tree = ET.parse(initialXML)
    root = tree.getroot()
    
    allXMLSubmodels = uf.getModelsByTypeAndSetClasses(root,modelClasses,3,24)
    root, namesDict, iCatchN, iCombN = uf. setPathElementsProp(root, dictForWEST[0][0], dictForWEST[0][1], dictForWEST[2]['Trunk'], allXMLSubmodels, 1, 1)
    
    assert iCatchN == 5, f"The next index for catchment is not the expected"
    assert iCombN == 5, f"The next index for combiner is not the expected"

#   ET.indent(tree, space="\t", level=0)
#   tree.write('tests/xmlTEST_RESUKT.xml')

    # ------------------------check the updating of the quantities ------------------------------------------------
    quantities = {'.Sew_1.A':'11','.Sew_1.k':'0.2',
                  '.Sew_6.A':'12','.Sew_6.k':'0.2',
                  '.Sew_10.A':'13','.Sew_10.k':'0.2',
                  '.Sew_13.A':'15','.Sew_13.k':'0.2',
                  '.Catchment_1.TotalArea':'11','.Catchment_1.Inhabitants':'300',
                  '.Catchment_4.TotalArea':'14','.Catchment_4.Inhabitants':'300',
                  '.Connector_info_1.Vs_limit_min':'11','.Connector_info_1.Vs_limit(C0)':'6',
                  '.Connector_info_4.Vs_limit_min':'41','.Connector_info_4.Vs_limit(C0)':'6',}

    for q in quantities:

        checkProperty(root,q,quantities[q])

    
    # ------------------------check the updating of the quantities ------------------------------------------------
    dict_Resul= {}
    sewers = ['pipe100 - pipe101(0)','pipe100 - pipe101(1)','pipe100 - pipe101(2)','pipe100 - pipe101(3)',
            'pipe200 - pipe201(0)','pipe200 - pipe201(1)','pipe200 - pipe201(2)','pipe200 - pipe201(3)',
            'pipe300 - pipe301(0)','pipe300 - pipe301(1)','pipe400 - pipe401(0)','pipe400 - pipe401(1)','pipe500 - pipe501(0)']
    catchments = ['pipe100 - pipe101(Catch)[previous]','pipe100 - pipe101(Catch)','pipe200 - pipe201(Catch)','pipe400 - pipe401(Catch)']

    for ele, prefix, icons in zip([sewers,catchments,range(1,5),range(1,5)],
                            ['','','Connector_info_','Well_'],
                            [range(1,14),range(25,29),range(32,36),range(39,43)]):

        for s,i in zip(ele, icons):
            dict_Resul[prefix + str(s)] =  "Icon" + str(i)

    assert namesDict == dict_Resul, f"The dictionary with name equivalences between display and model name is not the expected"

def test_connectBranchToCombiner(sample_Links):
  
    lastBranchEle = "Icon23"
    linki = 3
    iComb = 4
    tree = sample_Links[1]
    eleSample = {4: ET.Element("SubModel", {"Name": "IconCombiner"})}

    # Call the function
    result_linksXML, iLinkN, iCombN, result_lastElement = uf.connectBranchToCombiner(sample_Links[0], lastBranchEle, linki, eleSample, iComb)
    
    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_RESUKT.xml')

    # Assert the result
    assert len(result_linksXML.findall(".//Link")) == 3
    assert result_linksXML.findall(".//Link[@Name= 'Link3']"), f"The link was not saved in the XML"
    assert iLinkN == 4, f"The index of the next link is not the expected"
    assert iCombN == 5, f"The index of the next combiner is not the expected"
    assert result_lastElement == "IconCombiner", f"The name of the combiner model is not correct"

def test_updateWESTLayoutFile(initialXML, dictForWEST,modelClasses):

    initialXMLMOD = 'tests/updateWESTLayoutFileTEST_Result.xml'

    uf.updateWESTLayoutFile(initialXML, initialXMLMOD, modelClasses, dictForWEST[0], dictForWEST[1], dictForWEST[2])

    root = ET.parse(initialXMLMOD).getroot()
    linksXML = root.find('.//Links')

    assert len(list(linksXML)) == 47, "Incorrect final number of links"
    
    checkLink(linksXML,"Link1","Icon25","Icon32","CustomOrthogonalLine1") #branch 1 starts
    checkLink(linksXML,"Link2","Icon32","Icon39","CustomOrthogonalLine2","2") 
    checkLink(linksXML,"Link3","Icon39","Icon14","CustomOrthogonalLine3") 
    checkLink(linksXML,"Link4","Icon14","Icon15","CustomOrthogonalLine4") 
    checkLink(linksXML,"Link5","Icon15","Icon16","CustomOrthogonalLine5") # branch 1 finishes
    checkLink(linksXML,"Link6","Icon16","Icon40","CustomOrthogonalLine6","1") # branch 1 to connector.

    checkLink(linksXML,"Link7","Icon17","Icon18","CustomOrthogonalLine7") #branch 2 starts
    checkLink(linksXML,"Link8","Icon18","Icon41","CustomOrthogonalLine8","1") 
    checkLink(linksXML,"Link9","Icon26","Icon33","CustomOrthogonalLine9") 
    checkLink(linksXML,"Link10","Icon33","Icon41","CustomOrthogonalLine10","2") 
    checkLink(linksXML,"Link11","Icon41","Icon19","CustomOrthogonalLine11") 
    checkLink(linksXML,"Link12","Icon19","Icon20","CustomOrthogonalLine12") 
    checkLink(linksXML,"Link13","Icon20","Icon21","CustomOrthogonalLine13") 
    checkLink(linksXML,"Link14","Icon21","Icon22","CustomOrthogonalLine14") # branch 2 finishes
    checkLink(linksXML,"Link15","Icon22","Icon42","CustomOrthogonalLine15","1") # branch 2 to connector

    checkLink(linksXML,"Link16","Icon23","Icon24","CustomOrthogonalLine16") #branch 3 starts
    checkLink(linksXML,"Link17","Icon24","Icon43","CustomOrthogonalLine17","1") 
    checkLink(linksXML,"Link18","Icon27","Icon34","CustomOrthogonalLine18") 
    checkLink(linksXML,"Link19","Icon34","Icon43","CustomOrthogonalLine19","2") # branch 3 finishes
    checkLink(linksXML,"Link20","Icon43","Icon44","CustomOrthogonalLine20","1") # branch 3 to connector

    checkLink(linksXML,"Link21","Icon28","Icon35","CustomOrthogonalLine21") # Trunk starts
    checkLink(linksXML,"Link22","Icon35","Icon45","CustomOrthogonalLine22","2") 
    checkLink(linksXML,"Link23","Icon45","Icon1","CustomOrthogonalLine23") 
    checkLink(linksXML,"Link24","Icon1","Icon2","CustomOrthogonalLine24") 
    checkLink(linksXML,"Link25","Icon2","Icon3","CustomOrthogonalLine25") 
    checkLink(linksXML,"Link26","Icon3","Icon4","CustomOrthogonalLine26") 
    checkLink(linksXML,"Link27","Icon4","Icon46","CustomOrthogonalLine27","1") 
    checkLink(linksXML,"Link28","Icon29","Icon36","CustomOrthogonalLine28") 
    checkLink(linksXML,"Link29","Icon36","Icon46","CustomOrthogonalLine29","2") 
    checkLink(linksXML,"Link30","Icon46","Icon40","CustomOrthogonalLine30","2") #connects branch
    checkLink(linksXML,"Link31","Icon40","Icon5","CustomOrthogonalLine31") 
    checkLink(linksXML,"Link32","Icon5","Icon6","CustomOrthogonalLine32") 
    checkLink(linksXML,"Link33","Icon6","Icon7","CustomOrthogonalLine33") 
    checkLink(linksXML,"Link34","Icon7","Icon8","CustomOrthogonalLine34") 
    checkLink(linksXML,"Link35","Icon8","Icon47","CustomOrthogonalLine35","1") 
    checkLink(linksXML,"Link36","Icon30","Icon37","CustomOrthogonalLine36") 
    checkLink(linksXML,"Link37","Icon37","Icon47","CustomOrthogonalLine37","2") 
    checkLink(linksXML,"Link38","Icon47","Icon9","CustomOrthogonalLine38") 
    checkLink(linksXML,"Link39","Icon9","Icon10","CustomOrthogonalLine39") 
    checkLink(linksXML,"Link40","Icon10","Icon42","CustomOrthogonalLine40","2") #connects branch
    checkLink(linksXML,"Link41","Icon42","Icon11","CustomOrthogonalLine41") 
    checkLink(linksXML,"Link42","Icon11","Icon12","CustomOrthogonalLine42") 
    checkLink(linksXML,"Link43","Icon12","Icon48","CustomOrthogonalLine43","1") 
    checkLink(linksXML,"Link44","Icon31","Icon38","CustomOrthogonalLine44")  
    checkLink(linksXML,"Link45","Icon38","Icon48","CustomOrthogonalLine45","2") 
    checkLink(linksXML,"Link46","Icon48","Icon44","CustomOrthogonalLine46","2") #connects branch
    checkLink(linksXML,"Link47","Icon44","Icon13","CustomOrthogonalLine47") # Trunk finishes