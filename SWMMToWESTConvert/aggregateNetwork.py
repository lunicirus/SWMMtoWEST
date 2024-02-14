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

def findTrunk(idWRRF:str, outfile:str, links:pd.DataFrame, idTrunkIni:str=None)->pd.DataFrame:
    """
        Finds the trunk of the network. If the start point of the trunk is known then finds the path between that point and the WRRF.
        If the start point is unknown then it selects the path with largest flow, starting from the WRRF.
    Args:
        idWRRF (str): id name of the node in the .inp representing the entrance of the WRRF
        outfile (str): path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        links (pd.DataFrame): links (pipes, pumps..) of the network
        idTrunkIni (str,optional): id name of the most upstream node of the trunk in the .inp. Defaults to None.
    Returns:
        pd.Dataframe: each record is a link on the trunk and columns are characteristics, ordered upstream to downstream.
    """    
    if idTrunkIni is None:
        trunkDF = fp.findMainFlowPath(idWRRF,outfile,links) #Gets the path of the larges flow 
    else:
        path = fp.getPathToWTP(idWRRF,links,[idTrunkIni]) #Get path as a list from leave to WRRF
        trunkDF = convertListPathtoDF(path[idTrunkIni],links) 

    return trunkDF

def getPipesConnectedToPath(linksMainPath:pd.DataFrame, allLinks:pd.DataFrame) -> pd.DataFrame:
    """
        Search for pipes connected to the trunk
    Args:
        linksMainPath (pd.DataFrame): Links in the main path
        allLinks (pd.DataFrame): All the links of the network
    Returns:
        pd.DataFrame: pipes connected to the trunk associated with the pipe just before their connection and the outnode.
                    The column is named "SWWM_C.NAME + STW_C.TRUNK_PIPE_SUFFIX".
    """    
    linksPathOutNodes = linksMainPath[[SWWM_C.OUT_NODE]] 
    pipesNotPath = allLinks[~allLinks.index.isin(linksPathOutNodes.index)].copy() #Gets the links that are not in the path
    assert allLinks.shape[0] == pipesNotPath.shape[0] + linksMainPath.shape[0]

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

    pipesConnected = pipesConnected.reset_index().set_index(SWWM_C.NAME + STW_C.CONNECTED_PIPE_SUFFIX) #resets the index again to name

    return pipesConnected

def evaluateBranchInfluence(fileOut:str, branchPipe:str, trunkPipeBeforeBranch:str)->tuple[bool, pd.DataFrame]:
    """
        Obtains the flowrate time series of the two pipes and decide if the brach is relevant or not.
        If the mean flowrate of the branch is larger than the STW_C.PERC_LIM_TO_BRANCH % of the trunk then is relevant.
    Args:
        fileOut (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        branchPipe (str): name of the pipe discharging into the trunk
        trunkPipeBeforeBranch (str): trunk pipe just before the discharge of the branch pipe
    Returns:
        tuple[bool, pd.DataFrame]: true if the branch is relevant, time series of the flow rate of the branch
    """
    #the flow from the connections to the path and the pipe before the discharge
    dfTS = gnpd.getFlowTimeSeries([branchPipe,trunkPipeBeforeBranch],fileOut) #Gets the timeseries of both pipes (branchPipe, trunkPipeBeforeBranch)

    meanVals = dfTS.mean() #gets the mean of both flow timeseries
    meanDischarging = meanVals[branchPipe]
    limitFlowrate = meanVals[trunkPipeBeforeBranch] * STW_C.PERC_LIM_TO_BRANCH

    relevant = meanDischarging > limitFlowrate
    tsBranch =  dfTS.drop(columns=[trunkPipeBeforeBranch])

    return relevant, tsBranch

def selectBranches(fileOut:str, trunk:bool, pipesConnected:pd.DataFrame)->tuple[pd.DataFrame,list,pd.DataFrame]:
    """
        Iterates the DF of connected pipes, selecting the relevant branches and obtaining the ts of the pipes to be modelled as catchments.
        If the path is the network's trunk only not relevant pipes will be model as catchments.
        If the path is not the trunk then all connected pipes will be model as catchments.
    Args:
        fileOut (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        trunk (bool): Whether the path is the trunk of the network or not
        pipesConnected (pd.DataFrame): Pipes connected to the trunk, with index the name of the pipe and a column with the trunk pipe just 
                                       before the discharge.
    Returns:
        tuple[pd.DataFrame,list,pd.DataFrame]: Time series of the pipes to be modelled as catchments, with name as columns and index the datetime.
                                               Pipes names of the connected pipes selected as relevant.
                                               Pipes connected to the trunk without the column of the trunk pipe.
    """    
    trunkPipeLabel = SWWM_C.NAME + STW_C.TRUNK_PIPE_SUFFIX
    tsDFCatchments = None
    relevantBranches = []

    for branch, row in pipesConnected.iterrows(): #the index (branch) is the name of the discharging pipe
        trunkPipe = row[trunkPipeLabel]
        relevant, tsCurrentBranch = evaluateBranchInfluence(fileOut, branch, trunkPipe) #Evaluates if its relevant or not
            
        if ((tsCurrentBranch[branch] != 0).any()): #Checks that the values are not all zero
            if (relevant):
                relevantBranches.append(branch) 
            
            if (not relevant and trunk) or (not trunk): 
                if tsDFCatchments is None:
                    tsDFCatchments = tsCurrentBranch
                else:
                    tsDFCatchments = tsDFCatchments.join(tsCurrentBranch)

    print(len(relevantBranches),' relevant branches')
    print(tsDFCatchments.shape[1]," connections to the path to be converted into catchments") 

    pipesConnected = pipesConnected.drop(trunkPipeLabel, axis=1)

    return tsDFCatchments,relevantBranches,pipesConnected

def getBreakPoints(trunk:bool, pipesAsCatchments:list, relevantBranches:list, pipesConnected:pd.DataFrame)->pd.DataFrame:
    """
        Select points to break the path. 
        If it is the trunk then all pipes with nonzero discharging flow are a path break point. 
        If it is a branch only relevant pipes are a break point
    Args:
        trunk (bool): whether the path is the trunk of the network or not
        pipesAsCatchments (list): Pipe names of the pipes to be modelled as catchments
        relevantBranches (list): Pipes names of the pipes connected to the path and selected as relevant
        pipesConnected (pd.DataFrame): List of the pipes connected to the trunk, with index the name of the pipe.
    Returns:
        pd.DataFrame: break points to cut the path 
    """    
    if trunk:
        outNodesToBreak =  pipesConnected[(pipesConnected.index.isin(relevantBranches)) | (pipesConnected.index.isin(pipesAsCatchments))]
    else:
        outNodesToBreak = pipesConnected[(pipesConnected.index.isin(relevantBranches))]

    print(outNodesToBreak.shape[0]," points to break the path were found")

    return outNodesToBreak

def selectBranchesAndBreakPoints(fileOut:str, mainPath:pd.DataFrame,links:pd.DataFrame,trunk:bool=False)-> tuple[list[str],pd.DataFrame|None,pd.DataFrame]:    
    """
        It decides if it is a pipe connected to the trunk needs to be modeled in detail (tank series) or just as a catchment.
        For this, it compares the flow timeseries of the connected pipe and the trunk before the connection. 
        If the flow of the pipe is larger than a set limit then it is selected as a branch.
    Args:
        fileOut (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        mainPath (pd.DataFrame): links in the main path
        links (pd.DataFrame): All the links of the network
        trunk (bool, optional): Whether the path is the trunk of the network or not. Defaults to False.
    Returns:
        tuple[list[str],pd.DataFrame|None,pd.DataFrame]: Connected pipes names selected as branches. 
                                                         Timeseries of the pipes selected as catchments.
                                                         All pipes (name as index and outnodes as column) that are modelled either as branches or catchments
    """    
    pipesConnected = getPipesConnectedToPath(mainPath, links) #Gets the pipes connected to the path

    tsDFCatchments, relevantBranches, pipesConnected = selectBranches(fileOut, trunk, pipesConnected)

    outNodesToBreak = getBreakPoints(trunk, tsDFCatchments.columns.to_list(), relevantBranches, pipesConnected)

    return relevantBranches,tsDFCatchments,outNodesToBreak

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

def createLookPointsDF(nElements:dict,timeSeriesPointsCon:pd.DataFrame)->pd.DataFrame:
    """
        Merges all the network flow elements (measured nodes, catchments, dwfs, direct flows, and incoming pipes) in a dataframe. 
        It aggregates catchments that discharge on the same node.
    Args:
        nElements (dict): Dictionary with links, leaves, catchments, DWFs, timepatterns, directflows and timeseries of the network.
        timeSeriesPointsCon (pd.DataFrame): Timeseries of the pipes discharging into the path and selected as catchments.
    Returns:
        pd.DataFrame: lookPoints of the network to be converted to WEST catchments. 
    """    
    links = nElements[STW_C.LINKS]
    
    TSFlowsNodes = links[links.index.isin(timeSeriesPointsCon.columns.to_list())][[SWWM_C.OUT_NODE]].copy()#gets the pipes connected and dischargint into the path
    TSFlowsNodes[STW_C.MODELED_INPUT]= True 
    catchmNodes = nElements[STW_C.SUBCATCHMENTS].groupby([SWWM_C.CATCH_OUT]).agg({SWWM_C.AREA: 'sum'}).reset_index().rename( 
                                                    columns={'index':SWWM_C.OUT_NODE, SWWM_C.CATCH_OUT:SWWM_C.OUT_NODE}) #aggregates by node, and renames to be able to merge
    DWFsNodes = nElements[STW_C.DWFS].reset_index().rename(columns={SWWM_C.INFLOW_NODE:SWWM_C.OUT_NODE}) # renames to merge later
    dFlowNodes = nElements[STW_C.DIRECTF].reset_index().rename(columns={SWWM_C.INFLOW_NODE:SWWM_C.OUT_NODE}) # renames to merge later
    
    #Merges: adds the columns of the second table, and add not existent rows. 
    tsFlowAndCatchment = pd.merge(TSFlowsNodes, catchmNodes, on=SWWM_C.OUT_NODE, how='outer') #Merges of meassurement and catchment points
    stopAndCatchmentDwf = pd.merge(tsFlowAndCatchment, DWFsNodes, on=SWWM_C.OUT_NODE, how='outer') #Merges dry weather flows inputs points
    lookPoints = pd.merge(stopAndCatchmentDwf, dFlowNodes, on=SWWM_C.OUT_NODE, how='outer') #Merges direct inputs points
   
    return lookPoints

def dividesPathByBreakPoints(linksPath:pd.DataFrame,nodeBreak:pd.DataFrame,linkMeasurement:list[str])-> tuple[list[pd.DataFrame],pd.Index]:
    """
        Joins the nodes to break with link measurements and cuts the path using these points.
    Args:
        linksPath (pd.DataFrame): Links in the main path
        nodeBreak (pd.DataFrame): Break points to cut the path 
        linkMeasurement (list[str]): pipe names where measurements are taken in the field.
    Returns:
        tuple[list[pd.DataFrame],pd.Index]: Set of pipe sections cutted using the cut points. Index of the cut points in the complete path 
    """   


    measuringNodes = linksPath[linksPath[SWWM_C.OUT_NODE].isin(linkMeasurement)][[SWWM_C.OUT_NODE]].copy() #Get nodes out of the links with flow measures
    print("Number of measurement points", len(measuringNodes))

    breakLinksAndMeasure= pd.merge(nodeBreak, measuringNodes, on=SWWM_C.OUT_NODE, how='outer') #joins break links and measurement points
        
    linksPath=linksPath.reset_index()
    
    cutLinks = pd.merge(linksPath, breakLinksAndMeasure.set_index(SWWM_C.OUT_NODE), 
                              left_on=SWWM_C.OUT_NODE, right_index=True, how='inner',indicator=True).copy() #Gets th index of the break points on the path 
    
    indexCutLinks = cutLinks.index + 1
        
    dfs = np.split(linksPath, indexCutLinks)  #separates the path in smaller parts according to cut points
    print("Number of divisions by meassurement or input nodes" , len(dfs))
    
    return dfs, indexCutLinks

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

def checkUniqueDWFPatterns(lookPointsPath:pd.DataFrame):

    groupedPatterns = lookPointsPath.groupby(STW_C.BREAK_POINT)[SWWM_C.INFLOW_PATTERNS].transform('nunique')
    assert len(lookPointsPath[STW_C.BREAK_POINT][groupedPatterns > 1].unique()) == 0,f"Sewer sections with different DWF patterns are trying to be grouped."  
    assert lookPointsPath[SWWM_C.NAME].nunique() == lookPointsPath.shape[0],f"There are duplicate names"

# Joins the linkpath df to the lookpoints and slices the result df by element
# checks for elements at the initial point of the path 
# stores all the results in the proElements dictionary
def extractPathLookPoints(linksPath:pd.DataFrame,lookPoints:pd.DataFrame,breaklinksIndexPath:pd.Index)->tuple[pd.DataFrame,dict]:

    #selects the pipes IN THE PATH that are connected to look points
    lookPointsPath = linksPath.join(lookPoints.set_index(SWWM_C.OUT_NODE), on=SWWM_C.OUT_NODE).copy()
    
    #Finds the closest breaking point of each element --------------------------------------------------------------------------
    markerIndicesUnmodified = (breaklinksIndexPath - 1).tolist() #because previously one was added
    
    lookPointsPath[STW_C.BREAK_POINT] = lookPointsPath.index.to_series().apply(lambda idx: min((n for n in markerIndicesUnmodified if n >= idx), default=None))
       
    # Check if there are no grouped sections with different dwf patterns --------------------------------------------------------
    checkUniqueDWFPatterns(lookPointsPath)

    # Groups by the sections elements to the nearest break point --------------------------------------------------------------------
    pathElements = lookPointsPath.groupby([STW_C.BREAK_POINT]).agg({SWWM_C.NAME: 'last',SWWM_C.AREA:'sum', 
                                                                            SWWM_C.INFLOW_MEAN: 'sum', SWWM_C.INFLOW_PATTERNS: 'first',
                                                                            SWWM_C.DFLOW_BASELINE: 'sum', 
                                                                            STW_C.MODELED_INPUT:'first'}).set_index([SWWM_C.NAME]) 
    
    #lookPointsPath.to_csv('02-Output/'+'elementsImportantPath'+'.csv')
    
    #Checks for elements at the initial node of the path
    initialPathElements = checkForInitialElements(linksPath,lookPoints)
    
    return pathElements,initialPathElements
    
def convertPathToSwrSectAndCatchts(linksPath:pd.DataFrame, networkElements:dict,timeSeriesPointsCon:pd.DataFrame, 
                                   nodesTobreakPath:pd.DataFrame,linkMeasurement:list[str]=[])->tuple[list[dict],list[dict]]: 
    """_summary_ #TODO!!

    Args:
        linksPath (pd.DataFrame): Links in the main path
        networkElements (dict): Dictionary with links, leaves, catchments, DWFs, timepatterns, directflows and timeseries of the network.
        timeSeriesPointsCon (pd.DataFrame): Time series of the pipes to be modelled as catchments, with name as columns and index the datetime.
        nodesTobreakPath (pd.DataFrame): Break points to cut the path. Pipe name as index and nodeout as column.
        linkMeasurement (list[str], optional): List of pipe names where measurements are taken in the field. Defaults to an empty list.
    Returns:
        tuple[list[dict],list[dict]]: a dictionary per tank model of the converted path (to tank in series) with its characteristiscs.
                                      a dictionary per catchment model representing one or more inflows from (DWF, DF, cathment, or discharging pipe)
    """    
    #linksPath.to_csv('02-Output/'+'elementspath'+'.csv')
   
    pathDfs, indexbreakLinks = dividesPathByBreakPoints(linksPath,nodesTobreakPath,linkMeasurement,networkElements[STW_C.LINKS])#Divides the path in various sections using dfs

    pathElements, initialPathElements = extractPathLookPoints(linksPath,lookPoints,indexbreakLinks) #converts the important points into links with the characteristics required
   
    #separates the path by diameter and converts the group of pipes into sewer sections, catchments, and dwf
    pipeSectionsProperties, catchmentsProperties = cw.getPathElementsDividingByDiam(pathDfs,pathElements,initialPathElements,
                                                                        networkElements[STW_C.T_PATTERNS],timeSeriesPointsCon)
              
    return pipeSectionsProperties, catchmentsProperties

def getTrunkModels(idWRRF:str, linkMeasurementFlow:list[str], networkElements:dict, outfile:str, idTrunkIni:str=None)->tuple[list[str],tuple[list,list]]:
    """
        Find the trunk of the model, selects the representative branches and converts the trunk into WEST models.
    Args:
        idWRRF (str): Name in the .inp of the node representing the entrance of the WRRF.
        linkMeasurementFlow (list[str]): List of pipe names where measurements are taken in the field
        networkElements (dict): Links, leaves, catchments, DWFs, timepatterns, directflows and timeseries of the network. 
        outfile (str): Path to the .out of the network.
        idTrunkIni (str,optional): Id name of the most upstream node of the trunk in the .inp. Defaults to None.
    Returns:
        tuple[list[str],tuple[list,list]]: Names  of the connecting pipes to the trunk that were selected as branches to model in detail.
        Models representing the trunk with the list of tank series models and a list of catchments models.
    """    
    linksNetwork= networkElements[STW_C.LINKS]

    trunkDF = findTrunk(idWRRF, outfile, linksNetwork, idTrunkIni) #df of the network's trunk

    #Selects which branches to model detailed as tank in series, or as catchments depending on their flow rate
    branches,tsPipeCatchmentsTrunk,outNodesToBreakTrunk = selectBranchesAndBreakPoints(outfile, trunkDF,linksNetwork,True) 
 
    trunkModels = convertPathToSwrSectAndCatchts(trunkDF,networkElements,tsPipeCatchmentsTrunk,outNodesToBreakTrunk,linkMeasurementFlow)

    return branches,trunkModels

def getBranchesModels(networkElements:dict, outfile:str, branches:list[str])->dict[dict]:
    """
        For each branch it finds the main flow path, selects the relevant branches and then convert them into WEST models
    Args:
        networkElements (dict): Dictionary with links, leaves, catchments, DWFs, timepatterns, directflows and timeseries of the network.
        outfile (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        branches (list[str]): names  of the connecting pipes to the trunk that were selected as branches to model in detail.
    Returns:
        dict[dict]: A dictionary for each branch using as key the name of the pipe discharging into the trunk. A branch dictionary has a list of tank series models and a list of catchments models 
    """    
    branchesModels = {}
    linksNetwork= networkElements[STW_C.LINKS]

    for branch in branches:
        nodeStartBranchTRunk = linksNetwork.loc[branch,SWWM_C.OUT_NODE] #gets the node that connect to the main trunk and start the branch trunk

        pathDF = fp.findMainFlowPath(nodeStartBranchTRunk,outfile,linksNetwork)

        relevant,tsPipeCatchments,outNodesToBreak = selectBranchesAndBreakPoints(outfile, pathDF,linksNetwork) 

        branchModelsTanks, branchModelsCatch = convertPathToSwrSectAndCatchts(pathDF,networkElements,tsPipeCatchments,outNodesToBreak) 

        branchesModels[branch] = {} #creates the dictionary inside the dictionary with key the first pipe of the branch
        branchesModels[branch][STW_C.PATH] = branchModelsTanks
        branchesModels[branch][STW_C.WCATCHMENTS] = branchModelsCatch

    return branchesModels

def aggregateAndModelNetwork(networkInp:str, idWRRF:str, linkMeasurementFlow:list[str],idTrunkIni:str= None)->tuple[tuple[list,list],dict[dict]]:  
    """
        Converts a detailed network given in the .inp on a list of tank in series and catchments for the trunk, and the same of each important branch.
        It uses the list of measurements flows as additional cut points in the trunk. It aggregates branches by flowrate.
    Args:
        networkInp (str): Path of the .inp of the network
        idWRRF (str): Name in the .inp of the node representing the entrance of the WRRF.
        linkMeasurementFlow (list[str]): List of pipe names where measurements are taken in the field
        idTrunkIni (str, optional): Id name of the most upstream node of the trunk in the .inp. Defaults to None.
    Returns:
        tuple[tuple[list,list],dict[dict]]: A tuple representing the trunk with the list of tank series models and a list of catchments models.
                                            A dictonary with a dictionary for each branch. Each branch dictionary has a list of tank series models and a list of catchments models.
    """    
    networkElements, outfile = gnpd.getsNetwork(networkInp) #Gets all the necesary elements from the network 

    lookPoints = createLookPointsDF(networkElements,timeSeriesPointsCon) #Joins all important points of the whole network into a df
    
    branches, trunkModels = getTrunkModels(idWRRF, linkMeasurementFlow, networkElements, outfile, idTrunkIni)  
    branchesModels = getBranchesModels(networkElements, outfile, branches)

    return trunkModels,branchesModels




#-----------------------------------------------------------------------------------------------------------------------------------
#DEPRECATED----------------------------------------------------------

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
