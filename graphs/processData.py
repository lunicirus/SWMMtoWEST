
import pandas as pd
import graphs.meassuresConstants as MC
import graphs.PCSWMMConstants as PSC 


#Columns separated by their units
flowsLs = [MC.LIMOILOU_ME_SANI,MC.LIMOILOU_ME_PLUV,MC.BEAUPORT_ME_1,MC.BEAUPORT_ME_2,MC.BEAUPORT_ME_3,
            MC.STSACREMENT_ME_AF,MC.STSACREMENT_ME_EF,MC.STSACREMENT_ME_R,MC.STSACREMENT_ME_D]

flowsm3h = [MC.ESTA_ME,MC.PASCAL_ME,MC.NO_ME,MC.NO_ME_PLUV]


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
def getModelData(file):

    # create a dataframe with the data from the file 
    flowModelVals = pd.read_csv(file, delimiter = ',')
    flowModelVals.columns = flowModelVals.columns.str.replace(' ', '') #Remove white spaces from columns names
    #flowModelVals.rename(columns={LIMOILOU_COL: "Limoilou", PASCAL_COL: "Pascal", STSACRA_C:"St-Sacrement"},inplace=True)
    flowModelVals.rename(columns={WTP_COL: WTP, STSACRA_TO_LIMOLIOU_COL: STSACRA_TO_LIMOLIOU, PASCAL_COL:PASCAL},inplace=True)
    
    #Combines and formats the date and time. And set it as the index
    flowModelVals["LongDate"] = flowModelVals["Date"]+" "+flowModelVals["Time"] #concat date and time columns
    flowModelVals.drop(columns=['Date', 'Time'],inplace=True) #removes redundant columns
    flowModelVals["LongDate"]= pd.to_datetime(flowModelVals["LongDate"],format='%m/%d/%Y %H:%M:%S') # formats date
    flowModelVals.set_index("LongDate",inplace=True)

    # convert values to m3/h
    flowModelValsm3h=flowModelVals*3600
    flowModelValsm3h = flowModelValsm3h.add_suffix(MOD_SUFFIX)
    
    return flowModelValsm3h