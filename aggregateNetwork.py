import pandas as pd 
import numpy as np
from pyswmm import Output
from swmm.toolkit.shared_enum import LinkAttribute


#Files with constants
import SWMM_InpConstants as SWWM_C
import SWMMtoWESTConstants as STW_C


#Files with functions
import convertSWMMToWEST as cw
import findPaths as fp
import getNetworkFromSWMM as gnpd


#types of aggregation
AGG_CATCHMENT = 'AggregateAtNearestCatchment'

#utils 
BREAK_POINT = "BreakPoint"
PATH_ELEMENTS = "ElementsOnThePath"
PATH_ELEMENTS_INI = "ElementsOnTheBegginingOfThePath"


def convertListPathtoDF(path, links):
    
    #list of links names and information from the leaf node to the WTP
    linksPath= pd.DataFrame(path, columns= [SWWM_C.NAME])
    linksPath = linksPath.join(links,on= SWWM_C.NAME)
    
    return linksPath


def createLookPointsDF(nElements,pointsConnected,linkMeasurement,aggregating=AGG_CATCHMENT):
    
    #Get nodes out of the links with flow measures
    links = nElements[STW_C.LINKS]
    stopNodes = links[links.index.isin(linkMeasurement)][[SWWM_C.OUT_NODE]].copy()

    #gets created inputs (pipes that connect to the path with flow)
    createdInputs = pointsConnected.reset_index().rename(columns={SWWM_C.NAME:STW_C.MODELED_INPUT})

    #gets output nodes of catchments, and aggregates by node. renames so that all stop nodes and cathcment nodes can be merged
    catchmNodes = nElements[STW_C.SUBCATCHMENTS].groupby([SWWM_C.CATCH_OUT]).agg({SWWM_C.AREA: 'sum'}).reset_index().rename(
                                                    columns={'index':SWWM_C.OUT_NODE, SWWM_C.CATCH_OUT:SWWM_C.OUT_NODE})

    #selects the nodes where there is direct input, renames so that all stop nodes and cathcment nodes can be merged
    inputFlowNodes = nElements[STW_C.DWFS].reset_index().rename(columns={SWWM_C.INFLOW_NODE:SWWM_C.OUT_NODE})
    directFlowNodes = nElements[STW_C.DIRECTF].reset_index().rename(columns={SWWM_C.INFLOW_NODE:SWWM_C.OUT_NODE})
    
    print("Number of measurement points", len(stopNodes))
    print("Number of catchments nodes ",len(catchmNodes))
    print("Number of dw flows ", len(inputFlowNodes))
    print("Number of direct flows ",len(directFlowNodes))
    
    #Joins meassurement and catchment points
    #stopAndCatchment = pd.merge(stopNodes, catchmNodes, on=OUT_NODE, how='outer')
    stopAndInput = pd.merge(stopNodes, createdInputs, on=SWWM_C.OUT_NODE, how='outer')
    #Joins meassurement and catchment points
    #stopAndCatchmentAndInput = pd.merge(stopAndCatchment, createdInputs, on=OUT_NODE, how='outer')
    stopAndCatchmentAndInput = pd.merge(stopAndInput, catchmNodes, on=SWWM_C.OUT_NODE, how='outer')
    #Joins dry weather flows inputs points
    stopAndCatchmentDwf = pd.merge(stopAndCatchmentAndInput, inputFlowNodes, on=SWWM_C.OUT_NODE, how='outer')
    #Joins direct inputs points
    lookPoints = pd.merge(stopAndCatchmentDwf, directFlowNodes, on=SWWM_C.OUT_NODE, how='outer')
    
    #Gets the indexes to divide the path according to the level of aggregation
    if aggregating == AGG_CATCHMENT:
        #breakLinks = stopAndCatchmentAndInput
        breakLinks = stopAndInput
    else: #TODO other methods of aggregation ( This is no aggregation )
        breakLinks = None
    
    return lookPoints, breakLinks


def dividesPathByBreakPoints(linksPath,breakLinks):
    
    #Gets th index of the break points on the path and divides the pipe
    breakLinks = pd.merge(linksPath, breakLinks.set_index(SWWM_C.OUT_NODE), 
                              left_on=SWWM_C.OUT_NODE, right_index=True, how='inner',indicator=True).copy()
    indexBreakLinks = breakLinks.index + 1
    
    #separates the path in smaller parts according to the meassurable points
    dfs = np.split(linksPath, indexBreakLinks)    
    print("Number of divisions by meassurement or input nodes" , len(dfs))
    
    return dfs, indexBreakLinks

#checks if the initial node of the path is a outlet node of a catchment and if it is, it returns its area
def checkForInitialElements(dfPath,lookupLinks):
    
    initialNode = dfPath.iloc[0][SWWM_C.IN_NODE]
    lookupLinks.set_index(SWWM_C.OUT_NODE,inplace=True)
    initialElement = None
    
    if initialNode in lookupLinks.index:
        
        assert lookupLinks.loc[[initialNode]].shape[0] <=  1 ,f"There is more than one element with equal node out in the df"
        
        initialElement = {}
        initialElement[SWWM_C.OUT_NODE] = initialNode
        initialElement[SWWM_C.AREA] = lookupLinks.loc[initialNode,SWWM_C.AREA]
        initialElement[SWWM_C.INFLOW_MEAN] = lookupLinks.loc[initialNode,SWWM_C.INFLOW_MEAN]
        initialElement[SWWM_C.INFLOW_PATTERNS] = lookupLinks.loc[initialNode,SWWM_C.INFLOW_PATTERNS]
        initialElement[SWWM_C.DFLOW_BASELINE] = lookupLinks.loc[initialNode,SWWM_C.DFLOW_BASELINE]
        initialElement[STW_C.MODELED_INPUT] = lookupLinks.loc[initialNode,STW_C.MODELED_INPUT]
            
    return initialElement

def checkUniqueDWFPatterns(lookPointsPath):

    groupedPatterns = lookPointsPath.groupby(BREAK_POINT)[SWWM_C.INFLOW_PATTERNS].transform('nunique')
    assert len(lookPointsPath[BREAK_POINT][groupedPatterns > 1].unique()) == 0,f"Sewer sections with different DWF patterns are trying to be grouped."  
    assert lookPointsPath[SWWM_C.NAME].nunique() == lookPointsPath.shape[0],f"There are duplicate names"

# Joins the linkpath df to the lookpoints and slices the result df by element
# checks for elements at the initial point of the path 
# stores all the results in the proElements dictionary
def extractPathLookPoints(linksPath,lookPoints,breaklinksIndexPath):
    
    proElements = {}
    
    #selects the pipes IN THE PATH that are connected to look points
    lookPointsPath = linksPath.join(lookPoints.set_index(SWWM_C.OUT_NODE), on=SWWM_C.OUT_NODE).copy()
    
    #Finds the closest breaking point of each element --------------------------------------------------------------------------
    markerIndicesUnmodified = (breaklinksIndexPath - 1).tolist() #because previously one was added
    
    lookPointsPath[BREAK_POINT] = lookPointsPath.index.to_series().apply(lambda idx: min((n for n in markerIndicesUnmodified if n >= idx), default=None))
       
    # Check if there are no grouped sections with different dwf patterns --------------------------------------------------------
    checkUniqueDWFPatterns(lookPointsPath)

    # Groups by the sections elements to the nearest break point --------------------------------------------------------------------
    proElements[PATH_ELEMENTS] = lookPointsPath.groupby([BREAK_POINT]).agg({SWWM_C.NAME: 'last',SWWM_C.AREA:'sum', 
                                                                            SWWM_C.INFLOW_MEAN: 'sum', SWWM_C.INFLOW_PATTERNS: 'first',
                                                                            SWWM_C.DFLOW_BASELINE: 'sum', 
                                                                            STW_C.MODELED_INPUT:'first'}).set_index([SWWM_C.NAME]) #TODO add other values
    
    #proElements[PATH_ELEMENTS].to_csv('02-Output/'+'elementsGrouped'+'.csv')
    #lookPointsPath.to_csv('02-Output/'+'elementsImportantPath'+'.csv')
    
    #Checks for elements at the initial node of the path
    proElements[PATH_ELEMENTS_INI] = checkForInitialElements(linksPath,lookPoints)
    
    return proElements
    

def convertPathToSwrSectAndCatchts(linksPath, nElements,timeSeriesPointsCon, pointsConnected,linkMeasurement):
    
    #Calculate the slopes FOR OPTION IN THE INP = ELEVATION only for conduits
    linksPath[STW_C.SLOPE] = (linksPath[SWWM_C.INOFF]-linksPath[SWWM_C.OUTOFF])/linksPath[SWWM_C.LEN]
    
    #linksPath.to_csv('02-Output/'+'elementspath'+'.csv')

    #Joins all important points (measured nodes, out nodes of catchments, input flows for dwf and direct flows) into a df
    lookPoints, breaklinks = createLookPointsDF(nElements,pointsConnected,linkMeasurement)
    
    #Divides the path in various sections using dfs
    pathDfs, indexbreakLinks = dividesPathByBreakPoints(linksPath,breaklinks)

    #converts the important points into pipes with the characteristics required
    proElements = extractPathLookPoints(linksPath,lookPoints,indexbreakLinks)
   
    #separates the path by diameter and converts the group of pipes into sewer sections, catchments, and dwf
    pipeSectionsProperties, catchmentsProperties = cw.getPathElements(pathDfs,proElements[PATH_ELEMENTS],proElements[PATH_ELEMENTS_INI],
                                                                        nElements[STW_C.T_PATTERNS],timeSeriesPointsCon)
              
    return pipeSectionsProperties, catchmentsProperties

#find the pipes connected to the path giving it flow
def lookForOtherPipesConnected(linksPath,allLinks,fileOut):

    #Gets the links that are not in the path
    linksPathOutNodes = linksPath.set_index(SWWM_C.NAME)[SWWM_C.OUT_NODE]
    pipesNotPath = allLinks[~allLinks.index.isin(linksPathOutNodes.index)].copy()
    assert allLinks.shape[0] == pipesNotPath.shape[0] + linksPath.shape[0]
    
    #Gets links in the network connected to the path (but not part of it)
    pipesConnected = pipesNotPath[pipesNotPath[SWWM_C.OUT_NODE].isin(linksPathOutNodes)][[SWWM_C.OUT_NODE]].copy()
    pipesConnectedNames = pipesConnected.index.to_list()
    print("There are", len(pipesConnectedNames), "connections to the path")

    #Check that there are no more than one pipe per outnode!! TODO
    #-------TODO-------TODO-------TODO--------TODO-----TODO-----TODO

    #Gets the timeseries of the flow from the connections to the path
    tsDFNoZeros = None    
    if len(pipesConnectedNames) > 0:
        tsDF = None

        with Output(fileOut) as out:
            for pipe in pipesConnectedNames:
                
                ts = out.link_series(pipe, LinkAttribute.FLOW_RATE)
                
                if tsDF is None:
                    tsDF = pd.DataFrame.from_dict(ts, orient='index',columns=[pipe])
                else:
                    tsDF = tsDF.join(pd.DataFrame.from_dict(ts, orient='index',columns=[pipe]))
    
        # remove columns with only zeros
        tsDFNoZeros = tsDF.loc[:, (tsDF != 0).any(axis=0)]
        print(tsDF.shape[1] - tsDFNoZeros.shape[1],"connections to the path were removed due to no flow at anytime.") 

    #Removes from the list the pipes with only zero flow
    outNodesNoZeros = pipesConnected[pipesConnected.index.isin(tsDFNoZeros.columns.to_list())]
    
    return tsDFNoZeros, outNodesNoZeros


def aggregateTrunk(networkInp, idWTP, idTrunkIni, linkMeasurementFlow):

    #Gets all the elements from the network used
    nElements, outfile = gnpd.getsNetwork(networkInp)
    links = nElements[STW_C.LINKS]

    #Get all paths from leaves to water treatment plant
    pathsAll = fp.getPathToWTP(idWTP,links,nElements[STW_C.LEAVES])

    #---------------------------------------------------------------------------------
    #Get St sacrament path as df
    #Pipes in the path are in order from downstream to upstream
    trunkDF = convertListPathtoDF(pathsAll[idTrunkIni],links)

    #Gets the pipes connected to the path but not part of it with their flow timeseries
    timeSeriesPointsCon, pointsConnected  = lookForOtherPipesConnected(trunkDF,links,outfile)
    
    #converts the path from st sacrement to the WTP into sewer sections
    pipesModels, catchmentsModels = convertPathToSwrSectAndCatchts(trunkDF,nElements,timeSeriesPointsCon, pointsConnected,linkMeasurementFlow) 

    return pipesModels, catchmentsModels

