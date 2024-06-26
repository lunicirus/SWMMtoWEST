#Variables to check that the models have
#Descriptions of the models 
SEWER = 'Sewer'
CATCHMENT = 'Catchment'
CONNECTOR = 'Connector_info'
COMBINER = 'Two combiner'

#Start of the models' names
XML_SEWER_NAMES =  'Sew_'
XML_CATCH_NAMES = 'Catchment_'
XML_CONN_NAMES = 'Connector_info_'
XML_COMB_NAMES = 'Well_'

#Names of the models' attributes
XML_AREA_SEWER = '.A'
XML_VMAX_SEWER = '.V_Max'
XML_K_SEWER = '.k'

XML_AREA_CATCH = '.TotalArea'

XML_CONN_VELCLASS = '.Vs_limit'
XML_CONN_VELMINCLASS = '.Vs_limit_min'

XML_DWF_NPEOPLE = '.Inhabitants' #Associated to a catchment in WEST
XML_DWF_QPERPERSON = '.WastewaterPerIE' #Associated to a catchment in WEST
XML_DWF_Q_INDUSTRY = '.Q_Industry'
XML_DWF_CUSTOMFLOWPATTERN = '.DWF.CustomFlow(H' #Associated to a catchment in WEST

# XML_DWF_INFILTRATION = '.Infiltration' #Associated to a catchment in WEST | it is repeated directly to the catchment i.e., .Infiltration 

#NOT BEING USED YET---------------------------------------
# XML_CATH_YEARLYEVAPO = '.YearlyEvaporation'  
# XML_CATH_ACCMAXAREAL = '.M_acc_max_areal'
# XML_ISTROM_AREA = '.IndirectStorm.A'
# XML_ISTROM_QMAX = '.IndirectStorm.Q_Max'
# XML_ISTROM_VMAX ='.IndirectStorm.V_Max'
# XML_ISTROM_KOUT = '.IndirectStorm.k_out'
# XML_WRUNOFF_MAXWETTINGLOSSES = '.FRunoff.MaxWettingLosses'#Associated to a catchment in WEST | it is repeated directly to the catchment i.e., .MaxWettingLosses 

# XML_SEWER_DRATE = '.D_rateSARS'
# XML_SEWER_KSAT = '.K_sat'
# XML_SEWER_RESUSPENK = '.k_resuspension'  
# XML_SEWER_RESUSPENN = '.n_resuspension' 


XML_MODEL_PROP_NAME = 'InstanceDisplayName'

#Elements of the XML
XML_QUANTIY = 'Quantity'
XML_LINK = 'Link'

#Values used for the properties
XML_PROPS = 'Props'
XML_PROP = 'Prop'
XML_NAME = 'Name'
XML_VAL = 'Value'

#Properties of links
XML_FROM = 'From'
XML_TO = 'To'
XML_TYPE = 'Type'
XML_DATA = 'Data'
XML_INFLOW_SUFFIX1= '1'
XML_INFLOW_SUFFIX2 = '2'

#Utils for the links
XML_SUBMOD = 'sub_models'
XML_INTERFACE_OUT = '.interface.Outflow'
XML_INTERFACE_IN = '.interface.Inflow'
XML_TYPEVAL_LINK = 'Connect'
XML_CONN_TYPE = 'ConnectionType'
XML_CONN_NAME = 'ConnectionName'
XML_WATERLINE = 'WaterLine'

XML_QUOT = '&quot;'