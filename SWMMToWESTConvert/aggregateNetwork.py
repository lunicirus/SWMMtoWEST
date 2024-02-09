import pandas as pd 
import numpy as np
from pyswmm import Output
from swmm.toolkit.shared_enum import LinkAttribute


#Files with constants
import SWMMToWESTConvert.SWMM_InpConstants as SWWM_C
import SWMMToWESTConvert.SWMMtoWESTConstants as STW_C


#Files with functions
import SWMMToWESTConvert.convertSWMMToWEST as cw
import SWMMToWESTConvert.findPaths as fp
import SWMMToWESTConvert.getNetworkFromSWMM as gnpd


#types of aggregation
AGG_CATCHMENT = 'AggregateAtNearestCatchment'

#utils 
BREAK_POINT = "BreakPoint"
PATH_ELEMENTS = "ElementsOnThePath"
PATH_ELEMENTS_INI = "ElementsOnTheBegginingOfThePath"


def convertListPathtoDF(path:list[str], linksNetwork:pd.DataFrame)->pd.DataFrame:
    """
        Converts a path in list form into a dataframe with the pipes' characteristics maintaining the same order.
    Args:
        path (list[str]): list of names of the pipes in the path
        linksNetwork (pd.DataFrame): links of the entire network. Index is the link name and columns are their attributes.
    Returns:
        pd.DataFrame: records are the pipes of the path in order, index is the name and columns are the attributes.
    """         
    
    return linksNetwork.loc[path].copy()


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
                                                                            STW_C.MODELED_INPUT:'first'}).set_index([SWWM_C.NAME]) 
    
    #proElements[PATH_ELEMENTS].to_csv('02-Output/'+'elementsGrouped'+'.csv')
    #lookPointsPath.to_csv('02-Output/'+'elementsImportantPath'+'.csv')
    
    #Checks for elements at the initial node of the path
    proElements[PATH_ELEMENTS_INI] = checkForInitialElements(linksPath,lookPoints)
    
    return proElements
    
#DEPRECATED 
def convertPathToSwrSectAndCatchts(linksPath, nElements,timeSeriesPointsCon, pointsConnected,linkMeasurement):
    
    #linksPath.to_csv('02-Output/'+'elementspath'+'.csv')

    #Joins all important points (measured nodes, out nodes of catchments, input flows for dwf and direct flows) into a df
    lookPoints, breaklinks = createLookPointsDF(nElements,pointsConnected,linkMeasurement)
    
    #Divides the path in various sections using dfs
    pathDfs, indexbreakLinks = dividesPathByBreakPoints(linksPath,breaklinks)

    #converts the important points into links with the characteristics required
    proElements = extractPathLookPoints(linksPath,lookPoints,indexbreakLinks)
   
    #separates the path by diameter and converts the group of pipes into sewer sections, catchments, and dwf
    pipeSectionsProperties, catchmentsProperties = cw.getPathElementsDividingByDiam(pathDfs,proElements[PATH_ELEMENTS],proElements[PATH_ELEMENTS_INI],
                                                                        nElements[STW_C.T_PATTERNS],timeSeriesPointsCon)
              
    return pipeSectionsProperties, catchmentsProperties

#DEPRECATED
def lookForOtherPipesConnected(linksPath,allLinks,fileOut):
    #find the pipes connected to the path giving it flow

    #Gets the links that are not in the path
    linksPathOutNodes = linksPath.set_index(SWWM_C.NAME)[SWWM_C.OUT_NODE]
    pipesNotPath = allLinks[~allLinks.index.isin(linksPathOutNodes.index)].copy()
    assert allLinks.shape[0] == pipesNotPath.shape[0] + linksPath.shape[0]

    #pipesNotPath.to_csv('pipesNotInPath.csv')
    
    #Gets links in the network connected to the path (but not part of it)
    pipesConnected = pipesNotPath[pipesNotPath[SWWM_C.OUT_NODE].isin(linksPathOutNodes)][[SWWM_C.OUT_NODE]].copy()
    pipesConnectedNames = pipesConnected.index.to_list()
    print("There are", len(pipesConnectedNames), "connections to the path")

    #pipesConnected.to_csv('pipesConnected.csv')

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

        #tsDF.to_csv('cleaned.csv', index=True)
    
        # remove columns with only zeros
        tsDFNoZeros = tsDF.loc[:, (tsDF != 0).any(axis=0)]
        print(tsDF.shape[1] - tsDFNoZeros.shape[1],"connections to the path were removed due to no flow at anytime.") 

    #Removes from the list the pipes with only zero flow
    outNodesNoZeros = pipesConnected[pipesConnected.index.isin(tsDFNoZeros.columns.to_list())]
    
    return tsDFNoZeros, outNodesNoZeros

#DEPRECATED
def aggregateTrunk(networkInp:str, idWTP:str, idTrunkIni:str, linkMeasurementFlow:list[str]) -> tuple[list[dict],list[dict]]:
    
    """It obtains the elements of the network and converts it into a trunk with elements (catchments, DWFs, DFs) attached. 
        Then, it converts the trunk into a list of tanks in series and the elements into a list of catchments.
    Args:
        networkInp (str): path to the networks .inp file
        idWTP (str): id of the water treatment plant (where the trunk finishes)
        idTrunkIni (str): id of the initial node of the trunk 
        linkMeasurementFlow (list[str]): list of ids of the pipes where meassurements are taken

    Returns:
         tuple[list[dict],list[dict]]: List of tanks in series (WEST models) of the trunk with its parameters, 
                                       List of catchments (WEST models) with its parameters
    """
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

def getPipesConnectedToPath(linksTrunk:pd.DataFrame, allLinks:pd.DataFrame) -> pd.DataFrame:
    """
        Search for pipes connected to the trunk
    Args:
        linksTrunk (pd.DataFrame): Links in the trunk path
        allLinks (pd.DataFrame): All the links of the network

    Returns:
        pd.DataFrame: pipes connected to the trunk associated with the pipe just before their connection and the outnode.
    """    

    #Gets the links that are not in the path
    linksPathOutNodes = linksTrunk.set_index(SWWM_C.NAME)[[SWWM_C.OUT_NODE]]
    pipesNotPath = allLinks[~allLinks.index.isin(linksPathOutNodes.index)].copy()
    assert allLinks.shape[0] == pipesNotPath.shape[0] + linksTrunk.shape[0]

    #pipesNotPath.to_csv('pipesNotInPath.csv')
    
    #Gets links in the network connected to the path (but not part of it)
    pipesConnected = pipesNotPath[pipesNotPath[SWWM_C.OUT_NODE].isin(linksPathOutNodes[SWWM_C.OUT_NODE])][[SWWM_C.OUT_NODE]].copy()
    print("There are", pipesConnected.shape[0], "connections to the path")

    #pipesConnected.to_csv('pipesConnected.csv')

    #creates a dataframe with the name of the discharging pipe and one column with the name of the pipe of the trunk before the discharge
    pipesConnected = pipesConnected.reset_index().set_index([SWWM_C.OUT_NODE]).join(
                                                                            linksPathOutNodes.reset_index().set_index([SWWM_C.OUT_NODE]),
                                                                            lsuffix=STW_C.CONNECTED_PIPE_SUFFIX, 
                                                                            rsuffix=STW_C.TRUNK_PIPE_SUFFIX)
    #resets the index again to name
    pipesConnected = pipesConnected.reset_index().set_index(SWWM_C.NAME + STW_C.CONNECTED_PIPE_SUFFIX)

    return pipesConnected

def selectBranches(fileOut:str, pipesConnected:pd.DataFrame)-> tuple[list[str],pd.DataFrame|None,pd.DataFrame]:    
    """
        It decides if it is a pipe connected to the trunk needs to be modeled in detail (tank series) or just as a catchment.
        For this, it compares the flow timeseries of the connected pipe and the trunk before the connection. 
        If the flow of the pipe is larger than a set limit then it is selected as a branch.
    Args:
        fileOut (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        pipesConnected (pd.DataFrame): Df of the pipes connected to the trunk, with index the name of the pipe, 
                                       and a column named "SWWM_C.NAME + STW_C.TRUNK_PIPE_SUFFIX" with the name of trunk pipe before the connection.

    Returns:
        tuple[list(str), pd.DataFrame, pd.DataFrame]: Connected pipes names selected as branches, timeseries of the pipes selected as catchments,
                                                      all pipes (and their outnodes) that are modelled either as branches or catchments
    """

    tsDFCatchments = None
    branches = []
    trunkPipeLabel = SWWM_C.NAME + STW_C.TRUNK_PIPE_SUFFIX

    #the index is the name of the discharging pipe
    for index, row in pipesConnected.iterrows():
        trunkPipe = row[trunkPipeLabel]

        #Gets the timeseries of the flow from the connections to the path and the pipe before the discharge
        dfTS = gnpd.getFlowTimeSeries([index,trunkPipe],fileOut)
        maxVals = dfTS.max()

        maxDischarging = maxVals[index]
        limitFlowrate = maxVals[trunkPipe] * STW_C.PERC_LIM_TO_BRANCH
            
        #Checks that the values are not all zero
        if ((dfTS[index] != 0).any()): 
            if (maxDischarging > limitFlowrate):
                branches.append(index)
            else:
                if tsDFCatchments is None:
                    tsDFCatchments = dfTS.drop(columns=[trunkPipe])
                else:
                    tsDFCatchments = tsDFCatchments.join(dfTS.drop(columns=[trunkPipe]))

    outNodesToBreak =  pipesConnected[(pipesConnected.index.isin(branches)) | (pipesConnected.index.isin(tsDFCatchments.columns.to_list()))].drop(trunkPipeLabel, axis=1)  
        
    print(tsDFCatchments.shape[1]," connections to the path to be converted into catchments") 
    print(len(branches),' connections in the path to be modelled as branches')

    return branches,tsDFCatchments,outNodesToBreak

def convertBranchesToModels(branchesStart:list[str], NetworkLinks:pd.DataFrame, outFile:str):

    branchesModels = {}

    for b in branchesStart:

        catchs = []
        tanks = []

        branchesModels[b] = {} #creates the dictionary inside the dictionary with key the branch

        nodeStartBranchTRunk = NetworkLinks.loc[b,SWWM_C.OUT_NODE] #gets the node that connect to the main trunk and start the branch trunk

        fp.findMainFlowPath(nodeStartBranchTRunk,outFile,NetworkLinks)



    return branchesModels

def findTrunk(idWRRF:str, outfile:str, links:pd.DataFrame, idTrunkIni:str=None)->pd.DataFrame:
    """
        Finds the trunk of the network. If the start point of the trunk is known then finds the path between that point and the WRRF.
        If the start point is unknown then it selects the path with largest flow, starting from the WRRF.
    Args:
        idWRRF (str): id name of the node in the .inp representing the entrance of the WRRF
        outfile (str): path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        links (pd.DataFrame): links (pipes, pumps..) of the network
        idTrunkIni (str): id name of the most upstream node of the trunk in the .inp

    Returns:
        pd.Dataframe: each record is a link on the trunk and columns are characteristics, ordered upstream to downstream.
    """    
    if idTrunkIni is None:
        trunkDF = fp.findMainFlowPath(idWRRF,outfile,links) #Gets the path of the larges flow 
    else:
        path = fp.getPathToWTP(idWRRF,links,[idTrunkIni]) #Get path as a list from leave to WRRF
        trunkDF = convertListPathtoDF(path[idTrunkIni],links) 

    return trunkDF

def aggregateAndModelPath(linkMeasurementFlow, nElements, outfile, trunkDF,trunk:bool=False):

    linksNetwork = nElements[STW_C.LINKS] #get all the links on the network

    pipesConnected = getPipesConnectedToPath(trunkDF, linksNetwork) #Gets the pipes connected to the path

    #Selects which branches to model as tank in series, as catchments or no model depending on their flow rate
    branches,tsPipeCatchments,outNodesToBreak = selectBranches(outfile, pipesConnected) 

    if (trunk):
    
        
        #TODO finish the select branches has to have this if. and 
        #if it is not trunk then the big flow pipes are converted into catchments, the low flow pipes are removed and the flow ..

    #converts the path from st sacrement to the WTP into sewer sections
    #trunk models has tanks and catchments
    trunkModels = convertPathToSwrSectAndCatchts(trunkDF,nElements,tsPipeCatchments,outNodesToBreak,linkMeasurementFlow) 

    # modelar las ramas y retornar tambien una tupla con lista de modelos y lista de catchments
    branchesModels = convertBranchesToModels(branches,linksNetwork,outfile)

    

    return trunkModels,branchesModels


def aggregateTrunkAndBranches(networkInp : str, idWTP: str, linkMeasurementFlow: list[str], idTrunkIni: str= None):
    """Converts a detailed network into a trunk with branches and elements attached.
       Then it converts the trunk and branches into tank in series models and all other elements
       are into catchments models. Models are returned as dictionaries. 
    Args:
        networkInp (str): .inp of a detailed hydraulic wastewater network that has been previously run in SWwM so it has an associated .out file too.
        idWTP (str): id name of the node in the .inp representing the entrance of the WRRF
        idTrunkIni (str):  id name of the most upstream node of the trunk in the .inp
        linkMeasurementFlow (list[str]): list of pipe names from the .inp where measurements are avaliable

    Returns:
        _type_: _description_ TODO 
    """    

    nElements, outfile = gnpd.getsNetwork(networkInp) #Gets all the necesary elements from the network 
    
    trunkDF = findTrunk(idWTP, idTrunkIni, outfile, nElements[STW_C.LINKS]) #df of the network's trunk

    #Gets the pipes connected to the path but not part of it 
    trunkModels, branchesModels = aggregateAndModelPath(linkMeasurementFlow, nElements, outfile, trunkDF)


    return trunkModels, branchesModels