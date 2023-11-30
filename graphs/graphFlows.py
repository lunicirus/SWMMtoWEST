import utils as util

import matplotlib.pyplot as plt

#Graph a whole DF as a time series
def plotTimeSeries(df,fileOut,ppt=False,alpha=0.7,colorS=None,limsX=None,limsY=None,points=False):
    
    #For the label
    df.columns = df.copy().columns.str.replace('(m³/h)','')

    #plots the series of each column
    fig1, ax  = plt.subplots(figsize=(14,6)); #creates the figure
        
    if points:
        df.plot(ax= ax,alpha=alpha,marker='.',linewidth=0,color=colorS);
    elif colorS is None:
        df.plot(ax= ax,alpha=alpha);
    else:
        df.plot(ax= ax,alpha=alpha,color=colorS);
        
    #For ppt
    if(ppt):
        ax= util.modifyForPpt(ax)
    
    #Visual prettiness
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.18), framealpha=0);#puts the figure in the bottom center with 4 col
    util.removeTopRightFrame(ax)
    
    ax.set_ylabel("Flow rate (m³/h)")
    
    if limsX is not None:
        ax.set_xlim(limsX)
    if limsY is not None:
        ax.set_ylim(limsY)
    
    fig1.savefig(fileOut, dpi=200, bbox_inches='tight',transparent=True); #saves the fig
    
    return ax


def plotComparisonsComplete(measured, westOriginal, west, figName,colors):

    #plots the series of each column
    fig1, ax  = plt.subplots(figsize=(14,6)); #creates the figure

    measured.plot(ax=ax, alpha=0.8, marker='.', linewidth=0, color=colors[0]);
    
    westOriginal.plot(ax=ax, alpha=0.8, linewidth=2, ls='--', color=colors[1]);

    west.plot(ax=ax, alpha=0.8, linewidth=2, color= colors[2]);
    
    ax= util.modifyForPpt(ax)
        
    ax.set_ylabel("Flow rate (m³/h)")
    
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.45,-.22), framealpha=0);#puts the figure in the bottom center with 4 col
    util.removeTopRightFrame(ax)

    fig1.savefig('03-Graphs/'+'Comparison'+figName+'.png', dpi=200, bbox_inches='tight',transparent=True); #saves the fig
   

#Assumes values are in m3/h
def plotComparisonsSWMM_WEST(swmm, west, fileOut, color, ppt=True):

    #plots the series of each column
    fig1, ax  = plt.subplots(figsize=(14,6)); #creates the figure
    
    #Plots the SWMM values
    swmm.plot(ax=ax, alpha=0.8, linewidth=2 , color=color);

    #Plots WEST values with a darker color and cutted line
    colorD = util.darken_hex_color(color)
    west.plot(ax=ax, alpha=0.8, linewidth=2, ls='--',color= colorD);
    
    if ppt:
        ax= util.modifyForPpt(ax)
        
    ax.set_ylabel("Flow rate (m³/h)")
    
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.45,-.22), framealpha=0);#puts the figure in the bottom center with 4 col
    util.removeTopRightFrame(ax)

    fig1.savefig(fileOut, dpi=200, bbox_inches='tight',transparent=True); #saves the fig
   
   