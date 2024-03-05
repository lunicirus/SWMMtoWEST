import pandas as pd
import pytest

from SWMMToWESTConvert import aggregateNetwork as an
from SWMMToWESTConvert import getNetworkFromSWMM as gnfs

# Sample data for testing
# You may need to adjust these sample data according to your actual data structure
sample_idWRRF = "RA_606859"
sample_outfile = "tests/DWF2022_TEST.out"
sample_inpfile = "tests/DWF2022_TEST.inp"

sample_links = gnfs.getsNetworksLinks(sample_inpfile)
sample_idTrunkIni = "R007637"


def test_findTrunk_with_known_start_point():
    # Call the function with known start point
    result = an.findTrunk(sample_idWRRF, sample_outfile, sample_links, idTrunkIni=sample_idTrunkIni)

    # Define the expected result based on your test data
    # Adjust this according to your test case
    expected_result = pd.DataFrame(...) #TODO

    # Assert that the result matches the expected result
    pd.testing.assert_frame_equal(result, expected_result)

def test_findTrunk_with_unknown_start_point():
    # Call the function with unknown start point
    result = an.findTrunk(sample_idWRRF, sample_outfile, sample_links)

    # Define the expected result based on your test data
    # Adjust this according to your test case
    expected_result = pd.DataFrame(...) #TODO

    # Assert that the result matches the expected result
    pd.testing.assert_frame_equal(result, expected_result)


#TODO check and run these tests
def test_min_index_exists():
    # Test when a minimum index exists in breaklinksIndexPath
    pathWithLookPoints = pd.DataFrame({'col1': [1, 2, 3]}, index=[0, 2, 4])
    breaklinksIndexPath = [1, 3]
    expected_result = pd.Series([1, 3, 4], index=[0, 2, 4])
    assert (an.setAggregationNodes(pathWithLookPoints, breaklinksIndexPath) == expected_result).all()

def test_min_index_does_not_exist():
    # Test when no minimum index exists in breaklinksIndexPath
    pathWithLookPoints = pd.DataFrame({'col1': [1, 2, 3]}, index=[0, 2, 4])
    breaklinksIndexPath = [5, 6]
    expected_result = pd.Series([4, 4, 4], index=[0, 2, 4])
    assert (an.setAggregationNodes(pathWithLookPoints, breaklinksIndexPath) == expected_result).all()

def test_empty_breaklinksIndexPath():
    # Test when breaklinksIndexPath is empty
    pathWithLookPoints = pd.DataFrame({'col1': [1, 2, 3]}, index=[0, 2, 4])
    breaklinksIndexPath = []
    expected_result = pd.Series([4, 4, 4], index=[0, 2, 4])
    assert (an.setAggregationNodes(pathWithLookPoints, breaklinksIndexPath) == expected_result).all()