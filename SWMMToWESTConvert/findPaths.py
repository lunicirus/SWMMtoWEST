import SWMMToWESTConvert.SWMM_InpConstants as SWWM_C
import SWMMToWESTConvert.getNetworkFromSWMM as gnfs



def addLinkToPath(linkAux:'pd.Series',pipesPath:list[str])->tuple[str,list[str]]:
    """
        Adds the link to the path and obtains its nodeout
    Args:
        linkAux (pd.Series): link to add to the path and its attributes
        pipesPath (list[str]): links in the path 
    Returns:
        tuple[str,list[str]]: Most downstream node of the path. List of pipes in the path
    """    
    
    pipesPath.append(linkAux.name) 
    
    nodeAux = linkAux[SWWM_C.OUT_NODE] #Get's the node after the selected link
    
    return nodeAux, pipesPath


def reRoute(nodesDecision:list[str],links:'pd.DataFrame',pipesPath:list[str])->tuple['pd.Series',list[str],list[str]]:
    """
        Go to the last node a decision was made, and changes the pipe at the decision. It only reroutes twice 
        TODO make more general (nodes with 3 pipes)
        It also updates the path by removing the links added to the path after that node. 
    Args:
        nodesDecision (list[str]): List of nodes where a decision was made to construct the path.
        links (pd.DataFrame): Links of the network and their attributes.
        pipesPath (list[str]): List of pipes in the path already.
    Returns:
        tuple['pd.Series',list[str],list[str]]: The next pipe to be added to the path. 
                                                The modified path after the reroute.
                                                The nodes where a decision has been made in the path. 
    """   
    #Go to the last node a decision was made
    linksOut = links[links[SWWM_C.IN_NODE] == nodesDecision.pop()].sort_values(by=[SWWM_C.MAX_Q,SWWM_C.DIAM], ascending=False) 
    
    i=0
    linkDelete = linksOut.iloc[i]
    #If this is not the first time it reroutes
    if (not linkDelete.name in pipesPath):
        i=i+1
        linkDelete = linksOut.iloc[i]
        
    #removes the links in the failed section of the path
    iToDelete = pipesPath.index(linkDelete.name)
    del pipesPath[iToDelete:]

    #selects other pipe 
    linkAux = linksOut.iloc[i+1]
    
    return linkAux, pipesPath, nodesDecision

def lookForPath(finalDownstreamNode:str,initialNodeUpstream:str,links:'pd.DataFrame',pipesPath:list[str],
                nodesDecision:list[str])->tuple[list[str],list[str],str]:
    """
        Obtains a path from the initialNodeUpstream to the finalDownstreamNode selecting at decision points the 
        link with largest full Q and Geom 1 (Diameter if it is circular pipe). Removes circuits attached to the path.
    Args:
        finalDownstreamNode (str): id name of the node downstream where the paths must finish. 
        initialNodeUpstream (str): id name of the node upstream the leaves where the paths starts. 
        links (pd.DataFrame): Links of the network and their attributes.
        pipesPath (list[str]): List of pipes in the path already.
        nodesDecision (list[str]): List of nodes where a decision was made to construct the path.
    Returns:
        tuple[list[str],list[str],str]: Pipes in the path. 
                                        Nodes where a decision was made to construct the path. 
                                        Id name of the node upstream the leaves where the paths starts. 
    """    
    endPoint = False
    
    while (initialNodeUpstream != finalDownstreamNode) and (not endPoint):
        
        #Gets the links out of the node evaluated
        linksOut = links[links[SWWM_C.IN_NODE] == initialNodeUpstream].copy()

        if(linksOut.shape[0] > 1):
            nodesDecision.append(initialNodeUpstream) #Saves the last decision of this path

        if linksOut.empty:
            endPoint = True
        else:
            linkOut = linksOut.sort_values(by=[SWWM_C.MAX_Q,SWWM_C.DIAM], ascending=False).iloc[0] #Orders and select the links by largest diameter/full flow 

            #if the link selected was already selected for this iniNode then it is in a loop
            if linkOut.name in pipesPath:
                
                #If it does not have history is because is rerouting coz it went to an outlet
                if not nodesDecision:
                    print("Error")
                else:
                    linkOut,pipesPath,nodesDecision = reRoute(nodesDecision,links, pipesPath)

            initialNodeUpstream, pipesPath = addLinkToPath(linkOut,pipesPath)
         
            
    return pipesPath, nodesDecision, initialNodeUpstream


#Could be replaced by using this swmmio.utils.functions.find_network_trace()
def getPathToWTP(finalDownstreamNode:str,linksDF:'pd.DataFrame',leaves:list[str])-> dict[list[str]]:
    """
        Get all paths from leaves (end nodes or the network) to a specific final node (downstream the leaves), 
        starting at the leave and going downstream to the final node.
    Args:
        finalDownstreamNode (str): id name of the node downstream the leaves where the paths must finish.
        linksDF (pd.DataFrame): links of the network and their attributes
        leaves (list[str]): List of nodes from which the path is wanted to the final node
    Returns:
        dict[list[str]]: the keys are the leaves and values are list with the pipes of the path going from upstream to downstream.
    """    
    paths = {}

    # Repeat for each point
    for iniNode in leaves:

        pathsAux = []
        decisionsN = []
        
        pathsAux, decisionsN, endNode = lookForPath(finalDownstreamNode,iniNode,linksDF,pathsAux,decisionsN)

        while (endNode != finalDownstreamNode):

            try:
                linkOut,pathsAux,decisionsN = reRoute(decisionsN,linksDF, pathsAux)

            except Exception as e:
                print(iniNode, " ", e)
                paths[iniNode] = pathsAux
                break

            nodeAux, pathsAux = addLinkToPath(linkOut,pathsAux)

            #Looks for the path again
            pathsAux,decisionsN,endNode = lookForPath(finalDownstreamNode,nodeAux,linksDF,pathsAux,decisionsN)

        paths[iniNode] = pathsAux  #Saves the list of pipes
            
    return paths


def findMainFlowPath(endNode:str,outPath:str,linksNetwork:'pd.DataFrame')-> 'pd.DataFrame':
    """
        Selects pipe by pipe going upstream from the end node, selecting the pipe with largest flow.
        Assumes the pipes direction is correct (outnode is downstream and innode upstream)
    Args:
        endNode (str): name of the end node (i.e. WRRF). 
        outPath (str): path of the .out of the network SWMM model.
        linksNetwork (pd.DataFrame): all links of the network with name as index and its characteristics and connecting nodes as attributes.
    Returns:
        pd.DataFrame: links selected as part of the trunk with name as index and its characteristics and connecting nodes as attributes. 
                      ordered upstream to downstream.
    """
    nodeEval = endNode
    trunk = []
    trunkDF = None

    try:
        while nodeEval is not None:
            previousPipes = linksNetwork[linksNetwork[SWWM_C.OUT_NODE]==nodeEval].copy() #gets all the pipes discharging to the evaluated node

            if previousPipes.shape[0] != 0: 

                dfTSprePipes = gnfs.getFlowTimeSeries(previousPipes.index.to_list(),outPath) #gets the time series of all connected pipes to the node evaluated

                pipeTrunk = dfTSprePipes.mean().idxmax() # Calculate the mean of each pipe and gets the pipe with the largest mean

                trunk.append(pipeTrunk) #adds the selected pipe to the list of the trunk

                nodeEval = previousPipes.loc[pipeTrunk,SWWM_C.IN_NODE] #Gets the  name of the inital node of the pipe selected
            else:
                nodeEval = None

        trunkUptoDownstream = trunk[::-1]
        trunkDF = linksNetwork.loc[trunkUptoDownstream].copy() #gets the attributes of the pipes in the trunk and its ordered downstream to upstream

    except Exception as e:
        print("Error finding the main water path: ", e)

    return trunkDF