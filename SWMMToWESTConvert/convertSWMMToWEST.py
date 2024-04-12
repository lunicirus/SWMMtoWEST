import math
import numpy as np
from datetime import datetime, timedelta

import SWMMToWESTConvert.SWMMtoWESTConstants as STW_C
import SWMMToWESTConvert.SWMM_InpConstants as SWMM_C

#hydraulic constants
VISCO = 1.0035*(10**-6)*60*60*24 #m2/d
GRAVITY = 9.81*(60*60*24)**2  #m/d2 

FLOW_PER_PERSON = 0.4  #m3/d as in WEST

class ConvertionException(Exception):
    pass


def convertManningToM(manning:float)->float:
    """
        Converts manning factor of pipe roughness to absolute roughness in meters. 
        Aproximation using Webber, N.B. (1971) Fluid Mechanics for Civil Engineers. Chapman & Hall.
        The approximation gives ft which are then converted to meters.
    Args:
        manning (float): Manning factor of pipe roughness
    Returns:
        float: Absolute roughness in meters
    """    
    m = (manning*26)**6/3.28 # m

    return m

def convertMeanSWMMFlowToNPeopleWEST(averageDWF:float)->int:
    """
        Converts an mean dry weather flow in m3/s to get the equivalent number of people, using a fix flow per person in m3/d.
        In SWMM units are m3/s, and in WEST are in m3/d.
    Args:
        averageDWF (float): mean dry weather flow in m3/s
    Returns:
        int: number of people equivalent to the averageDWF.
    """    
    averageM3d = averageDWF * 86400 #SWMM 'average' is in m3/s 
    npeople = math.ceil(averageM3d / FLOW_PER_PERSON) # flow per person is in m3/d as it is west

    return npeople

def convertTimeSeriesIntoDWF(ts:'pd.Series')->tuple[list[str],float]:
    """
        Calculates the average flow per hour of the day and normalises it using the ts total average flow.
        Discarts the first day of the ts from the calculation, as it considers the stabilisation period of the flow modeling
    Args:
        ts (pd.Series): Time series of flows in order (i.e., the first day starts at hour 0 and finises at hour 23).
    Returns:
        tuple[list[str],float]: _description_ TODO
    """    
    initialDate = ts.index[0]
    initialDateEvaluation = initialDate + timedelta(days=1) #it assumes that flow gets stable after one day!!
        
    dryWeather = ts[initialDateEvaluation:]
        
    totalMean = dryWeather.mean()
    hourly_pattern = dryWeather.groupby(dryWeather.index.hour).mean()
    
    assert list(hourly_pattern.index) == list(range(24)) #assumess that the TS is in order 
        
    normalized_HP = hourly_pattern / totalMean
    NHP_stringList = list(map(str, normalized_HP))

    return NHP_stringList, totalMean


def calculateSewerValues(pipeSection:'pd.DataFrame',shapeType: str)->tuple[float,float,float,int]:
    """
        Calcutes the atributes of the tanks in series to represent the sewer section. Using Kalinin-Miljukov.
        Asumes RECT pipes have the same geom 2 than geom 1 TODO
    Args:
        pipeSection (pd.DataFrame): Pipes in the pipe section. rows are pipes and columns the attributes.
        shapeType (str): Shape of the pipe section e.g., circular, rect_closed.
    Returns:
        tuple[float,float,float,int]: Area of the tanks. Max volumen of the tanks. Retention time of one tank. Number of tanks.
    """    
    length = pipeSection[SWMM_C.LEN].sum()  #m
    diam = np.average(pipeSection[SWMM_C.DIAM], weights=pipeSection[SWMM_C.LEN]) #m
    slope = np.average(pipeSection[STW_C.SLOPE], weights=pipeSection[SWMM_C.LEN])
    roughness = np.average(pipeSection[SWMM_C.ROUG], weights=pipeSection[SWMM_C.LEN]) # manning       
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
    
    return areaTank, Volmax, k, n

def createSewerWEST(pipeSection:'pd.DataFrame',name:str,shapeType:str,tankIndex:int)-> tuple[dict,int]:
    """
        Creates a dictionary with all the required attributes of a sewer section in WEST. 
        A sewer in WEST is represented with various tank in series mmodels with the same characterisitcs.
    Args:
        pipeSection (pd.DataFrame): Characteristics of the sewer section.
        name (str): Name of the sewer section.
        shapeType (str): Shape of the sewer section e.g. circular, rectangular.
        tankIndex (int): Initial tank series number to be used for the sewer section. E.g. if the entired model already has 20 tank in series, this should be 21.
    Returns:
        tuple[dict,int]: dictionary representing the sewer section in WEST. The number of tank in series in the sewer section.
    """    
    areaTank, Volmax, k, n = calculateSewerValues(pipeSection,shapeType)
        
    pipe = {}
    pipe[STW_C.NAME] = name
    pipe[STW_C.AREATANK] = areaTank #m2
    pipe[STW_C.VMAX] = Volmax #m3
    pipe[STW_C.K] = k #d
    pipe[STW_C.TANK_INDEXES] = [*range(tankIndex,tankIndex+n,1)]
    
    return pipe, n

def createCatchmentWEST(name:str, element:dict, timePatterns:dict, isEnd:bool=True)->dict:
    """
        Creates a dictionary with all the required attributes of a Catchment model in WEST. 
        Converst flow and area values from SWMM to the attributes and units used in WEST.
    Args:
        name (str): Name of the catchment.
        element (dict): Values from SWMM to be used or converted to create the catchment. #TODO check the type
        timePatterns (dict): All time patterns to be used in the aggregated model. #TODO check the type
        isEnd (bool, optional): True if the catchment should be placed at the end of the pipe section, False otherwise. Defaults to True.
    Returns:
        dict: dictionary representing a catchment in WEST.
    """    
    catchment = {}

    pos = '' if isEnd else STW_C.BEFORE_CATCHMENT
    catchment[STW_C.NAME_CATCH] = name + STW_C.SECTION_CATCHMENT + pos
    catchment[STW_C.END] = isEnd
    
    #Attributes of catchments (equal to SWMM) ----------------------------
    catchment[STW_C.AREA] = element[SWMM_C.AREA] * 10000 #converts from ha to m2
    
    #Attributes from DWF----------------------------------------
    averageDWF = element[SWMM_C.INFLOW_MEAN] #m3/s
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
    
    
    return catchment

def createInputWEST(name:str,input:str,tsInputs:'pd.DataFrame')->dict:
    """
        It creates a catchment WEST model (pattern, #people, flow per person) using as input the time series of one or more pipes. 
    Args:
        name (str): Name of the pipe section at which the model should be connected.
        input (str): Names of the time series/ pipes to be used as input
        tsInputs (pd.DataFrame): All time series to be converted to inputs in the complete WEST model 
    Returns:
        dict: Catchment WEST model.
    """
    inputWEST = {}
    npeople = None
    tPatternP= None

    inputWEST[STW_C.NAME_CATCH] = name + STW_C.SECTION_CATCHMENT + STW_C.INPUT_CATCHMENT

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

def getPathElements(dfs:list['pd.DataFrame'],elements:'pd.DataFrame', initialElements:dict,
                    timePatterns:dict[list],tSDischarging:'pd.DataFrame', firstPipe:str)->tuple[list[dict],list[dict]]:
    """
        Converts the pipe sections into list of tank in series models and the flowelements into a list of catchment models.
        The model of each pipe section has the name "initial-final pipe", the slope, diameter, and total length.
        The slope and diameter are the mean weigthed by length of the composing pipes, to calculate the area it assumes the most common shape.
    Args:
        dfs (list[pd.DataFrame]): Sections of the path ordered from upstream to downstream, each dataframe is a section.
        elements (pd.DataFrame): Flow elements of the path.
        initialElements (dict): Flow elements at the initial node of the path.
        timePatterns (dict[list]): Time patterns of the network.
        tSDischarging (pd.DataFrame): Time series discharging into the path.
        firstPipe (str): The name of the first pipe of the path.
    Returns:
        tuple[list[dict],list[dict]]: list of tank in series models and catchments models of the path.
    """    
    pipesSection = []
    catchments= []
    
    tankIndex = 1
    firstSection = True
    
    for df in dfs:  #Elements are in order from upstream to downstream

        dfClean = df[df[SWMM_C.LEN].notna() & (df[SWMM_C.LEN] != 0)].copy() #Removes elements with length zero (pumps, orifices or weirs)
         
        if dfClean.empty:
            raise 

        mostCommonShape = dfClean[SWMM_C.SHAPE].value_counts().idxmax()
        name = dfClean.iloc[0,0] + " - " + dfClean.iloc[-1,0]
        
        #Creates and adds the pipe section to the list
        sewerSect, n = createSewerWEST(dfClean,name,mostCommonShape,tankIndex) 
        pipesSection.append(sewerSect)
        tankIndex += n
                
        #Creates and adds a catchment and/or and dwf to their list if they are connected at the beggining of the path
        if firstSection and initialElements:
            catchment = createCatchmentWEST(name, initialElements,timePatterns,False) #Cathcments are named as the name the pipe section connected to
            catchments.append(catchment)
            
            firstSection = False
         
        #Creates and adds a catchment and/or a dwf to their list if they are connected to the end part of the sewer section
        pipeEvaluated = dfClean.iloc[-1][SWMM_C.NAME]
        if pipeEvaluated in elements.index:
            element = elements.loc[pipeEvaluated].copy()
            catchments = createCatchmentsFromFlowElement(element, timePatterns, tSDischarging, catchments, name)
    
    if not dfs:
        element = elements.iloc[0].copy()
        catchments = createCatchmentsFromFlowElement(element, timePatterns, tSDischarging, catchments, firstPipe)
            
    print("----------------------------")
    print("Final number of pipe sections ", len(pipesSection))
    print("Final number of catchments: ", len(catchments))
    
    if pipesSection:
        print("Final number of tanks in series:", pipesSection[-1][STW_C.TANK_INDEXES][-1])
                            
    return pipesSection, catchments

def createCatchmentsFromFlowElement(element:'pd.Serie', timePatterns:dict[list], tSDischarging:'pd.DataFrame', 
                                   catchments:list[dict], pipeSectionName:str)->list[dict]:
    """
        Looks for elements associated to the pipeEvaluated and if there are it adds new catchment models to the catchments list.
    Args:
        elements (pd.DataFrame): Flow elements of the path.
        timePatterns (dict[list]): Time patterns of the network.
        tSDischarging (pd.DataFrame): Time series discharging into the path.
        catchments (list[dict]): List of catchments in which to add the new catchments models.
        pipeEvaluated (str): Name of the last pipe of the pipe section where the possible flow elements of the section were aggregated.
        pipeSectionName (str): Name of the pipe section being modelled (i.e.,"first pipe - last pipe")
    Returns:
        list[dict]: list of catchment models updated with the models of the pipe section evaluated.
    """    
    tsInput = element[STW_C.MODELED_INPUT]

    #If the ts is not empty it creates an input object
    if tsInput is not None:
        input = createInputWEST(pipeSectionName, tsInput, tSDischarging)
        catchments.append(input)
    else:
        print("Connected pipe did not have flow")

    element.drop(labels=STW_C.MODELED_INPUT,inplace=True) #TODO why do i need to drop it?
    element.fillna(0,inplace=True)
                
    #if any of the others values are different from zero or null then it creates a catchment object      
    if ~((element == 0.0) | element.isna()).all():
        catchment = createCatchmentWEST(pipeSectionName, element, timePatterns) #Cathcments are named as the name the pipe section connected to
        catchments.append(catchment)

    return catchments


#------------------------------------------------Outdated--------------------------------------------------------

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

                sewerSect, name, n = createSewerWEST(group,shapeType,tankIndex) #Creates and adds the pipe section to the list
                pipesSection.append(sewerSect)
                tankIndex += n
                
                #Creates and adds a catchment and/or and dwf to their list if they are connected at the beggining of the path
                if firstSection and (initialElements is not None):
                    catchment = createCatchmentWEST(name, initialElements,timePatterns,False) #Cathcments are named as the name the pipe section connected to
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
                        catchment = createCatchmentWEST(name, element, timePatterns) #Cathcments are named as the name the pipe section connected to
                        catchments.append(catchment)
    
            
    print("----------------------------")
    print("Final number of pipe sections: ", len(pipesSection))
    print("Final number of catchments: ", len(catchments))
    print("Final number of tanks in series:", pipesSection[-1][STW_C.TANK_INDEXES][-1])
                            
    return pipesSection, catchments
