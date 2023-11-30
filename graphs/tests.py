import pandas as pd
import pytest

import processData as prd

# Pytest fixture to create a sample DataFrame
@pytest.fixture
def sample_dataframe():
    data = {'.Sew_1.Q_In': [1, 2, 3],
            '.Sew_4.Q_Out': [4, 5, 6],
            '.Sew_16.Q_Out': [7, 8, 9],
            '.Sew_19.Q_Out': [10, 11, 12],
            '.Sew_1.Q_Out': [13, 14, 15],  # Same number (1) but different word part
            '.Sew_4.Q_In': [16, 17, 18],   # Same number (4) but different word part
            '.Sew_19.Q_In': [19, 20, 21]   # Same number (19) but different word part
            }
    return pd.DataFrame(data)

# Pytest test case for renaming columns
def test_rename_columns(sample_dataframe):
    df_renamed = prd.renameWEST(sample_dataframe)

    # Verify that the columns are renamed as expected
    expected_columns = ['1 (In)', '4 (Out)', '16 (Out)', '19 (Out)', '1 (Out)', '4 (In)','19 (In)']
    assert list(df_renamed.columns) == expected_columns

# Pytest test case for sorting columns
def test_sort_columns_by_number(sample_dataframe):

    df_renamed = prd.renameWEST(sample_dataframe)
    df_sorted = prd.sortColumnsWEST(df_renamed)

    # Verify that the columns are sorted as expected
    expected_columns = ['1 (In)', '1 (Out)', '4 (In)', '4 (Out)', '16 (Out)', '19 (In)', '19 (Out)']
    assert list(df_sorted.columns) == expected_columns
