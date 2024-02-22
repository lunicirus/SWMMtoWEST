import math
import numpy as np
from datetime import datetime, timedelta

import SWMMToWESTConvert.SWMMtoWESTConstants as STW_C
import SWMMToWESTConvert.SWMM_InpConstants as SWMM_C

#hydraulic constants
VISCO = 1.0035*(10**-6)*60*60*24 #m2/d
GRAVITY = 9.81*(60*60*24)**2  #m/d2 


FLOW_PER_PERSON = 0.4  #m3/d as in WEST. In SWMM units are m3/s 

#Aproximation using
#Webber, N.B. (1971) Fluid Mechanics for Civil Engineers. Chapman & Hall
#Result is in ft and then converted to meters
def convertManningToM(manning):

    m = (manning*26)**6/3.28 # m

    return m

#Converts the m3/s of SWMM to m3/d of WEST and divides per the flow per person constant to get the number of people
def convertMeanSWMMFlowToNPeopleWEST(averageDWF):

    averageM3d = averageDWF * 86400 #SWMM 'average' is in m3/s 
    npeople = math.ceil(averageM3d / FLOW_PER_PERSON) # flow per person is in m3/d as it is west

    return npeople

#Removes the first day of the ts as it considers the stabilisation period of the flow modeling
#With the rest of the time series, calculates the average flow per hour of the day and normalises it using the ts total average flow 
def convertTimeSeriesIntoDWF(ts):

    initialDate = ts.index[0]
    initialDateEvaluation = initialDate + timedelta(days=1) #it assumes that flow gets stable after one day!!
        
    dryWeather = ts[initialDateEvaluation:]
        
    totalMean = dryWeather.mean()
    hourly_pattern = dryWeather.groupby(dryWeather.index.hour).mean()
    
    assert list(hourly_pattern.index) == list(range(24)) #assumess that the TS is in order (starts in hour 0 and finish in 23)
        
    normalized_HP = hourly_pattern / totalMean
    NHP_stringList = list(map(str, normalized_HP))

    return NHP_stringList, totalMean

#Asumes RECT pipes have the same geom 2 than geom 1
def calculateSewerValues(group,shapeType: str):
    
    length = group[SWMM_C.LEN].sum()  #m
    name = group.iloc[0,0] + " - " + group.iloc[-1,0]
    diam = group[SWMM_C.DIAM].min()  #m           #they are all the same
    slope = np.average(group[STW_C.SLOPE], weights=group[SWMM_C.LEN])
    roughness = np.average(group[SWMM_C.ROUG], weights=group[SWMM_C.LEN]) # manning       
    roughness = convertManningToM(roughness)
    Lc = 0.4 * diam / slope   #m
    n1 = length/Lc  
    n = round(n1) if n1 >= 1 else 1
    ltank = length/n  #m
    
    c = (2*GRAVITY*diam*slope)**0.5    #m/d 
    a = 2.51*VISCO/(diam*c) # adimensional (m2/d / m2/d)
    b = roughness/(3.71*diam) #adimensional (m/m)

    #m2
    if shapeType == SWMM_C.CIRC:
        area = math.pi * (diam**2)/4
    elif (shapeType == SWMM_C.REC) or (shapeType == SWMM_C.REC2):
        area = diam**2
    else:
        assert True
        area = 0

    Qmax = area*(-2*math.log(a+b)*c) if slope > 0 else 0 # m3/d
    
    k = 0.64 * ltank* (diam**2)/ Qmax
    Volmax = Qmax*k
    areaTank = ltank*diam # TODO!!!!!
    
    return name, areaTank, Volmax, k, n

#assigns the properties to the sewer section 
def createSewerWEST(group,shapeType,tankIndex):
    
    name, areaTank, Volmax, k, n = calculateSewerValues(group,shapeType)
        
    pipe = {}
    pipe[STW_C.NAME] = name
    pipe[STW_C.AREATANK] = areaTank #m2
    pipe[STW_C.VMAX] = Volmax #m3
    pipe[STW_C.K] = k #d
    pipe[STW_C.TANK_INDEXES] = [*range(tankIndex,tankIndex+n,1)]
    
    return pipe, name, n

#Cathcments are named as the name the pipe section connected to 
#Converst flow and area to the values from SWMM to the units used in WEST
def createCatchmentWEST(name, element, timePatterns, isEnd=True):

    catchment = {}
    catchment[STW_C.NAME] = name
    
    #Attributes of catchments (equal to SWMM) ----------------------------
    catchment[STW_C.AREA] = element[SWMM_C.AREA] * 10000 #converts from ha to m2
    
    #Attributes from DWF----------------------------------------
    averageDWF = element[SWMM_C.INFLOW_MEAN]
    timePatternDWF = element[SWMM_C.INFLOW_PATTERNS]
    
    if (not math.isnan(averageDWF)) & (averageDWF != 0):
        npeople = convertMeanSWMMFlowToNPeopleWEST(averageDWF)
        tPatternP = timePatterns[timePatternDWF]
    else:
        npeople = None
        tPatternP = None
    
    catchment[STW_C.N_PEOPLE] = npeople
    catchment[STW_C.FLOWRPERPERSON] = FLOW_PER_PERSON
    catchment[STW_C.TIMEPATTERN] = tPatternP
    
    #Attributes from direct flows --------------------------------
    catchment[STW_C.DF_BASELINE] = element[SWMM_C.DFLOW_BASELINE] * 86400 # convert it from m3/s to m3/d
    #directFlow[DDFLOW_TIMES] = timeSeries
    #directFlow[DFLOW_SFACTOR] = Sfactor
    
    #Aux attributes ---------------------------------------------
    catchment[STW_C.END] = isEnd
    
    return catchment

#It creates a catchment element in west with the timeseries of the input
def createInputWEST(name:str,input:str,tsInputs:'pd.DataFrame')->dict:
    """TODO 

    Args:
        name (str): _description_
        input (str): _description_
        tsInputs (pd.DataFrame): _description_

    Returns:
        dict: _description_
    """
    inputWEST = {}
    npeople = None
    tPatternP= None

    inputWEST[STW_C.NAME] = name + "[input]"

    #Catchment attributes not used for representing an input -----------------
    inputWEST[STW_C.AREA] = 0
    inputWEST[STW_C.DF_BASELINE] = 0
    
    #converts the time series into a pattern and number of people
    if input:
        columns_to_sum = input.split(',') 
        result_series = tsInputs[columns_to_sum].sum(axis=1) 
        tPatternP, averageDWF = convertTimeSeriesIntoDWF(result_series)
        npeople = convertMeanSWMMFlowToNPeopleWEST(averageDWF)
    
    inputWEST[STW_C.N_PEOPLE] = npeople
    inputWEST[STW_C.TIMEPATTERN] = tPatternP
    
    
    #Aux attributes ------------------------------
    inputWEST[STW_C.FLOWRPERPERSON] = FLOW_PER_PERSON
    inputWEST[STW_C.END] = True
    
    return inputWEST

#Each pipe section has the name as the initial and final node of the composing pipes 
# it has the mean of the slopes of the composing pipes, the mean (and only) diameter of the group, and the total length 
def getPathElementsDividingByDiam(dfs,elements, initialElements,timePatterns,tSConnectedPoints)->tuple[list[dict],list[dict]]:
    
    pipesSection = []
    catchments= []
    
    tankIndex = 1
    firstSection = True
    
    #Elements are in order from upstream to downstream
    for df in dfs:
        #Classifies consecutive pipes with the same diameter
        groups = df.groupby((df[SWMM_C.DIAM] != df[SWMM_C.DIAM].shift()).cumsum())

        for i, groupDiameter in groups:
            
            shapes = groupDiameter.groupby(SWMM_C.SHAPE,sort=False)
            
            length = groupDiameter[SWMM_C.LEN].sum()
            if length == 0:
                print("Pump, Orifice or Weir")
                continue
            
            for shapeType, group  in shapes:

                #print("pipe: ",group.iloc[0,0], " - ", group.iloc[-1,0])
                
                #Creates and adds the pipe section to the list
                sewerSect, name, n = createSewerWEST(group,shapeType,tankIndex) 
                pipesSection.append(sewerSect)
                tankIndex += n
                
                #Creates and adds a catchment and/or and dwf to their list if they are connected at the beggining of the path
                if firstSection and (initialElements is not None):
                    catchment = createCatchmentWEST(name, initialElements,timePatterns,False)
                    catchments.append(catchment)
                    
                    firstSection = False
                
                #Creates and adds a catchment and/or a dwf to their list if they are connected to the end part of the sewer section
                connectingPipe= group.iloc[-1,0]
                if connectingPipe in elements.index:

                    #check that the data is not empty or zero before creating a catchment
                    element = elements.loc[connectingPipe].copy()
                    tsInput = element[STW_C.MODELED_INPUT]

                    #If the ts is not empty it creates an input object
                    if tsInput is not None:
                        input = createInputWEST(name, tsInput,tSConnectedPoints)
                        catchments.append(input)

                    #if any of the others values are different from zero or null then it creates a catchment object
                    element.drop(labels=STW_C.MODELED_INPUT,inplace=True)
                    element.fillna(0,inplace=True)
               
                    if ~((element == 0.0) | element.isna()).all():
                        catchment = createCatchmentWEST(name, element, timePatterns)
                        catchments.append(catchment)
    
            
    print("----------------------------")
    print("Final number of pipe sections ", len(pipesSection))
    print("Final number of catchments: ", len(catchments))
    print("Final number of tanks in series:", pipesSection[-1][STW_C.TANK_INDEXES][-1])
                            
    return pipesSection, catchments


#Each pipe section has the name as the initial and final node of the composing pipes 
# it has the mean of the slopes of the composing pipes, the mean diameter of the group, and the total length 
# to calculate the area it assumes the most common shape
def getPathElements(dfs,elements, initialElements,timePatterns,tSConnectedPoints):
    
    pipesSection = []
    catchments= []
    
    tankIndex = 1
    firstSection = True
    
    #Elements are in order from upstream to downstream
    for df in dfs:

        #Removes elements with length zero (pumps, orifices or weirs)
        df = df[df[SWMM_C.LEN].notna() & (df[SWMM_C.LEN] != 0)].copy()

        #Obtains the most common shape 
        mostCommonShape = df[SWMM_C.SHAPE].value_counts().idxmax()
        
        #Creates and adds the pipe section to the list
        sewerSect, name, n = createSewerWEST(df,mostCommonShape,tankIndex) 
        pipesSection.append(sewerSect)
        tankIndex += n
                
        #Creates and adds a catchment and/or and dwf to their list if they are connected at the beggining of the path
        if firstSection and initialElements:
            catchment = createCatchmentWEST(name, initialElements,timePatterns,False)
            catchments.append(catchment)
            
            firstSection = False
         
        #Creates and adds a catchment and/or a dwf to their list if they are connected to the end part of the sewer section
        connectingPipe= df.iloc[-1,0]
        if connectingPipe in elements.index:

            element = elements.loc[connectingPipe].copy()
            tsInput = element[STW_C.MODELED_INPUT]

            #If the ts is not empty it creates an input object
            if tsInput is not None:
                input = createInputWEST(name, tsInput, tSConnectedPoints)
                catchments.append(input)

            element.drop(labels=STW_C.MODELED_INPUT,inplace=True)
            element.fillna(0,inplace=True)
            
            #if any of the others values are different from zero or null then it creates a catchment object      
            if ~((element == 0.0) | element.isna()).all():
                catchment = createCatchmentWEST(name, element, timePatterns)
                catchments.append(catchment)
    
            
    print("----------------------------")
    print("Final number of pipe sections ", len(pipesSection))
    print("Final number of catchments: ", len(catchments))
    print("Final number of tanks in series:", pipesSection[-1][STW_C.TANK_INDEXES][-1])
                            
    return pipesSection, catchments
