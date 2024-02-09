import pytest
import swmmio
import pandas as pd

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
    
    # Check if the columns are present in the result
    expected_columns = [SWWM_C.IN_NODE,SWWM_C.OUT_NODE,SWWM_C.LEN,SWWM_C.DIAM,SWWM_C.MAX_Q,SWWM_C.ROUG,SWWM_C.SHAPE,STW_C.SLOPE]
    assert result.columns.tolist() == expected_columns
    
    # Check if the slope is calculated correctly
    #expected_slope = [(200 - 100) / 100, (250 - 150) / 150] #TODO!!
    #assert result['slope'].tolist() == expected_slope
    
    # Check if columns SWWM_C.INOFF and SWWM_C.OUTOFF are dropped
    assert SWWM_C.INOFF not in result.columns
    assert SWWM_C.OUTOFF not in result.columns