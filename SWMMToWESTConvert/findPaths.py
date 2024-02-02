import SWMMToWESTConvert.SWMM_InpConstants as SWWM_C
import SWMMToWESTConvert.getNetworkFromSWMM as gnfs


#Adds the linkOut to the path 
def addLinkToPath(linkOut,pipesPath):
    
    linkOutName = linkOut.name
    
    pipesPath.append(linkOutName)

    #Get's the node after the selected link
    nodeAux = linkOut[SWWM_C.OUT_NODE]
    
    return nodeAux, pipesPath

#It only reroutes twice
#Go to the last node a decision was made, and removes the links added to the path aftar that node
#changes to the next pipe at the decision node
def reRoute(nodesDecision,links,pipesPath):
    
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
    linkOut = linksOut.iloc[i+1]
    
    return linkOut, pipesPath, nodesDecision

def lookForPath(WTP_Tank,nodeAux,links:'pd.DataFrame',pipesPath,nodesDecision):
    
    endPoint = False
    
    while (nodeAux != WTP_Tank) and (not endPoint):
        
        #Gets the links out of the node evaluated
        linksOut = links[links[SWWM_C.IN_NODE] == nodeAux].copy()

        if(linksOut.shape[0] > 1):
            nodesDecision.append(nodeAux) #Saves the last decision of this path

        #Orders and select the links by largest diameter/full height and length (although pumps have length 0 )
        if linksOut.empty:
            endPoint = True
        else:
            linkOut = linksOut.sort_values(by=[SWWM_C.MAX_Q,SWWM_C.DIAM], ascending=False).iloc[0]

            #if the link selected was already selected for this iniNode then it is in a loop
            if linkOut.name in pipesPath:
                
                #If it does not have history is because is rerouting coz it went to an outlet
                if not nodesDecision:
                    print("Error")
                else:
                    linkOut,pipesPath,nodesDecision = reRoute(nodesDecision,links, pipesPath)

            nodeAux, pipesPath = addLinkToPath(links,linkOut,pipesPath)
         
            
    return pipesPath, nodesDecision, nodeAux


#Could be replaced by using this swmmio.utils.functions.find_network_trace()
def getPathToWTP(WTP_Tank:str,linksDF:'pd.DataFrame',leaves)-> dict:
    """
        Get all paths from leaves (end nodes or the network) to a specific node
    Args:
        WTP_Tank (str): id name of the WRRF
        linksDF (pd.DataFrame): links of the network and their attributes
        endPoints (_type_): _description_

    Returns:
        _type_: _description_
    """    

    #linksDF[SEL] = False

    paths = {}

    # Repeat for each point
    for iniNode in leaves:

        pathsAux = []
        decisionsN = []
        
        #find the path for a point to the treatment plant
        pathsAux, decisionsN, endNode = lookForPath(WTP_Tank,iniNode,linksDF,pathsAux,decisionsN)

        while (endNode != WTP_Tank):

            try:
                linkOut,pathsAux,decisionsN = reRoute(decisionsN,linksDF, pathsAux)

            except Exception as e:
                print(iniNode, " ", e)
                paths[iniNode] = pathsAux
                break

            nodeAux, pathsAux = addLinkToPath(linksDF,linkOut,pathsAux)

            #Looks for the path again
            pathsAux,decisionsN,endNode = lookForPath(WTP_Tank,nodeAux,linksDF,pathsAux,decisionsN)

        #Saves the list of pipes
        paths[iniNode] = pathsAux
            
    return paths


def findMainFlowPath(initialNode:str,inpPath:str)-> 'pd.DataFrame':
    """
        Selects pipe by pipe going upstream from the initial node, selecting the pipe with largest flow.
        Assumes the pipes direction is correct (outnode is downstream and innode upstream)
    Args:
        initialNode (str): name of the initial node (i.e. WRRF)
        inpPath (str): path of the inp of the network

    Returns:
        pd.DataFrame: links selected as part of the trunk with name as index and its characteristics and connecting nodes as attributes. 
                      ordered downstream to upstream
    """
    nodeEval = initialNode
    trunk = []
    trunkDF = None

    try:
        
        linksNetwork = gnfs.getsNetworksLinks(inpPath) #all links of the network with name as index and its characteristics and connecting nodes as attributes.

        while nodeEval is not None:

            previousPipes = linksNetwork[linksNetwork[SWWM_C.OUT_NODE]==nodeEval].copy() #gets all the pipes discharging to the evaluated node

            if previousPipes.shape[0] != 0: 

                dfTSprePipes = gnfs.getFlowTimeSeries(previousPipes.index.to_list(),inpPath) #gets the time series of all connected pipes to the node evaluated

                pipeTrunk = dfTSprePipes.mean().idxmax() # Calculate the mean of each pipe and gets the pipe with the largest mean

                trunk.append(pipeTrunk) #adds the selected pipe to the list of the trunk

                nodeEval = previousPipes.loc[pipeTrunk,SWWM_C.IN_NODE] #Gets the  name of the inital node of the pipe selected

            else:
                nodeEval = None

        trunkDF = linksNetwork.loc[trunk].copy() #gets the attributes of the pipes in the trunk and its ordered downstream to upstream

    except Exception as e:

        print("Error finding the main water path: ", e)


    return trunkDF, trunk