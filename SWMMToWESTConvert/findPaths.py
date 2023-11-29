
import SWMMToWESTConvert.SWMM_InpConstants as SWWM_C


#Adds the linkOut to the path 
def addLinkToPath(links,linkOut,pipesPath):
    
    linkOutName = linkOut.name
    
    #links.at[linkOutName, SEL]= True
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

def lookForPath(WTP_Tank,nodeAux,links,pipesPath,nodesDecision):
    
    endPoint = False
    
    while (nodeAux != WTP_Tank) and (not endPoint):
        
        #Gets the links out of the node evaluated
        linksOut = links[links[SWWM_C.IN_NODE] == nodeAux]

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
def getPathToWTP(WTP_Tank,linksDF,endPoints):

    #linksDF[SEL] = False

    paths = {}

    # Repeat for each point
    for iniNode in endPoints:

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
        
    #linksDF.drop(columns=[SEL],inplace=True)
    
    return paths
