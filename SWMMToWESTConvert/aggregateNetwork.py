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
        #TODO update doc
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

def selectRelevantBranches(fileOut:str, isTrunk:bool, pipesConnected:pd.DataFrame)->tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    """
        Iterates the DF of connected pipes, selecting the relevant branches and obtaining the ts of the pipes to be modelled as catchments.
        If the path is the network's trunk only not relevant pipes will be model as catchments.
        If the path is not the trunk then all connected pipes will be model as catchments.
    Args:
        fileOut (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        isTrunk (bool): Whether the path is the trunk of the network or not
        pipesConnected (pd.DataFrame): Pipes connected to the trunk, with index the name of the pipe and a column with the trunk pipe just 
                                       before the discharge.
    Returns:
        tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]: Time series of the pipes to be modelled as catchments, with name as columns and index the datetime.
                                               Pipes names of the connected pipes selected as relevant. #TODO change this and under explaining the datafram
                                               Pipes in the trunk where a discharging pipe that is going to be modelled as catchment
    """    
    tsDFCatchments = pd.DataFrame()
    relevantBranches = []

    for branch, row in pipesConnected.iterrows(): #the index (branch) is the name of the discharging pipe
        trunkPipe = row[STW_C.TRUNK_PIPE_NAME]
        relevant, tsCurrentBranch = evaluateBranchInfluence(fileOut, branch, trunkPipe) #Evaluates if its relevant or not
            
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

def selectBranches(fileOut:str, mainPath:pd.DataFrame,links:pd.DataFrame,isTrunk:bool)-> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:    
    """
        It decides if it is a pipe connected to the path is relevant.
        For this, it compares the flow timeseries of the connected pipe and the trunk before the connection. 
        If the flow of the pipe is larger than a set limit then it is selected as a branch.
        In case of the trunk, branches should be modeled in detail (tank series) and others just as a catchment.
        In case of a branch, sub branches will be model as catchments in the spot and others aggregated at the next cut point.
    Args:
        fileOut (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        mainPath (pd.DataFrame): links in the main path
        links (pd.DataFrame): All the links of the network
        trunk (bool): Whether the path is the trunk of the network or not.
    Returns:
        tuple[list[str],pd.DataFrame,pd.DataFrame]: Connected pipes names selected as relevant branches. 
                                            Timeseries of the pipes selected as catchments in columns index is datetime. For istrunk, these are only the not relevant, in other case it is all.
    """    
    pipesConnected = getPipesConnectedToPath(mainPath, links) #Gets the pipes connected to the path
    
    tsDFCatchments, relevantBranchCon, pipesCatchments = selectRelevantBranches(fileOut, isTrunk, pipesConnected)

    return relevantBranchCon, tsDFCatchments, pipesCatchments #TODO change the documentation 

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

def createLookPointsDF(nElements:dict)->pd.DataFrame:
    """
        Merges all the network flow elements (catchments, dwfs, direct flows) in a dataframe. 
        It aggregates catchments that discharge on the same node.
    Args:
        nElements (dict): Dictionary with links, leaves, catchments, DWFs, timepatterns, directflows and timeseries of the network.
    Returns:
        pd.DataFrame: Flow elements of the network. 
        No index. In the cols it is the outNode and the values of each different type of element added
    """    
    catchmNodes = nElements[STW_C.SUBCATCHMENTS].groupby([SWWM_C.CATCH_OUT]).agg({SWWM_C.AREA: 'sum'}).reset_index().rename( 
                                                    columns={'index':SWWM_C.OUT_NODE, SWWM_C.CATCH_OUT:SWWM_C.OUT_NODE}) #aggregates by node, and renames to be able to merge
    DWFsNodes = nElements[STW_C.DWFS].reset_index().rename(columns={SWWM_C.INFLOW_NODE:SWWM_C.OUT_NODE}) # renames to merge later
    dFlowNodes = nElements[STW_C.DIRECTF].reset_index().rename(columns={SWWM_C.INFLOW_NODE:SWWM_C.OUT_NODE}) # renames to merge later
    
    #Merges: adds the columns of the second table, and add not existent rows. 
    stopAndCatchmentDwf = pd.merge(catchmNodes, DWFsNodes, on=SWWM_C.OUT_NODE, how='outer') #Merges cathcments with dwfs points
    lookPoints = pd.merge(stopAndCatchmentDwf, dFlowNodes, on=SWWM_C.OUT_NODE, how='outer') #Merges direct inputs points
   
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
        linksPath (pd.DataFrame): Links in the main path
        linksToBreak (pd.DataFrame): Pipes where the path should be cutted. 
    Returns:
        tuple[list[pd.DataFrame],pd.Index]: Set of pipe sections cutted using the cut points. Index of the cut points in the complete path 
    """   
    indexCutLinks = linksToBreak.index + 1 #needed for the split
    dfs = np.split(linksPath, indexCutLinks)  #separates the path in smaller parts according to cut points
    print("Number of resulting sections of the path" , len(dfs))

    indexCutLinks = indexCutLinks - 1 
    cutlinks = indexCutLinks.to_list()

    return dfs, cutlinks

def getPathLookPoints(pathDF:pd.DataFrame, networkLookNodes:pd.DataFrame, pipesCatchments:pd.DataFrame)->pd.DataFrame:
    """TODO do this
    Args:
        pathDF (pd.DataFrame): _description_
        networkLookNodes (pd.DataFrame): _description_
        pipesCatchments (pd.DataFrame): _description_
    Returns:
        pd.DataFrame: _description_
    """    
    pathWithLookPoints = pathDF.join(networkLookNodes.set_index(SWWM_C.OUT_NODE), on=SWWM_C.OUT_NODE).copy() 

    pipesTS = pipesCatchments.reset_index().set_index(STW_C.TRUNK_PIPE_NAME).rename(columns={STW_C.DISCHARGE_PIPE_NAME:STW_C.MODELED_INPUT})
    
    pathWithLookPoints.to_csv('pathWithLookPoints.csv')

    pathWithLookPoints = pathWithLookPoints.join(pipesTS.drop(columns=[SWWM_C.OUT_NODE]))

    pipesTS.to_csv('pipesTS.csv')

    return pathWithLookPoints

#checks if the initial node of the path is a outlet node of a catchment and if it is, it returns its area
def checkForInitialElements(initialNode:str, lookupLinks:pd.DataFrame)->dict:
    """_summary_
        #TODO
    Args:
        initialNode (str): _description_
        lookupLinks (pd.DataFrame): _description_
    Returns:
        dict: _description_
    """    
    lookupLinks.set_index(SWWM_C.OUT_NODE,inplace=True)
    initialElement = {}
    
    if initialNode in lookupLinks.index:
        
        assert lookupLinks.loc[[initialNode]].shape[0] <=  1 ,f"There is more than one element with equal node out in the df"
        
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

def aggregatePathLookPoints(pathWithLookPoints:pd.DataFrame, breaklinksIndexPath:list[int])->pd.DataFrame:
    """
        Joins the linkpath df to the lookpoints and aggregates elements at break links.
        checks for elements at the initial point of the path
    Args:
        linksPath (pd.DataFrame): Links in the main path.
        lookPointsNetwork (pd.DataFrame): Flow elements of the network. Cols are outnode and the values of the elements.
        breaklinksIndexPath (pd.Index): Index of the cut points of the path. #TODO change documentation add new args
    Returns:
        tuple[pd.DataFrame,dict]: Path elements within the path. Elements at the start of the path.
    """    
    pathWithLookPoints[STW_C.BREAK_POINT] = pathWithLookPoints.index.to_series().apply(lambda idx: min((n for n in breaklinksIndexPath if n >= idx), default=None))
    
    checkUniqueDWFPatterns(pathWithLookPoints) #TODO check this!

    # Groups by the sections elements to the nearest break point --------------------------------------------------------------------
    pathElements = pathWithLookPoints.groupby([STW_C.BREAK_POINT]).agg({SWWM_C.NAME: 'last',
                                                                        SWWM_C.AREA:'sum', 
                                                                        SWWM_C.INFLOW_MEAN: 'sum', 
                                                                        SWWM_C.INFLOW_PATTERNS: 'first',
                                                                        SWWM_C.DFLOW_BASELINE: 'sum', 
                                                                        STW_C.MODELED_INPUT:lambda x: ', '.join(x) 
                                                                        }).set_index([SWWM_C.NAME]) 
    
    return pathElements

def modelPath(pathDF:pd.DataFrame, isTrunk:bool, links:pd.DataFrame, networkLookNodes:pd.DataFrame, outfile:str, nodeMeasurementFlow:list[str], networkPatterns:dict[list]):
    """
        #TODO return definitions, y doc!
    Args:
        pathDF (pd.DataFrame): Links in the main path.
        isTrunk (bool): True if the path to model is the main trunk of the network.
        links (pd.DataFrame): Links of the network
        networkLookNodes (pd.DataFrame): Flow elements of the network. Cols are outnode and the values of the elements.
        outfile (str): Path to the .out of the network.
        nodeMeasurementFlow (list[str]): _description_
        networkPatterns #TODO!!
    Returns:
        _type_: _description_
    """    
    relevantBranches, tsPipeCatchments, pipesCatchments = selectBranches(outfile,pathDF,links,isTrunk) 

    #Gets the break points and divides the path in various sections (dfs)  
    linksToBreak = getBreakPoints(pathDF, relevantBranches, nodeMeasurementFlow)
    pathDfs, indexbreakLinks = dividesPathByBreakPoints(pathDF,linksToBreak) 

    #selects look points within the path using the outnode and aggregates them at the cut points
    pathWithLookPoints = getPathLookPoints(pathDF, networkLookNodes, pipesCatchments)
    pathElements = aggregatePathLookPoints(pathWithLookPoints,indexbreakLinks) 

    #Checks for elements at the initial node of the path
    initialPathNode = pathDF.iloc[0][SWWM_C.IN_NODE]
    initialPathElements = checkForInitialElements(initialPathNode,networkLookNodes) 

    #converts the group of pipes into sewer sections, catchments, and dwf
    #TODO check for where timeseries to convert it to catchments
    branchModelsTanks, branchModelsCatch = cw.getPathElements(pathDfs,pathElements,initialPathElements,
                                                                        networkPatterns,tsPipeCatchments)

    return relevantBranches,branchModelsTanks, branchModelsCatch

def getTrunkModels(links:pd.DataFrame, networkLookNodes:pd.DataFrame, outfile:str, nodeMeasurementFlow:list[str], 
                   patterns:dict[list], idWRRF:str, idTrunkIni:str=None)->tuple[list[str],tuple[list,list]]:
    """
        Find the trunk of the model, selects the representative branches and converts the trunk into WEST models.
    Args:
        links (pd.DataFrame): Links of the network
        networkLookNodes (pd.DataFrame): Flow elements of the network. Cols are outnode and the values of the elements.
        outfile (str): Path to the .out of the network.
        #TODO add nodeMeasurementeFlow and patterns
        idWRRF (str): Name in the .inp of the node representing the entrance of the WRRF.
        idTrunkIni (str,optional): Id name of the most upstream node of the trunk in the .inp. Defaults to None.
    Returns:
        tuple[list[str],tuple[list,list]]: Names  of the connecting pipes to the trunk that were selected as branches to model in detail.
        Models representing the trunk with the list of tank series models and a list of catchments models.
    """    
    trunkDF = findTrunk(idWRRF,outfile,links,idTrunkIni) #df of the network's trunk

    branches, trunkModelsTanks, trunkModelsCatch = modelPath(trunkDF,True,links,networkLookNodes,outfile,nodeMeasurementFlow,patterns) 

    return branches,[trunkModelsTanks,trunkModelsCatch]

def getBranchesModels(links:pd.DataFrame, networkLookNodes:pd.DataFrame, outfile:str, nodeMeasurementFlow:list[str], patterns:dict[list],
                      branches:pd.DataFrame)->dict[dict]:
    """
        For each branch it finds the main flow path, selects the relevant branches and then convert them into WEST models
    Args:
        links (pd.DataFrame): Links of the network
        networkLookNodes (pd.DataFrame): Flow elements and measured nodes of the network. Cols are outnode and the values of the elements.
        outfile (str): Path of the .out file created by SWMM after running the model with the flowrate timeseries of the pipes
        branches (list[str]): names  of the connecting pipes to the trunk that were selected as branches to model in detail.
        #TODO add nodeMeasurementFlow and patterns
    Returns:
        dict[dict]: A dictionary for each branch using as key the name of the pipe discharging into the trunk. A branch dictionary has a list of tank series models and a list of catchments models 
    """    
    branchesModels = {}

    for branch in branches.index:#TODO this only works if there is only one pipe discahrging in that node
        
        nodeStartBranchTRunk = links.loc[branch,SWWM_C.OUT_NODE] #gets the node that connect to the main trunk and start the branch trunk

        pathDF = fp.findMainFlowPath(nodeStartBranchTRunk,outfile,links)

        branchModelsTanks, branchModelsCatch = modelPath(pathDF,False,links,networkLookNodes,outfile,nodeMeasurementFlow,patterns) 

        branchesModels[branch] = {} #creates the dictionary inside the dictionary with key the first pipe of the branch
        branchesModels[branch][STW_C.PATH] = branchModelsTanks
        branchesModels[branch][STW_C.WCATCHMENTS] = branchModelsCatch

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
    networkElements, outfile = gnpd.getsNetwork(networkInp) #Gets all the necesary elements from the network 
    networkLookPoints = createLookPointsDF(networkElements) #Joins all important points of the whole network into a df
    
    branches, trunkModels = getTrunkModels(networkElements[STW_C.LINKS], networkLookPoints, outfile, nodeMeasurementFlow, networkElements[STW_C.T_PATTERNS], idWRRF, idTrunkIni)  
    branchesModels = getBranchesModels(networkElements[STW_C.LINKS], networkLookPoints, outfile, nodeMeasurementFlow, networkElements[STW_C.T_PATTERNS], branches)

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
