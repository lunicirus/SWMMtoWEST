import pytest
import swmmio
import pandas as pd
import numpy as np

from SWMMToWESTConvert import getNetworkFromSWMM as gnfs
from SWMMToWESTConvert import SWMM_InpConstants as SWWM_C
from SWMMToWESTConvert import SWMMtoWESTConstants as STW_C

"""
    Test of the class getNetworkFromSWMM. Should be runned from the main directory using "pytest tests\getNetworkFromSWMM_Test.py"
"""

@pytest.fixture
def sample_model():
    # Set up a sample SWMM model for testing
    model = swmmio.Model('tests/DWF2022_TEST.inp')
    
    return model

def test_getLinksWithSlope(sample_model):

    # Call the function
    result = gnfs.getLinksWithSlope(sample_model)
    
    # Check if the result is a DataFrame
    assert isinstance(result, pd.DataFrame)

    # Check that the correct number of links are there
    assert len(result) == 1532
    
    # Check if the columns are present in the result
    expected_columns = [SWWM_C.IN_NODE,SWWM_C.OUT_NODE,SWWM_C.LEN,SWWM_C.DIAM,SWWM_C.MAX_Q,SWWM_C.ROUG,SWWM_C.SHAPE,STW_C.SLOPE]
    assert result.columns.tolist() == expected_columns
    
    #Gets the expected slopes and truncate them 
    expected_slopes_file = "tests/PCSWMMSlopes.csv"
    expected_slope = pd.read_csv(expected_slopes_file, delimiter = ',',index_col=['Name'])
    resultCompa = result.join(expected_slope)

    # Check if the slope is calculated correctly
    for expected_val, actual_val, pipe in zip(resultCompa["Slope (m/m)"].to_list(), resultCompa[STW_C.SLOPE].tolist(),resultCompa.index.to_list()):
        assert np.isclose(expected_val, actual_val, rtol=0.1), f"Values are not within 10% tolerance: ({pipe}) {expected_val}, {actual_val}"
    
    # Check if columns SWWM_C.INOFF and SWWM_C.OUTOFF are dropped
    assert SWWM_C.INOFF not in result.columns
    assert SWWM_C.OUTOFF not in result.columns