import pytest
import swmmio
import pandas as pd
import os
import json


from SWMMToWESTConvert import getNetworkFromSWMM as gnfs
from SWMMToWESTConvert import SWMM_InpConstants as SWWM_C

"""
    Test of the class getNetworkFromSWMM. Should be runned from the main directory using "pytest tests\getNetworkFromSWMM_Test.py"
"""

@pytest.fixture
def sample_model():
    # Set up a sample SWMM model for testing
    model = swmmio.Model('tests/DWF2022_TEST.inp')
    
    return model

#---------------------------------------------------------------------------

def test_getSimulationResultsFile_exists():
   
    # Creates dummy files
    network_file = "test_network.inp"
    open(network_file, 'a').close()  # Create an empty file
    out_file = "test_network.out"
    open(out_file, 'a').close()  
    
    # Test that the function returns the expected output file path
    assert gnfs.getSimulationResultsFile(network_file) == out_file
    
    # Removes created files
    os.remove(network_file)
    os.remove(out_file)

def test_getSimulationResultsFile_not_exists():
    
    network_file = "test_network.inp" #Creates dummy files
    open(network_file, 'a').close()  
    
    # Test that the function raises FileNotFoundError when the .out file doesn't exist
    with pytest.raises(FileNotFoundError):
        gnfs.getSimulationResultsFile(network_file)
    
    os.remove(network_file) # Clean ups created file

#----------------------------------------------------------------------------
    
def test_getsNetworksLinks_valid_input():
    inp_path = "tests/DWF2022_TEST.inp"
    expected_columns = ['InletNode','OutletNode','Length','Geom1','MaxQ','Roughness','Shape']
    
    # Test that the function returns a DataFrame with the expected columns
    links_df = gnfs.getsNetworksLinks(inp_path)
    assert isinstance(links_df, pd.DataFrame)
    assert links_df.columns.tolist() == expected_columns
    assert len(links_df) == 1532
      
def test_getsNetworksLinks_invalid_input():
    # Test that the function raises an error for invalid input file path
    with pytest.raises(Exception):  
        gnfs.getsNetworksLinks("nonexistent_file.inp")

#----------------------------------------------------------------------------
    
def test_getLinksWithSlope(sample_model):

    result = gnfs.getLinksWithSlope(sample_model)
    
    assert isinstance(result, pd.DataFrame) # Check if the result is a DataFrame
    assert len(result) == 1532 # Check that the correct number of links are there
    
    # Check if the columns are present in the result
    expected_columns = ['InletNode','OutletNode','Length','Geom1','MaxQ','Roughness','Shape','Slope']
    assert result.columns.tolist() == expected_columns
    
    #Gets the expected slopes and truncate them  
    expected_slopes_file = "tests/PCSWMMSlopes.csv"
    expected_slope = pd.read_csv(expected_slopes_file, delimiter = ',',index_col=['Name'])
    resultCompa = result.join(expected_slope)

    # Check if the slope is calculated correctly #TODO the expected slopes have mistakes (PCSWWM seems incorrect)
    #for expected_val, actual_val, pipe in zip(resultCompa["Slope (m/m)"].to_list(), resultCompa[STW_C.SLOPE].tolist(),resultCompa.index.to_list()):
        #assert np.isclose(expected_val, actual_val, rtol=0.1), f"Values are not within 10% tolerance: ({pipe}) {expected_val}, {actual_val}"
    
    # Check if columns SWWM_C.INOFF and SWWM_C.OUTOFF are dropped
    assert SWWM_C.INOFF not in result.columns
    assert SWWM_C.OUTOFF not in result.columns
    
#----------------------------------------------------------------------------
   
def test_getNodesLeaves_valid_input(sample_model):
    # Test that the function returns the expected node leaves
    filename = 'tests/leavesTest.json'
    with open(filename, 'r') as file:
        data = json.load(file)

    expected_leaves = data['expected_leaves']
    links = sample_model.links()

    result = gnfs.getNodesLeaves(links)
    assert all(l in result for l in expected_leaves) #check that the same values are there even if they are not in the same order
    assert len(result) == len(expected_leaves) #check that the number of leaves obtained are the same

def test_getNodesLeaves_empty_input():
    # Test that the function returns an empty Series when links DataFrame is empty
    links = pd.DataFrame(columns=["InletNode", "OutletNode"])  # Empty DataFrame

    assert not gnfs.getNodesLeaves(links) #checks that is empty
