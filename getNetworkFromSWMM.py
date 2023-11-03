import swmmio
import os
from itertools import chain

import SWMM_InpConstants as SWWM_C
import SWMMtoWESTConstants as STW_C


#ONLY WORKS IF THERE ARE NOT PATTERNS DIFFERENT FROM HOURLY!!! TODO
#returns a dictionary with the inp time patterns
def getHourlyPatterns(networkFile):
    
    #Gets the section from the inp
    patternsRaw = swmmio.utils.dataframes.dataframe_from_inp(networkFile,'PATTERNS')
    #Gets the names of the patterns
    hourlyPatternsNames = patternsRaw[SWWM_C.PATTERNS].str.extract(r'^(.*?)\sHOURLY').iloc[:,0].unique()
    hPatterns = [value.strip() for value in hourlyPatternsNames if isinstance(value, str)]
    #Removes the HOURLY word and expands the values in different columns
    patternsRaw[SWWM_C.PATTERNS] = patternsRaw[SWWM_C.PATTERNS].str.replace(r'\sHOURLY\b', '', regex=True).str.strip()
    hourlyPatterns = patternsRaw[SWWM_C.PATTERNS].str.split(r'\s+', expand=True).set_index(0)
    
    #Creates the dicitonary
    patterns = {}
    for hp in hPatterns:
        df = hourlyPatterns.loc[hp] #selects all the rows refering to the pattern
        vals = list(chain.from_iterable(df.values.tolist())) #it flattens the values on a list
        patterns[hp] = vals
    
    return patterns


def getsNetwork(networkFile):
    
    nElements = {}
    
    # Instantiate a swmmio model object
    model = swmmio.Model(networkFile)

    # Pandas dataframes with nodes and links
    #DONT USE CONDUITS, they are more but dont have all the links (bug of the library, or inp?)
    fileName, extension = os.path.splitext(networkFile)
    outfile = f"{fileName}.out"
    if not os.path.exists(outfile):
        raise FileNotFoundError(f"Output file '{outfile}' does not exist. Please run a simulation in SWMM before.")

    links = model.links()[[SWWM_C.IN_NODE,SWWM_C.OUT_NODE,SWWM_C.LEN,SWWM_C.DIAM,
                           SWWM_C.MAX_Q,SWWM_C.ROUG,SWWM_C.INOFF,SWWM_C.OUTOFF,SWWM_C.SHAPE]].copy()
    nodes = model.nodes().index.to_series()
    subCatch = model.subcatchments()[[SWWM_C.CATCH_OUT,SWWM_C.AREA]]
    dwfs = model.inp.dwf[[SWWM_C.INFLOW_TYPE,SWWM_C.INFLOW_MEAN,SWWM_C.INFLOW_PATTERNS]].copy()
    #Only flow DWFS !! 
    dwfsWater = dwfs[dwfs[SWWM_C.INFLOW_TYPE]==SWWM_C.FLOW].drop(columns=[SWWM_C.INFLOW_TYPE]).copy()
    directFlows = model.inp.inflows #can't handle direct inflows with a baseline pattern !!! IMPORTANT TODO
    #Only direct water flows not other constituents
    directWaterFlows = directFlows[(directFlows[SWWM_C.DFLOW_CONSTITUENT]==SWWM_C.FLOW)&(directFlows[SWWM_C.TYPE]==SWWM_C.FLOW)].drop(columns=[SWWM_C.DFLOW_CONSTITUENT,SWWM_C.TYPE,SWWM_C.DFLOW_MFACTOR])
    #Only the time series related to direct water flows
    timeS = model.inp.timeseries.loc[directWaterFlows[SWWM_C.DFLOW_TIMES].dropna().unique().tolist()]
    
    patterns = getHourlyPatterns(networkFile) #returns a dicitonary 
    
    #remove subtachments with area 0
    totalSubcathments = subCatch.shape[0]
    subCatch = subCatch[subCatch[SWWM_C.AREA]>0]
    print("There were ", totalSubcathments - subCatch.shape[0], "subcatchments with area 0")
    
    #check that the network uses elevation
    assert model.inp.options.loc['LINK_OFFSETS'].iloc[0] == SWWM_C.ELEVATION

    #Get outlet and inlet nodes of pipes and cathments
    outNodes = links[SWWM_C.OUT_NODE].drop_duplicates()
    inNodes = links[SWWM_C.IN_NODE].drop_duplicates()

    #Get only nodes that are not outlets 
    startPoints = nodes[~nodes.isin(outNodes.tolist())]
    #Removes nodes that are not connected to the network
    sPointsCleaned = startPoints[startPoints.isin(inNodes.tolist())]
    
    nElements[STW_C.LINKS] = links
    nElements[STW_C.LEAVES] = sPointsCleaned
    nElements[STW_C.SUBCATCHMENTS] = subCatch
    nElements[STW_C.DWFS] = dwfsWater
    nElements[STW_C.DIRECTF] = directWaterFlows
    nElements[STW_C.T_PATTERNS] = patterns 
    nElements[STW_C.TIMESERIES] = timeS
    
    print("Number of nodes ", nodes.shape[0],", outlets ", outNodes.shape[0], ", startPoints ",startPoints.shape[0], ", and after cleaned ",sPointsCleaned.shape[0])

    return nElements, outfile
