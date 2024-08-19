
import pandas as pd
import meassuresConstants as MC
import PCSWMMConstants as PSC 
import graphConstants as GC
import WESTConstants as WC
import re 

 
def processMeassuredData(filePath:str, colsInLps:list[str], colsInm3h:list[str])->pd.DataFrame:
    """
        Converts a csv file of measurements into a dataframe, with index the datetime and columns represent a location. 
        The file should have a column named MC.INDEX_COL which will be used as index. 
        Only columns with names in colsInLps or colsInm3h would be used.
    Args:
        filePath (str): Path to the file with the timeseries of values meassured in the field.
        colsInLps (list[str]): Names of the columns which values are in lps.
        colsInm3h (list[str]): Names of the columns which values are in m3/h.
    Returns:
        pd.DataFrame: Clean dataframe with values in m3/h.
    """    
    try:
        flowVals = pd.read_csv(filePath, delimiter = ',',index_col=[MC.INDEX_COL])
    except ValueError as e:
        raise  ValueError("The column '" + MC.INDEX_COL + "' does not exist in the CSV file. Please check the column name as this is used as index.") from e

    flowVals.index = pd.to_datetime(flowVals.index, format='%d/%m/%y %H:%M') #converts the index values to datetime
    flowVals= flowVals.apply(pd.to_numeric, errors='coerce') #convert string values to numeric replace invalid values as null

    #transformation of the units and renaming the columns
    dfLs = flowVals[colsInLps].copy()
    dfFlowsLsTom3h= dfLs*3.6
    dfFlowsLsTom3h.columns = dfFlowsLsTom3h.columns.str.replace('l/s', 'm³/h')

    #joining dataframes to create the original complete dataframe
    dfFlowsm3h = flowVals[colsInm3h].copy()
    dfFlowsm3h = dfFlowsm3h.join(dfFlowsLsTom3h).copy()

    #checks that the join was properly done
    assert dfFlowsm3h.shape[0] == flowVals.shape[0]
    assert dfFlowsm3h.shape[1] == flowVals.shape[1]

    #Cleaning error values
    dfFlowsm3h[dfFlowsm3h < 0] = 0 #replace negative values with 0

    return dfFlowsm3h

def processSWMMOutFlowData(filePath:str, startDate:'Timestamp', endDate:'Timestamp', renameDict:dict[str,str]=None)->pd.DataFrame:
    """
        Converts a csv file with flow values from SWMM into a dataframe with values within the evaluation time period. 
    Args:
        filePath (str): Path to the file with the timeseries of flow values in m3/s (CMS) from SWMM.
        startDate (Timestamp): Start date of the evaluation period (inclusive). 
        endDate (Timestamp): End date of the evaluation period (exclusive).
        renameDict (dict[str,str], optional): Names of the columns as keys and the new column names as values. Defaults to None.
    Returns:
        pd.DataFrame: Clean dataframe with values in m3/h.
    """    
    flowModelVals = pd.read_csv(filePath, delimiter = ',')
    flowModelVals.columns = flowModelVals.columns.str.replace(' ', '') #Remove white spaces from columns names
    
    #Creates the datetime values to be the index----------------------
    try:
        flowModelVals[GC.LONGDATE_LBL] = flowModelVals[PSC.DATE_LBL] + " " + flowModelVals[PSC.TIME_LBL] #concat date and time columns
    except KeyError as e:
        raise  KeyError("The columns '" + PSC.DATE_LBL + "' and '" + PSC.TIME_LBL + "' do not exist in the CSV file. Please check the column names as these are used as index.") from e
    
    flowModelVals.drop(columns=[PSC.DATE_LBL, PSC.TIME_LBL],inplace=True) #removes redundant columns
    flowModelVals[GC.LONGDATE_LBL]= pd.to_datetime(flowModelVals[GC.LONGDATE_LBL],format='%m/%d/%Y %H:%M:%S') # formats date
    flowModelVals.set_index(GC.LONGDATE_LBL,inplace=True)
    #-------------------------------------------------------------------

    flowModelValsm3h = flowModelVals*3600 # convert values to m3/h
    flowModelValsm3h = flowModelValsm3h[(flowModelValsm3h.index >= startDate)&(flowModelValsm3h.index < endDate)] # Removes values outside the evaluated period

    if renameDict is not None:
        flowModelValsm3h.rename(columns=renameDict,inplace=True)
    
    return flowModelValsm3h

def computeTotalTSSFromWell(df:pd.DataFrame)->pd.DataFrame:
    """
        Calculates the TSS values of a Well adding all the classes and dividing by the H2O.
    Args:
        df (pd.DataFrame): Values of TSS by classes (e.g. from 0 to 9) and H20 for various inputs or outputs.
    Returns:
        pd.DataFrame: TSS values in g/m3.
    """    
    dfTSSComputed = pd.DataFrame()
    DENSITY_H2O_G = 1000000

    wellsData = set(col.split('(')[0] for col in df.columns)
    for wellData in wellsData:
                
        wellDataCols = [col for col in df.columns if col.startswith(wellData+"(TSS")] # Filter columns related to the current well and flow type

        name = re.sub(r"\.Well_(\d+)\.(\w+)flow(\w*)", r"Well \1 (\2\3)", wellData)

        # Sum the values across the TSS columns (g/d), divide by H2O (g/d) and adjust units to g/m3
        dfTSSComputed[f"{name}"] = df[wellDataCols].sum(axis=1)/df[f"{wellData}(H2O)"]*DENSITY_H2O_G 

    return dfTSSComputed
        

def getDFWESTResults(filePath:str, startDate:'Timestamp', endDate:'Timestamp', dictRenames:dict[str,str]=None)->tuple[pd.DataFrame, pd.DataFrame]:
    """
        Converts a csv file with flow values from WEST into a dataframe with values within evaluation time period.
    Args:
        filePath (str): Path to the csv file (using , as separator) with the timeseries of flow values in m3/d from WEST and time in days.
        startDate (Timestamp): Start date of the evaluation period (inclusive). 
        endDate (Timestamp): End date of the evaluation period (exclusive).
        renameDict (dict[str,str], optional): Names of the columns as keys and the new column names as values. Defaults to None.
    Returns:
        tuple[pd.DataFrame,pd.DataFrame]: Clean flow dataframe with values in m3/h. Clean dataframe with values in g/m3.
    """    
    WTP_WEST_Results = pd.read_csv(filePath, delimiter = ',')
    units = WTP_WEST_Results.iloc[0]
    WTP_WEST_Results.drop(WTP_WEST_Results.index[0],inplace=True) #drops the row with units
    WTP_WEST_Results = WTP_WEST_Results.apply(pd.to_numeric, errors='coerce')

    #Calculates the dates to be used as index
    WTP_WEST_Results[WC.TIME_WEST] = WTP_WEST_Results[WC.TIME_WEST]-WTP_WEST_Results[WC.TIME_WEST].min() #In case the simulation in WEST was not started in day 0, it shifts the whole dataset to start at 0
    WTP_WEST_Results[WC.TIME_WEST] = pd.to_timedelta(WTP_WEST_Results[WC.TIME_WEST], unit='D') # Converts the "Days" column to timedelta objects (days) 
    WTP_WEST_Results[GC.DATE_LBL] = startDate + WTP_WEST_Results[WC.TIME_WEST]  # Calculates the date base on the starting date 
    
    #Removes extra records and set the index
    WTP_WEST_ResultsCut= WTP_WEST_Results[WTP_WEST_Results[GC.DATE_LBL] < endDate] # rows if they are outside the date range being evaluated 
    WTP_WEST_ResultsCut = WTP_WEST_ResultsCut.drop(columns=[WC.TIME_WEST]).set_index(GC.DATE_LBL) #Removes unnecesary columns and set the index
    
    #Separating flow from TSS
    dfFlow = WTP_WEST_ResultsCut.loc[:, units == WC.UNITS_FLOW]
    dfTSS = WTP_WEST_ResultsCut.loc[:, units == WC.UNITS_TSS]

    #Formating, change the data units and column names
    dfFlow = dfFlow /24 # from m3/d to m3/h
    dfFlow = renameWEST(dfFlow.copy()) #Renames columns for the graph
    dfTSS = renameWEST(dfTSS.copy(),False) #Renames columns for the graph
   
    #Obtaining TSS from Wells models
    dfTSSWell = WTP_WEST_ResultsCut.loc[:, units == WC.UNITS_TSS_WELL]
    dfTSS = dfTSS.join(computeTotalTSSFromWell(dfTSSWell))

    return dfFlow, dfTSS

def renameWEST(dfWEST:pd.DataFrame, isFlow:bool=True, dictRenames:dict[str,str]=None)->pd.DataFrame:
    """
        Renames the columns of a dataframe. In the case of no dictRenamesor, all the columns are renamed, otherwise
        as many columns as found in the dictionary.
    Args:
        dfWEST (pd.DataFrame): Dataframe with columns using the format of WEST (e.g., '.Element.Q_In' or '.Element.Q_Out')
        dictRenames (dict[str,str], optional): Names of the columns as keys and the new column names as values. Defaults to None.
        isFlow (bool, optional): True if the dataframe contains flow values, otherwise False.
    Returns:
        pd.DataFrame: The dfWEST with the columns renamed.
    """    
    if dictRenames is None:
        if isFlow:
            dfWEST.columns = dfWEST.columns.str.extract(r'\.\w+_(\d+)\.Q_(\w+)').apply(lambda x: f'{x[0]} ({x[1]})', axis=1)
        else:
            dfWEST.columns = dfWEST.columns.str.extract(r'\.\w+_(\d+)\.TSS_(\w+)').apply(lambda x: f'{x[0]} ({x[1]})', axis=1)
    else:
        dfWEST.rename(columns=dictRenames,inplace=True)

    return dfWEST

def sortColumnsWEST(dfWEST:pd.DataFrame)->pd.DataFrame:
    """
        Sorts a dataframe by the index in the name of the columns. 
        Columns are assumed to have the format "index (direction)"
    Args:
        dfWEST (pd.DataFrame): Dataframe to be sorted.
    Returns:
        pd.DataFrame: Sorted dataframe with columns ascending by the index inside the name of the columns 
    """    
    sorted_columns = sorted(dfWEST.columns, key=lambda x: (int(x.split()[0]), x.split()[1]))

    dfWEST = dfWEST[sorted_columns]

    return dfWEST

def checkAverageColumnsIncrements(df:pd.DataFrame)->bool:
    """
        Evaluate if the mean value of each of the columns increases with the index of the column.
    Args:
        df (pd.DataFrame): Dataframe to evaluate.
    Returns:
        bool: True if the mean value increases with the index of the column.
    """
    num_columns = df.shape[1]

    for column_index in range(1, num_columns):

        current_mean = df.iloc[:, column_index].mean()
        previous_mean = df.iloc[:, column_index - 1].mean()

        if (not current_mean > previous_mean) and ((previous_mean-current_mean)*100/previous_mean > 0.5):
            print("The column with error is: ",column_index)
            return False

    return True

def checkCorrectFlowWEST(df:pd.DataFrame)->tuple[bool,pd.DataFrame]:
    """
        Sorts the columns by the index of their name and evaluates if the flow increases with it.
    Args:
        df (pd.DataFrame): Dataframe to evaluate.
    Returns:
        bool: True if the mean value increases with the index of the column.
    """    
    df = sortColumnsWEST(df)
    df = df.iloc[20:,:] #remove the first data points as this period is assumed to be unstable

    return checkAverageColumnsIncrements(df), df

    

    