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
        Search for pipes connected to a path.
    Args:
        linksMainPath (pd.DataFrame): Links in the main path
        allLinks (pd.DataFrame): All the links of the network
    Returns:
        pd.DataFrame: pipes connected to the path associated with the pipe just before their connection and the outnode.
    """    
    linksPathOutNodes = linksMainPath[[SWWM_C.OUT_NODE]] 
    pipesNotPath = allLinks[~allLinks.index.isin(linksPathOutNodes.index)].copy() #Gets the links that are not in the path
    assert allLinks.shape[0] == pipesNotPath.shape[0] + linksMainPath.shape[0] ,f"The total number of pipes is the same as the sum of pipes in the path and pipes not in the path"

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

def evaluateRelativeBranchInfluence(fileOut:str, branchPipe:str, comparisonPipe:str)->tuple[bool, pd.DataFrame]:
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
    dfTS = gnpd.getFlowTimeSeries([branchPipe,comparisonPipe],fileOut) #Gets the timeseries of both pipes (branchPipe, trunkPipeBeforeBranch)

    meanVals = dfTS.mean() #gets the mean of both flow timeseries
    meanDischarging = meanVals[branchPipe]
    limitFlowrate = meanVals[comparisonPipe] * STW_C.PERC_LIM_TO_BRANCH


    relevant = meanDischarging > limitFlowrate
    tsBranch =  dfTS.drop(columns=[comparisonPipe])

    return relevant, tsBranch

def selectRelevantBranches(fileOut:str, isTrunk:bool, pipesConnected:pd.DataFrame, endPathLink:str=None)->tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    """
        Iterates the DF of connected pipes, selecting the relevant branches and obtaining the ts of the pipes to be modelled as catchments.
        If the path is the network's trunk only not relevant pipes will be model as catchments.
        If the path is not the trunk then all connected pipes will be model as catchments.
    Args:
        fileOut (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        isTrunk (bool): Whether the path is the trunk of the network or not
        pipesConnected (pd.DataFrame): Pipes connected to the trunk, with index the name of the pipe and a column with the trunk pipe just 
                                       before the discharge.
        endPathLink (str): The last downstream pipe of the path to use for the comparison of the relevant pipes. Default None.
    Returns:
        tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]: Time series of the pipes to be modelled as catchments, with name as columns and index the datetime.
                                               Names of the connected pipes selected as relevant. Index is the name of the discharging pipe, columns are outnode and trunk pipe.
                                               Pipes in the trunk where a discharging pipe that is going to be modelled as catchment.Index is the name of the discharging pipe, columns are outnode and trunk pipe.
    """    
    tsDFCatchments = pd.DataFrame()
    relevantBranches = []

    for branch, row in pipesConnected.iterrows(): #the index (branch) is the name of the discharging pipe

        if endPathLink is None:
            trunkPipe = row[STW_C.TRUNK_PIPE_NAME]
            relevant, tsCurrentBranch = evaluateRelativeBranchInfluence(fileOut, branch, trunkPipe) #Evaluates if its relevant or not
        else:
            relevant, tsCurrentBranch = evaluateRelativeBranchInfluence(fileOut, branch, endPathLink)
            
        if ((tsCurrentBranch[branch] != 0).any()): #Checks that the values are not all zero
            if (relevant):
                relevantBranches.append(branch) 
            
            if (not relevant and isTrunk) or (not isTrunk): 
                if (tsDFCatchments.shape[0] == 0):
                    tsDFCatchments = tsCurrentBranch
                else:
                    tsDFCatchments = tsDFCatchments.join(tsCurrentBranch)

    print(len(relevantBranches),' relevant branches')
    print(tsDFCatchments.shape[1]," connections to the path to be converted into catchments") 

    pipesWithCatchments = pipesConnected[pipesConnected.index.isin(tsDFCatchments.columns.to_list())]
    revelantBranchesConnection = pipesConnected[pipesConnected.index.isin(relevantBranches)]

    assert len(pipesWithCatchments) == tsDFCatchments.shape[1] ,f"The number of pipes to be converted to catchments is not the same in both DFs"

    return tsDFCatchments, revelantBranchesConnection, pipesWithCatchments

def selectBranches(fileOut:str, mainPath:pd.DataFrame,links:pd.DataFrame,isTrunk:bool,isRelative:bool=True)-> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:    
    """
        It decides if it is a pipe connected to the path is relevant.
        For this, it compares the flow timeseries of the connected pipe and the trunk before the connection. 
        If the flow of the pipe is larger than a set limit then it is selected as a branch.
        In case of the trunk, branches should be modeled in detail (tank series) and others just as a catchment.
        In case of a branch, sub relevant branches will be model as catchments in the spot and others aggregated at the next cut point.
    Args:
        fileOut (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        mainPath (pd.DataFrame): links in the main path. Index is the order of the pipe.
        links (pd.DataFrame): All the links of the network
        trunk (bool): Whether the path is the trunk of the network or not.
        isRelative (bool): Whether the selection of the relevant branches is done relative to the flow of the trunk at the joint point or not.
    Returns:
        tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]: Connected pipes selected as relevant branches. Index is the name of the discharging pipe, columns are outnode and trunk pipe.
                                            Timeseries of the pipes selected as catchments in columns index is datetime. For istrunk, these are only the not relevant, in other case it is all.
                                            Pipes selected as catchments. Index is the name of the discharging pipe, columns are outnode and trunk pipe.
    """    
    pipesConnected = getPipesConnectedToPath(mainPath, links) #Gets the pipes connected to the path
    
    if isRelative:
        tsDFCatchments, relevantBranchCon, pipesCatchments = selectRelevantBranches(fileOut, isTrunk, pipesConnected)
    else:
        lastPipe = mainPath.iloc[-1].name
        tsDFCatchments, relevantBranchCon, pipesCatchments = selectRelevantBranches(fileOut, isTrunk, pipesConnected, lastPipe)

    return relevantBranchCon, tsDFCatchments, pipesCatchments 

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

def getNetworkLookPoints(nElements:dict)->pd.DataFrame:
    """
        Merges all the network flow elements (catchments, dwfs, direct flows) in a dataframe. 
        It aggregates catchments that discharge on the same node.
    Args:
        nElements (dict): Dictionary with links, leaves, catchments, DWFs, timepatterns, directflows and timeseries of the network.
    Returns:
        pd.DataFrame: Nodes with flow elements and their characteristics (i.e., Area,...,Baseline). Index is OutletNode.
    """    
    catchmNodes = nElements[STW_C.SUBCATCHMENTS].groupby([SWWM_C.CATCH_OUT]).agg({SWWM_C.AREA: 'sum'}).reset_index().rename( 
                                                    columns={'index':SWWM_C.OUT_NODE, SWWM_C.CATCH_OUT:SWWM_C.OUT_NODE}) #aggregates by node, and renames to be able to merge
    DWFsNodes = nElements[STW_C.DWFS].reset_index().rename(columns={SWWM_C.INFLOW_NODE:SWWM_C.OUT_NODE}) # renames to merge later
    dFlowNodes = nElements[STW_C.DIRECTF].reset_index().rename(columns={SWWM_C.INFLOW_NODE:SWWM_C.OUT_NODE}) # renames to merge later
    
    #Merges: adds the columns of the second table, and add not existent rows. 
    stopAndCatchmentDwf = pd.merge(catchmNodes, DWFsNodes, on=SWWM_C.OUT_NODE, how='outer') #Merges cathcments with dwfs points
    lookPoints = pd.merge(stopAndCatchmentDwf, dFlowNodes, on=SWWM_C.OUT_NODE, how='outer') #Merges direct inputs points
   
    lookPoints.set_index(SWWM_C.OUT_NODE,inplace=True)

    return lookPoints

def getBreakPoints(pathDF: pd.DataFrame, relevantBranches:pd.DataFrame, nodesMeasurement:list[str])->pd.DataFrame:
    """
        Select the links to break the path. These are the links where relevant branches join and where there are nodes where measurements are taken.
    Args:
        pathDF (pd.DataFrame): Ordered links on the path with index pipe name. 
        relevantBranches (pd.DataFrame): Index is the connecting pipe name and the first column is the trunk pipe name where the pipe is connected.
        nodesMeasurement (list[str]): Names of the nodes connected to the path, where measurements are taken.
    Returns:
        pd.DataFrame: Pipes where the path should be cutted. 
    """    
    pathDF.reset_index(inplace=True)
    linksToBreak = pathDF[(pathDF[SWWM_C.NAME].isin(relevantBranches[STW_C.TRUNK_PIPE_NAME].to_list())) | (pathDF[SWWM_C.OUT_NODE].isin(nodesMeasurement))] 
    
    print(len(linksToBreak)," points to break the path were found")

    return linksToBreak

def dividesPathByBreakPoints(linksPath:pd.DataFrame,linksToBreak:pd.DataFrame)-> tuple[list[pd.DataFrame],list[int]]:
    """
        Splits the path using the links to break.
    Args:
        linksPath (pd.DataFrame): Links in the path
        linksToBreak (pd.DataFrame): Pipes where the path should be cutted. 
    Returns:
        tuple[list[pd.DataFrame],list[int]]: Set of pipe sections cutted using the cut points. List of the cut points indexes in the complete path 
    """   
    indexCut= linksToBreak.index
    indexCutLinks = list(indexCut + 1)

    dfs = [linksPath.iloc[i:j] for i, j in zip([0] + indexCutLinks, indexCutLinks + [len(linksPath)])]
    print("Number of resulting sections of the path" , len(dfs))

    return dfs, list(indexCut)

def getPathLookPoints(pathDF:pd.DataFrame, networkLookNodes:pd.DataFrame, pipesCatchments:pd.DataFrame)->pd.DataFrame:
    """
        Filters the network flow elements to obtain the flow elements on the path, and adds the pipes to be modelled as catchments
        to the look points.
    Args:
        pathDF (pd.DataFrame): Links in the main path with their characteristics, index is the order from upstream to downstream.
        networkLookNodes (pd.DataFrame): Nodes with flow elements and their characteristics (i.e., Area,...,Baseline). Index is OutletNode.
        pipesCatchments (pd.DataFrame): Links to be modelled as catchments. Index is discharging pipe, columns are ouletNode and trunk pipe.
    Returns:
        pd.DataFrame: Look points of the path including flow elements and discharing pipes in the path to be modelled as catchments.
    """    
    pathWithLookPoints = pathDF.join(networkLookNodes, on=SWWM_C.OUT_NODE).copy() 

    pipesTS = pipesCatchments.reset_index().set_index(STW_C.TRUNK_PIPE_NAME).rename(columns={STW_C.DISCHARGE_PIPE_NAME:STW_C.MODELED_INPUT})
    
    pathWithLookPoints = pathWithLookPoints.join(pipesTS.drop(columns=[SWWM_C.OUT_NODE]),on=SWWM_C.NAME)

    return pathWithLookPoints

def checkForInitialElements(initialPipe:pd.Series, networkLookupNodes:pd.DataFrame)->dict:
    """
        Creates a dictionary with the flow values of the initial node of the path.
    Args:
        initialPipe (pd.Series): Initial pipe of the path (upstream)
        networkLookupNodes (pd.DataFrame): Nodes with flow elements and their characteristics (i.e., Area,...,Baseline). Index is OutletNode.
    Returns:
        dict: flow values of the initial node of the path.
    """    
    initialElement = {}
    initialNode = initialPipe[SWWM_C.IN_NODE]
    
    if initialNode in networkLookupNodes.index:
        
        assert networkLookupNodes.loc[[initialNode]].shape[0] <=  1 ,f"There is more than one element with equal node out in the df"
        
        initialElement[SWWM_C.OUT_NODE] = initialNode
        initialElement[SWWM_C.AREA] = networkLookupNodes.loc[initialNode,SWWM_C.AREA]
        initialElement[SWWM_C.INFLOW_MEAN] = networkLookupNodes.loc[initialNode,SWWM_C.INFLOW_MEAN]
        initialElement[SWWM_C.INFLOW_PATTERNS] = networkLookupNodes.loc[initialNode,SWWM_C.INFLOW_PATTERNS]
        initialElement[SWWM_C.DFLOW_BASELINE] = networkLookupNodes.loc[initialNode,SWWM_C.DFLOW_BASELINE]

    return initialElement

def checkUniqueDWFPatterns(lookPointsPath:pd.DataFrame):

    groupedPatterns = lookPointsPath.groupby(STW_C.BREAK_POINT)[SWWM_C.INFLOW_PATTERNS].transform('nunique')
    assert len(lookPointsPath[STW_C.BREAK_POINT][groupedPatterns > 1].unique()) == 0,f"Sewer sections with different DWF patterns are trying to be grouped."  
    assert lookPointsPath[SWWM_C.NAME].nunique() == lookPointsPath.shape[0],f"There are duplicate names"

def setAggregationNodes(pathWithLookPoints, breaklinks:list[int])->pd.DataFrame:
    """
        Set the aggregated node to the closest downstream node. In other words, finds the minimum value in breaklinks that is greater than or 
        equal to the current index idx and sets it as the aggregation point. 
        If there is no value that satisfies this condition, the last index of the path is returned.
    Args:
        pathWithLookPoints (pd.DataFrame):  Look points of the path (i.e., flow elements and connected pipes to be modelled as catchments). 
                                            Index is the order of the pipe in the path and columns are the values of the elements.
        breaklinks (list[int]): Index of the cut points of the path. 
    Returns:
        pd.DataFrame: Look points of the path with the break point at which their values should be aggregated.
    """    
    pathWithLookPoints[STW_C.BREAK_POINT] = pathWithLookPoints.index.to_series().apply(lambda idx: min((n for n in breaklinks if n >= idx), default= pathWithLookPoints.index[-1]))

    return pathWithLookPoints

def aggregatePathLookPoints(pathWithLookPoints:pd.DataFrame, breaklinksIndexPath:list[int])->pd.DataFrame:
    """
        Aggregates the values of the path look points at the closest cut point in the path. 
    Args:
        pathWithLookPoints (pd.DataFrame): Look points of the path (i.e., flow elements and connected pipes to be modelled as catchments). 
                                            Index is the order of the pipe in the path and columns are the values of the elements.
        breaklinksIndexPath (list[int]): Index of the cut points of the path. 
    Returns:
        pd.DataFrame: Aggregated look points of the path.
    """    
    pathWithLookPoints = setAggregationNodes(pathWithLookPoints, breaklinksIndexPath)

    checkUniqueDWFPatterns(pathWithLookPoints) #TODO check this!
    
    # Groups by the sections elements to the nearest break point ----------------------------------------------------------
    pathElements = pathWithLookPoints.groupby([STW_C.BREAK_POINT]).agg({SWWM_C.NAME: 'last',
                                                                        SWWM_C.AREA:'sum', 
                                                                        SWWM_C.INFLOW_MEAN: 'sum', 
                                                                        SWWM_C.INFLOW_PATTERNS: 'first',
                                                                        SWWM_C.DFLOW_BASELINE: 'sum', 
                                                                        STW_C.MODELED_INPUT:lambda x: ','.join(str(val) for val in x if pd.notna(val))
                                                                        }).set_index([SWWM_C.NAME]) 
    
    return pathElements

def removeSectionsWithoutFlow(pathDfs:list[pd.DataFrame],initialPathElements:pd.DataFrame) -> list[pd.DataFrame]:
    """
        If there are no initial path elements the first section is removed as it will not carry water and all elements are agregated downstream.
    Args:
        pathDfs (list[pd.DataFrame]): Each dataframe in the list represent a section of the path.
        initialPathElements (pd.DataFrame): Initial elements of the path
    Returns:
        list[pd.DataFrame]: Dataframes representing the path without the first section if there are no initial elements in the path.
    """    
    if not initialPathElements:
        pathDfs = pathDfs[1:]

    return pathDfs


def modelPath(pathDF:pd.DataFrame, isTrunk:bool, links:pd.DataFrame, networkLookNodes:pd.DataFrame, outfile:str,
               nodeMeasurementFlow:list[str], networkPatterns:dict[list])->tuple[pd.DataFrame,list[dict],list[dict]]:
    """
        #Selects the relevant branches of the path, divides the path in sections, aggregates flow elements discharging directly into the path, 
        and creates the models of the tanks in series and catchments to represent the path. 
    Args:
        pathDF (pd.DataFrame): Links in the main path. Index is the order of the pipe.
        isTrunk (bool): True if the path to model is the main trunk of the network.
        links (pd.DataFrame): Links of the network. Index is the name of the pipe.
        networkLookNodes (pd.DataFrame): Nodes with flow elements and their characteristics (i.e., Area,...,Baseline). Index is OutletNode.
        outfile (str): Path to the .out of the network.
        nodeMeasurementFlow (list[str]): List of nodes where field measurements are taken.
        networkPatterns (dict[list]):Patterns of the network. 
    Returns:
        tuple[pd.DataFrame,list[dict],list[dict]]:  Connected pipes selected as relevant branches. Index is the name of the discharging pipe, columns are outnode and trunk pipe.
                                                    List of tank series models representing the path.
                                                    List of catchments models representing the path.
    """    
    relevantBranches, tsPipeCatchments, pipesCatchments = selectBranches(outfile,pathDF,links,isTrunk,False) 

    #Gets the break points and divides the path in various sections (dfs)  
    linksToBreak = getBreakPoints(pathDF, relevantBranches, nodeMeasurementFlow)
    pathDfs, indexbreakLinks = dividesPathByBreakPoints(pathDF,linksToBreak) 

    #selects look points within the path using the outnode and aggregates them at the cut points
    pathWithLookPoints = getPathLookPoints(pathDF, networkLookNodes, pipesCatchments)
    pathElements = aggregatePathLookPoints(pathWithLookPoints,indexbreakLinks) 

    #Checks for elements at the initial node of the path and if there are not it removes the first section
    initialPathElements = checkForInitialElements(pathDF.iloc[0],networkLookNodes) 
    pathDfs = removeSectionsWithoutFlow(pathDfs,initialPathElements)

    branchModelsTanks, branchModelsCatch = cw.getPathElements(pathDfs,pathElements,initialPathElements,
                                                                        networkPatterns,tsPipeCatchments,pathDF.iloc[0].Name)

    return relevantBranches,branchModelsTanks, branchModelsCatch

def getTrunkModels(links:pd.DataFrame, networkLookNodes:pd.DataFrame, outfile:str, nodeMeasurementFlow:list[str], 
                   patterns:dict[list], idWRRF:str, idTrunkIni:str=None)->tuple[list[str],tuple[list,list]]:
    """
        Find the trunk of the model, selects the relevant branches and converts the trunk and the selected branches into WEST models.
    Args:
        links (pd.DataFrame): Links of the network. Rows are the pipes.
        networkLookNodes (pd.DataFrame): Nodes with flow elements and their characteristics (i.e., Area,...,Baseline). Index is OutletNode.
        outfile (str): Path to the .out of the network.
        nodeMeasurementFlow (list[str]): List of nodes where field measurements are taken.
        patterns (dict[list]): Patterns of the network. 
        idWRRF (str): Name in the .inp of the node representing the entrance of the WRRF.
        idTrunkIni (str,optional): Id name of the most upstream node of the trunk in the .inp. Defaults to None.
    Returns:
        tuple[list[str],tuple[list,list],pd.DataFrame]: Names of the connecting pipes to the trunk that were selected as branches to model in detail.
                                                        Models representing the trunk with the list of tank series models and a list of catchments models.
    """    
    print("-------------------------------Obtaining and modelling the Trunk -------------------------------------------------")
    trunkDF = findTrunk(idWRRF,outfile,links,idTrunkIni) #df of the network's trunk

    branches, trunkModelsTanks, trunkModelsCatch = modelPath(trunkDF,True,links,networkLookNodes,outfile,nodeMeasurementFlow,patterns) 

    return branches, [trunkModelsTanks,trunkModelsCatch], trunkDF

def getBranchesModels(links:pd.DataFrame, networkLookNodes:pd.DataFrame, outfile:str, nodeMeasurementFlow:list[str], patterns:dict[list],
                      branches:pd.DataFrame, trunkPath: pd.DataFrame)->dict[dict]:
    """
        For each branch it finds the main flow path, selects the relevant branches and then convert them into WEST models
    Args:
        links (pd.DataFrame): Links of the network
        networkLookNodes (pd.DataFrame): Nodes with flow elements and their characteristics (i.e., Area,...,Baseline). Index is OutletNode.
        outfile (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        nodeMeasurementFlow (list[str]): List of nodes where field measurements are taken.
        patterns (dict[list]): Patterns of the network.
        branches (list[str]): Names  of the connecting pipes to the trunk that were selected as branches to model in detail.
        trunkPath (pd.DataFrame): Links on the trunk path.
    Returns:
        dict[dict]: A dictionary for each branch using as key the name of the pipe discharging into the trunk. A branch dictionary has a list of tank series models and a list of catchments models 
    """    
    print("-------------------------------Obtaining and converting the branches --------------------------------------------------")
    branchesModels = {}

    for branch in branches.index:#TODO this only works if there is only one pipe discahrging in that node
        
        print("--------------------------Obtaining and modelling branch ",branch,"-------------------------------------------")
        nodeStartBranch = links.loc[branch,SWWM_C.IN_NODE] 
        nodeConnectingTrunk = links.loc[branch,SWWM_C.OUT_NODE] 

        pathDF = fp.findMainFlowPath(nodeStartBranch,outfile,links)

        bRelevant, branchModelsTanks, branchModelsCatch = modelPath(pathDF,False,links,networkLookNodes,outfile,nodeMeasurementFlow,patterns) 

        #creates the dictionary inside the dictionary with key the outnode where the branch discharges
        branchConnection = trunkPath[trunkPath[SWWM_C.OUT_NODE] == nodeConnectingTrunk].Name.iloc[0]
        branchesModels[branchConnection] = {} 
        branchesModels[branchConnection][STW_C.PATH] = branchModelsTanks
        branchesModels[branchConnection][STW_C.WCATCHMENTS] = branchModelsCatch

    return branchesModels

def aggregateAndModelNetwork(networkInp:str, idWRRF:str, nodeMeasurementFlow:list[str],idTrunkIni:str= None)->tuple[tuple[list,list],dict[dict]]:  
    """
        Converts a detailed network given in the .inp on a list of tank in series and catchments for the trunk, and the same of each important branch.
        It uses the list of measurements flows as additional cut points in the trunk. It aggregates branches by flowrate.
    Args:
        networkInp (str): Path of the .inp of the network
        idWRRF (str): Name in the .inp of the node representing the entrance of the WRRF.
        nodeMeasurementFlow (list[str]): List of node names where measurements are taken in the field
        idTrunkIni (str, optional): Id name of the most upstream node of the trunk in the .inp. Defaults to None.
    Returns:
        tuple[tuple[list,list],dict[dict]]: A tuple representing the trunk with the list of tank series models and a list of catchments models.
                                            A dictonary with a dictionary for each branch. Each branch dictionary has a list of tank series models and a list of catchments models.
    """    
    networkElements, outfile = gnpd.getNetwork(networkInp) #Gets all the necesary elements from the network 
    networkLookPoints = getNetworkLookPoints(networkElements) #Joins all important points of the whole network into a df
    
    branches, trunkModels, trunk = getTrunkModels(networkElements[STW_C.LINKS], networkLookPoints, outfile, nodeMeasurementFlow, networkElements[STW_C.T_PATTERNS], idWRRF, idTrunkIni)  
    branchesModels = getBranchesModels(networkElements[STW_C.LINKS], networkLookPoints, outfile, nodeMeasurementFlow, networkElements[STW_C.T_PATTERNS], branches, trunk)

    return trunkModels, branchesModels

