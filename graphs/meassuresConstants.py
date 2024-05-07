
INDEX_COL = 'Date'


ESTA_ME = "Station Est (m³/h)"

PASCAL_ME ='U004 St-Pascal (m³/h)'

LIMOILOU_ME = "U002 Limoilou Sanitaire (m³/h)"
LIMOILOU_ME_SANI = "U002 Limoilou Sanitaire (l/s)"
LIMOILOU_ME_PLUV = "U002 Limoilou Pluvial (l/s)"

STSACREMENT_ME = "U225 St-Sacrement Effluent (m³/h)" 
STSACREMENT_ME_EF = 'U225 St-Sacrement Effluent (l/s)'
STSACREMENT_ME_AF = 'U225 St-Sacrement Affluent (l/s)'
STSACREMENT_ME_R = 'U225 St-Sacrement Entrée réservoir (l/s)' 
STSACREMENT_ME_D = 'U225 St-Sacrement Débordé (l/s)'


NO_ME = 'U003 Nord-Ouest Sanitaire (m³/h)'
NO_ME_PLUV = 'U003 Nord-Ouest Pluvial (m³/h)'


BEAUPORT_ME_1 ='U016 Beauport Pompe 1 (l/s)'
BEAUPORT_ME_2 ='U016 Beauport Pompe 2 (l/s)'
BEAUPORT_ME_3 ='U016 Beauport Pompe 3 (l/s)'


#Columns separated by their units
FLOWS_LPS = [LIMOILOU_ME_SANI,LIMOILOU_ME_PLUV,BEAUPORT_ME_1,BEAUPORT_ME_2,BEAUPORT_ME_3,
            STSACREMENT_ME_AF,STSACREMENT_ME_EF,STSACREMENT_ME_R,STSACREMENT_ME_D]

FLOWS_M3H = [ESTA_ME,PASCAL_ME,NO_ME,NO_ME_PLUV]