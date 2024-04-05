import pytest
import xml.etree.ElementTree as ET

from SWMMToWESTConvert import updateWESTfiles as uf


def test_connectCatchment():

    #Gets the test data
    tree = ET.parse('tests/xmlTEST.xml')
    root = tree.getroot()  
    linksXML = root.find('.//Links')

    catchmentNames = {"LinkName": "linkCatch1", "ElementName": "Catchment1", "ConnectionName": "connCatch1"}
    connectorNames = {"LinkName": "linkConn1", "ElementName": "Connection1", "ConnectionName": "connConn1"}
    combNames = {"LinkName": "linkComb1", "ElementName": "Combiner1", "ConnectionName": "connComb1"}
    prevElement = "Sewer1"

    result = uf.createCatchmentLinksXML(linksXML, catchmentNames, connectorNames, combNames, prevElement)

    ET.indent(tree, space="\t", level=0)
    tree.write('tests/xmlTEST_Mod.xml')

    assert isinstance(result, ET.Element) 
    assert len(list(result)) == 5  # Ensure that three links were appended to the linksXML element

    #Check the values of the link between the combiner and the next element-----------------------------------------------------
    linkC = result.find(".//Link[@Name='linkCatch1']")
    assert linkC is not None # Assert that the link element with name "linkCatch1" exists
    assert linkC.find(".Props/Prop[@Name='From'][@Value='sub_models.Sewer1.interface.Outflow']") is not None # Assert that the "prop" element with name "From" and value "Catchment1" exists inside the props element
    assert linkC.find(".Props/Prop[@Name='To'][@Value='sub_models.Catchment1.interface.Inflow']") is not None 
    assert linkC.find(".Props/Prop[@Name='Type'][@Value='Connect']") is not None 
    assert linkC.find(".Props/Prop[@Name='Data'][@Value='ConnectionName=&quot;connCatch1&quot; ConnectionType=&quot;WaterLine&quot;']") is not None 
    
    #Check the values of the link between catchment and the connection-----------------------------------------------------
    checkCatchConnCombLinks(result) 

def checkCatchConnCombLinks(result):

    linkC = result.find(".//Link[@Name='linkConn1']")
    assert linkC is not None # Assert that the link element with name "linkConn1" exists   
    assert linkC.find(".Props/Prop[@Name='From'][@Value='sub_models.Catchment1.interface.Outflow']") is not None # Assert that the "prop" element with name "From" and value "Catchment1" exists inside the props element
    assert linkC.find(".Props/Prop[@Name='To'][@Value='sub_models.Connection1.interface.Inflow']") is not None 
    assert linkC.find(".Props/Prop[@Name='Type'][@Value='Connect']") is not None 
    assert linkC.find(".Props/Prop[@Name='Data'][@Value='ConnectionName=&quot;connConn1&quot; ConnectionType=&quot;WaterLine&quot;']") is not None 

    #Check the values of the link between connection and the combiner-----------------------------------------------------
    linkC = result.find(".//Link[@Name='linkComb1']")
    assert linkC is not None # Assert that the link element with name "linkComb1" exists
    assert linkC.find(".Props/Prop[@Name='From'][@Value='sub_models.Connection1.interface.Outflow']") is not None # Assert that the "prop" element with name "From" and value "Catchment1" exists inside the props element
    assert linkC.find(".Props/Prop[@Name='To'][@Value='sub_models.Combiner1.interface.Inflow']") is not None 
    assert linkC.find(".Props/Prop[@Name='Type'][@Value='Connect']") is not None 
    assert linkC.find(".Props/Prop[@Name='Data'][@Value='ConnectionName=&quot;connComb1&quot; ConnectionType=&quot;WaterLine&quot;']") is not None
    
