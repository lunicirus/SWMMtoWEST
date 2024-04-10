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
def names_Dict():

    namesDict = {"Sew_1": "Icon00008", "Sew_2": "Icon1","Sew_3": "Icon3", "Catchment_2": "Icon2",
                 "Catchment_1":"Icon22","Connector_info_1":"Icon23","Well_1":"Two_combiner"}
    
    return namesDict

def checkLink(xml,linkName,fromM,toM,connName):

    linkC = xml.find(".//Link[@Name='"+ linkName +"']")
    assert linkC is not None # Assert that the link element with name <<linkName>> exists
    assert linkC.find(".Props/Prop[@Name='From'][@Value='sub_models."+ fromM +".interface.Outflow']") is not None # Assert that the "prop" element with name "From" and value "Catchment1" exists inside the props element
    assert linkC.find(".Props/Prop[@Name='To'][@Value='sub_models."+ toM +".interface.Inflow']") is not None 
    assert linkC.find(".Props/Prop[@Name='Type'][@Value='Connect']") is not None 
    assert linkC.find(".Props/Prop[@Name='Data'][@Value='ConnectionName=&quot;"+ connName +"&quot; ConnectionType=&quot;WaterLine&quot;']") is not None 
    

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
    assert len(list(result)) == 5  # Ensure that three links were appended to the linksXML element

    #Check the values of the link between the previous element and the catchment -----------------------------------------------------
    checkLink(result, catchmentNames["LinkName"], prevElement, catchmentNames["ElementName"], catchmentNames["ConnectionName"])
    #Check the values of the link between catchment and the connection-----------------------------------------------------
    checkLink(result, connectorNames["LinkName"], catchmentNames["ElementName"],connectorNames["ElementName"], connectorNames["ConnectionName"])
    #Check the values of the link between connection and the combiner-----------------------------------------------------
    checkLink(result, combNames["LinkName"], connectorNames["ElementName"], combNames["ElementName"], combNames["ConnectionName"])
    
  #TODO add other cases!!


def test_connectPipeSection_with_lastElement_none(sample_Links,names_Dict):

    linksXML = sample_Links[0]
    tree = sample_Links[1]
    linki = 3
    lastElement = None
    tanksIndexes = [1, 2, 3]

    # Call the function
    result_linksXML, result_linki, result_lastElement = uf.connectPipeSection(names_Dict, linksXML, linki, lastElement, tanksIndexes)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')
    
    assert result_linki == 5 # Expected updated index for the next link
    assert len(list(result_linksXML)) == 4  # Ensure that two links were appended to the linksXML element
    assert result_lastElement == "Icon3" # Expected updated name of the last element connected

    checkLink(result_linksXML,"Link3","Icon00008","Icon1","CustomOrthogonalLine3")
    checkLink(result_linksXML,"Link4","Icon1","Icon3","CustomOrthogonalLine4")

def test_connectPipeSection(sample_Links,names_Dict):

    linksXML = sample_Links[0]
    tree = sample_Links[1]
    linki = 3
    lastElement = "Icon22"
    tanksIndexes = [1, 2, 3]

    # Call the function
    result_linksXML, result_linki, result_lastElement = uf.connectPipeSection(names_Dict, linksXML, linki, lastElement, tanksIndexes)

    #ET.indent(tree, space="\t", level=0)
    #tree.write('tests/xmlTEST_Mod1.xml')
    
    assert result_linki == 6 # Expected updated index for the next link
    assert len(list(result_linksXML)) == 5  # Ensure that two links were appended to the linksXML element
    assert result_lastElement == "Icon3" # Expected updated name of the last element connected

    checkLink(result_linksXML,"Link3","Icon22","Icon00008","CustomOrthogonalLine3")
    checkLink(result_linksXML,"Link4","Icon00008","Icon1","CustomOrthogonalLine4")
    checkLink(result_linksXML,"Link5","Icon1","Icon3","CustomOrthogonalLine5")


