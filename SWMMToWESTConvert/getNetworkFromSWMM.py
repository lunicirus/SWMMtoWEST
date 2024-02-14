import swmmio
import os
import pandas as pd
from itertools import chain
from swmm.toolkit.shared_enum import LinkAttribute
from pyswmm import Output

import SWMMToWESTConvert.SWMM_InpConstants as SWWM_C
import SWMMToWESTConvert.SWMMtoWESTConstants as STW_C


def getsNetwork(networkFile:str)-> tuple[dict,str]:
    """
        Instanciates the network as a swmmio model and gets all the relevant elements of the network.
    Args:
        networkFile (str): path of the .inp of the network
    Returns:
        tuple[dict,str]: Dictionary with links, leaves, catchments, DWFs, timepatterns, directflows and timeseries of the network. 
        Path to the .out of the network.
    """    
    model = swmmio.Model(networkFile) # Instantiate a swmmio model object
    outfile = getSimulationResultsFile(networkFile) # gets the .out file 
    
    links = getLinksWithSlope(model)  # Links
    leaves = getNodesLeaves(model, links) # Get nodes that dont have another pipe connected upstream and are not outlets
    subCatchments = getCatchments(model) #Subcatchments
    FlowDWFs = getFlowDWFs(model)#Only flow Dry Weather Flows
    patterns = getHourlyPatterns(networkFile) #Time patterns (type dict) 
    directWaterFlows, timeS = getWaterDirectFlows(model) #Water Direct Flows and the time series related
    
    nElements = {}   
    nElements[STW_C.LINKS] = links
    nElements[STW_C.LEAVES] = leaves
    nElements[STW_C.SUBCATCHMENTS] = subCatchments
    nElements[STW_C.DWFS] = FlowDWFs
    nElements[STW_C.T_PATTERNS] = patterns 
    nElements[STW_C.DIRECTF] = directWaterFlows
    nElements[STW_C.TIMESERIES] = timeS

    return nElements, outfile

def getNodesLeaves(model:swmmio.Model, links:pd.DataFrame)->pd.Series:
    """
        Returns the leaves of the network that are not outlets. Leaves are nodes that do not have pipes connected upstream.
    Args:
        model (swmmio.Model): instanciated model of a network.
        links (pd.DataFrame): links of the entire network. Index is the link name and columns are their attributes.
    Returns:
        pd.Series: names of the node leaves of the network
    """   
    outNodes = links[SWWM_C.OUT_NODE].drop_duplicates()  #Get outlet nodes of pipes and cathments
    inNodes = links[SWWM_C.IN_NODE].drop_duplicates()  #Get inlet nodes of pipes and cathments
    nodes = model.nodes().index.to_series() #all nodes

    startPoints = nodes[~nodes.isin(outNodes.tolist())] #Get only nodes that are not outlets 

    SPCleaned = startPoints[startPoints.isin(inNodes.tolist())] #Removes nodes that are not connected to the network
    
    print("Number of nodes ", nodes.shape[0],", outlets ", outNodes.shape[0], ", startPoints ",startPoints.shape[0], ", and after cleaned ",SPCleaned.shape[0])

    return SPCleaned

def getWaterDirectFlows(model:swmmio.Model)->tuple[pd.DataFrame,pd.DataFrame]:
    """
        Returns the direct flows with type and constituent = FLOW and the time series related. Cannot handle direct inflows with a baseline pattern.
    Args:
        model (swmmio.Model): instanciated model of a network.
    Returns:
        tuple[pd.DataFrame,pd.DataFrame]: flow direct flows with discharging node as index and time series name, sfactor, and baseline as columns.
        time series of the direct flows with rows as the name of the time series, and columns date, time, and value.
    """    
    directFlows = model.inp.inflows #can't handle direct inflows with a baseline pattern !!! 
    directWaterFlows = directFlows[(directFlows[SWWM_C.DFLOW_CONSTITUENT]==SWWM_C.FLOW)&(directFlows[SWWM_C.TYPE]==SWWM_C.FLOW)].drop(
                                    columns=[SWWM_C.DFLOW_CONSTITUENT,SWWM_C.TYPE,SWWM_C.DFLOW_MFACTOR])
    
    print("There were", directFlows.shape[0] - directWaterFlows.shape[0], "DFs with other constituents than FLOW")

    timeSeriesNames = directWaterFlows[SWWM_C.DFLOW_TIMES].dropna().unique().tolist()
    timeSeries = model.inp.timeseries.loc[timeSeriesNames]
    
    return directWaterFlows, timeSeries

def getFlowDWFs(model:swmmio.Model)->pd.DataFrame:
    """
        Returns the dry weather flows with inflow type = FLOW of the model. 
    Args:
        model (swmmio.Model): instanciated model of a network.
    Returns:
        pd.DataFrame: flow DWFs with mean value and pattern name.
    """    
    dwfs = model.inp.dwf[[SWWM_C.INFLOW_TYPE,SWWM_C.INFLOW_MEAN,SWWM_C.INFLOW_PATTERNS]].copy()    
    dwfsWater = dwfs[dwfs[SWWM_C.INFLOW_TYPE]==SWWM_C.FLOW].drop(columns=[SWWM_C.INFLOW_TYPE]).copy()

    print("There were", dwfs.shape[0] - dwfsWater.shape[0], "DWFs with inflow type different than FLOW")
    return dwfsWater

def getCatchments(model:swmmio.Model)->pd.DataFrame:
    """
        Returns the catchments of the model with their discharge node and area. Discards catchments with area zero.
    Args:
        model (swmmio.Model): instanciated model of a network.
    Returns:
        pd.DataFrame: containing all valid catchments.
    """
    catchments = model.subcatchments()[[SWWM_C.CATCH_OUT,SWWM_C.AREA]]
    validCatchments = catchments[catchments[SWWM_C.AREA]>0]

    print("There were", catchments.shape[0] - validCatchments.shape[0], "subcatchments with area 0")
    return validCatchments

def getSimulationResultsFile(networkFile:str)-> str:
    """
        Looks for the simulation results file of the inp file passed as parameter
    Args:
        networkFile (str): path of the inp of the network

    Raises:
        FileNotFoundError: if there is no simulation results file with the same name as the inp

    Returns:
        str: path of the simulation results file 
    """    

    fileName, extension = os.path.splitext(networkFile)
    outfile = f"{fileName}.out"
    if not os.path.exists(outfile):
        raise FileNotFoundError(f"Output file '{outfile}' does not exist. Please run a simulation in SWMM before.")
    return outfile

def getsNetworksLinks(inpPath:str)-> pd.DataFrame:
    """
        Gets the links of the network (includes pumps, orifices, pipes..) 
    Args:
        inpPath (str): path of the inp of the network
    Returns:
        pd.DataFrame: links of the network
    """    

    # Instantiate a swmmio model object
    model = swmmio.Model(inpPath)
    
    #DONT USE CONDUITS, they are more but dont have all the links (bug of the library, or inp?)
    links = model.links()[[SWWM_C.IN_NODE,SWWM_C.OUT_NODE,SWWM_C.LEN,SWWM_C.DIAM,
                           SWWM_C.MAX_Q,SWWM_C.ROUG,SWWM_C.SHAPE]].copy()
    
    return links

def getLinksWithSlope(model:swmmio.Model)->pd.DataFrame:
    """
        Returns the links of the model with inNode, outNode, length, Geom1, Qmax, roughness,shape, and slope
        Assumes that the model has OPTION IN THE INP = ELEVATION to calculate the slope.
    Args:
        model (swmmio.Model): instanciated model of a network 
    Returns:
        pd.Dataframe: containing all the links 
    """    
    assert model.inp.options.loc['LINK_OFFSETS'].iloc[0] == SWWM_C.ELEVATION #check that the network uses elevation
    
    links = model.links()[[SWWM_C.IN_NODE,SWWM_C.OUT_NODE,SWWM_C.LEN,SWWM_C.DIAM,
                           SWWM_C.MAX_Q,SWWM_C.ROUG,SWWM_C.INOFF,SWWM_C.OUTOFF,SWWM_C.SHAPE]].copy() #gets the links of the network
    links[STW_C.SLOPE] = (links[SWWM_C.INOFF]-links[SWWM_C.OUTOFF])/links[SWWM_C.LEN] #calculates the slope

    links.drop(columns=[SWWM_C.INOFF,SWWM_C.OUTOFF],inplace=True)

    return links

def getHourlyPatterns(networkFile:str)-> dict:
    """
        Returns the hourly patters of the network. Only works if there are no patterns different from hourly in the inp.
    Args:
        networkFile (str): path of the .inp of the network
    Returns:
        dict: with the name of the pattern as key and the values as a list
    """    
    patternsRaw = swmmio.utils.dataframes.dataframe_from_inp(networkFile,'PATTERNS') #Gets the section from the inp
    
    hourlyPatternsNames = patternsRaw[SWWM_C.PATTERNS].str.extract(r'^(.*?)\sHOURLY').iloc[:,0].unique() #Gets the names of the patterns
    hPatterns = [value.strip() for value in hourlyPatternsNames if isinstance(value, str)]

    patternsRaw[SWWM_C.PATTERNS] = patternsRaw[SWWM_C.PATTERNS].str.replace(r'\sHOURLY\b', '', regex=True).str.strip()#Removes the HOURLY word
    hourlyPatterns = patternsRaw[SWWM_C.PATTERNS].str.split(r'\s+', expand=True).set_index(0) #Expands the values in different columns
    
    #Creates the dicitonary
    patterns = {}
    for hp in hPatterns:
        df = hourlyPatterns.loc[hp] #selects all the rows refering to the pattern
        vals = list(chain.from_iterable(df.values.tolist())) #it flattens the values on a list
        patterns[hp] = vals
    
    return patterns

def getFlowTimeSeries(pipes:list[str], fileOut:str)-> pd.DataFrame:
    """
        Gets the flow time series of a list of pipes using their name as key.
    Args:
        pipes (list[str]): names of the pipes for which to obtain the flow results
        fileOut (str): path of the .out of the network

    Returns:
        pd.DataFrame: time as index and columns are the names of the pipes 
    """    
    tsDF = None

    for p in pipes:

        #Gets the timeseries of the flow from the connections to the path and the pipe before the discharge
        with Output(fileOut) as out:
            tsEval = out.link_series(p, LinkAttribute.FLOW_RATE) # time series as dictionary with time as key
       
            #Convert the dictionaries into dataframes
            dfEval = pd.DataFrame.from_dict(tsEval, orient='index',columns=[p]) # dataframe of the time series 

            if tsDF is None:
                tsDF = dfEval
            else:
                tsDF = tsDF.join(dfEval)

    return tsDF
        