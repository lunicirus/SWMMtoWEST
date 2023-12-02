
import pandas as pd
import meassuresConstants as MC
import PCSWMMConstants as PSC 
import graphConstants as GC
import WESTConstants as WC


#Columns separated by their units
flowsLs = [MC.LIMOILOU_ME_SANI,MC.LIMOILOU_ME_PLUV,MC.BEAUPORT_ME_1,MC.BEAUPORT_ME_2,MC.BEAUPORT_ME_3,
            MC.STSACREMENT_ME_AF,MC.STSACREMENT_ME_EF,MC.STSACREMENT_ME_R,MC.STSACREMENT_ME_D]

flowsm3h = [MC.ESTA_ME,MC.PASCAL_ME,MC.NO_ME,MC.NO_ME_PLUV]

#Some values are in l/s and some in m3/h
#Returns a dataframe with the values in m3/h  
def processMeassuredData(file):

    # create a dataframe with the data from the file 
    flowVals = pd.read_csv(file, delimiter = ',',index_col=['Date'])
    flowVals.index = pd.to_datetime(flowVals.index, format='%d/%m/%y %H:%M')
    #convert string values to numeric replace invalid values as null
    flowVals= flowVals.apply(pd.to_numeric, errors='coerce')

    #transformation of the units and renaming the columns
    dfLs = flowVals[flowsLs].copy()
    dfFlowsLsTom3h= dfLs*3.6
    dfFlowsLsTom3h.columns = dfFlowsLsTom3h.columns.str.replace('l/s', 'm³/h')
    #joining dataframes to create the original complete dataframe
    dfFlowsm3h = flowVals[flowsm3h].copy()
    dfFlowsm3h = dfFlowsm3h.join(dfFlowsLsTom3h).copy()

    #checks that the join was properly done
    assert dfFlowsm3h.shape[0] == flowVals.shape[0]
    assert dfFlowsm3h.shape[1] == flowVals.shape[1]

    #Cleaning error values
    dfFlowsm3h[dfFlowsm3h < 0] = 0 #replace negative values with 0

    return dfFlowsm3h


# assumes values are in CMS, m3/s
# returns values in m3/h
def getModelData(file,startDate,endDate,renameDict=None):

    # create a dataframe with the data from the file 
    flowModelVals = pd.read_csv(file, delimiter = ',')
    flowModelVals.columns = flowModelVals.columns.str.replace(' ', '') #Remove white spaces from columns names
    
    #Combines and formats the date and time. And set it as the index
    flowModelVals[GC.LONGDATE_LBL] = flowModelVals[PSC.DATE_LBL] + " " + flowModelVals[PSC.TIME_LBL] #concat date and time columns
    flowModelVals.drop(columns=[PSC.DATE_LBL, PSC.TIME_LBL],inplace=True) #removes redundant columns
    flowModelVals[GC.LONGDATE_LBL]= pd.to_datetime(flowModelVals[GC.LONGDATE_LBL],format='%m/%d/%Y %H:%M:%S') # formats date
    flowModelVals.set_index(GC.LONGDATE_LBL,inplace=True)

    # convert values to m3/h
    flowModelValsm3h = flowModelVals*3600

    # Removes values outside the evaluated period
    flowModelValsm3h = flowModelValsm3h[(flowModelValsm3h.index >= startDate)&(flowModelValsm3h.index < endDate)]

    # renames columns
    #flowModelVals.rename(columns={LIMOILOU_COL: "Limoilou", PASCAL_COL: "Pascal", STSACRA_C:"St-Sacrement"},inplace=True)
    
    if renameDict is not None:
        flowModelValsm3h.rename(columns=renameDict,inplace=True)
    
    return flowModelValsm3h


#Assumes values come in m3/d, it should not have the row of units
#Returns values in m3/h
def getDFWESTResults(file,startDate,endDate,dictRenames=None):

    WTP_WEST_Results = pd.read_csv(file, delimiter = ',')

    #In case the simulation in WEST was not started in day 0, it shifts the whole dataset to start at 0
    WTP_WEST_Results[WC.TIME_WEST] = WTP_WEST_Results[WC.TIME_WEST]-WTP_WEST_Results[WC.TIME_WEST].min() 
    
    # Converts the "Days" column to timedelta objects (days) 
    WTP_WEST_Results[WC.TIME_WEST] = pd.to_timedelta(WTP_WEST_Results[WC.TIME_WEST], unit='D')
    # Calculates the date base on the starting date 
    WTP_WEST_Results[GC.DATE_LBL] = startDate + WTP_WEST_Results[WC.TIME_WEST] 
    
    #Removes extra records if they are outside the range being evaluated 
    WTP_WEST_ResultsCut= WTP_WEST_Results[WTP_WEST_Results[GC.DATE_LBL]< endDate]
    #Removes unnecesary columns and set the index
    WTP_WEST_ResultsCut = WTP_WEST_ResultsCut.drop(columns=[WC.TIME_WEST]).set_index(GC.DATE_LBL)
    
    # pass from m3/d to m3/h
    dfWEST = WTP_WEST_ResultsCut /24

    #Renames columns for the graph
    dfWEST = renameWEST(dfWEST.copy())
   
    return dfWEST


def renameWEST(dfWEST, dictRenames=None):

    if dictRenames is None:
        dfWEST.columns = dfWEST.columns.str.extract(r'\.\w+_(\d+)\.Q_(\w+)').apply(lambda x: f'{x[0]} ({x[1]})', axis=1)
    else:
        dfWEST.rename(columns=dictRenames,inplace=True)

    return dfWEST

def sortColumnsWEST(dfWEST):

    sorted_columns = sorted(dfWEST.columns, key=lambda x: (int(x.split()[0]), x.split()[1]))

    dfWEST = dfWEST[sorted_columns]

    return dfWEST

def checkAverageColumnsIncrements(df):

    num_columns = df.shape[1]

    for column_index in range(1, num_columns):

        current_mean = df.iloc[:, column_index].mean()
        previous_mean = df.iloc[:, column_index - 1].mean()

        if (not current_mean > previous_mean) and ((previous_mean-current_mean)*100/previous_mean > 0.5):
            print("The column with error is: ",column_index)
            return False

    return True


def checkCorrectFlowWEST(df):

    df = sortColumnsWEST(df)

    #remove the first data points coz is instable
    df = df.iloc[20:,:]

    return checkAverageColumnsIncrements(df)

    

    