import utils as util
import numpy as np
import matplotlib.cm as cmlib
import pandas as pd

import matplotlib.pyplot as plt


def plotTimeSeries(df:pd.DataFrame,fileOut:str,ylabel:str,ppt:bool=False,alpha:float=0.7,
                   colorS:list=None,limsX:tuple=None,limsY:tuple=None,points:bool=False)-> 'matplotlib.axes.Axes':
    """
        Graph a whole DF as a time series.
    Args:
        df (pd.DataFrame): Time series in each column.
        fileOut (str): Path and name of the file where the created plot will be saved.
        ylabel (str): Label title of the axis Y.
        ppt (bool, optional): _description_. Defaults to False.
        alpha (float, optional): Alpha of the lines in the plot. Defaults to 0.7.
        colorS (list, optional): Colors of the lines in the plot. Defaults to None.
        limsX (tuple, optional): Limits of the axis X. Defaults to None.
        limsY (tuple, optional): Limits of the axis Y. Defaults to None.
        points (bool, optional): True if the time series shoulf be drawn with points instead of lines. Defaults to False.
    Returns:
        matplotlib.axes.Axes: axes of the created plot.
    """    
    fig1, ax  = plt.subplots(figsize=(10,6)); #creates the figure
    
    #plots the series of each column
    if points:
        df.plot(ax=ax, alpha=alpha, marker='.', linewidth=0, color=colorS); 
    elif colorS is None:
        colorSeries = [cmlib._colormaps['viridis'](x) for x in np.linspace(0, 1,df.shape[1])]
        df.plot(ax=ax, alpha=alpha, color=colorSeries);
    else:
        df.plot(ax=ax, alpha=alpha, color=colorS);
        
    #For ppt
    if(ppt):
        ax= util.modifyForPpt(ax)
    
    #Visual prettiness
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.18), framealpha=0);#puts the figure in the bottom center with 4 col
    util.removeTopRightFrame(ax)
    ax.set_ylabel(ylabel)
    
    if limsX is not None:
        ax.set_xlim(limsX)
    if limsY is not None:
        ax.set_ylim(limsY)
    
    fig1.savefig(fileOut, dpi=200, bbox_inches='tight',transparent=True); #saves the fig
    
    return ax

def plotThreeTSeriesComparison(timeSeries1:pd.DataFrame, timeSeries2:pd.DataFrame, timeSeries3:pd.DataFrame,
                                fileOut:str, colors:list, ylabel:str, adaptForDarkBackground:bool=False):
    """
        Plots three timeseries in the same graph.
    Args:
        timeSeries1 (pd.DataFrame): Timeseries to be plotted with only dots.
        timeSeries2 (pd.DataFrame): Timeseries to be plotted with a cutted line.
        timeSeries3 (pd.DataFrame): Timeseries to be plotted with a solid line.
        fileOut (str): Path and name of the file where the created plot will be saved.
        colors (list): Three colors for timeseries 1, 2 and 3.
        ylabel (str): Label to set on the y axis.
        adaptForDarkBackground (bool, optional): True if the plot will be used on a dark background, False otherwise. Defaults to False.
    """    
    
    #'../02-Output/01-Graphs/'+'Comparison'
    
    fig1, ax  = plt.subplots(figsize=(10,6)); #creates the figure

    timeSeries1.plot(ax=ax, alpha=0.8, marker='.', linewidth=0, color=colors[0]); #Only dots
    timeSeries2.plot(ax=ax, alpha=0.8, linewidth=2, ls='--', color=colors[1]); #Cutted line
    timeSeries3.plot(ax=ax, alpha=0.8, linewidth=2, color= colors[2]);
    
    if adaptForDarkBackground:
        ax= util.modifyForPpt(ax)
        
    ax.set_ylabel(ylabel)
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.45,-.22), framealpha=0);#puts the figure in the bottom center with 4 col
    util.removeTopRightFrame(ax)

    fig1.savefig(fileOut, dpi=200, bbox_inches='tight',transparent=True); #saves the fig

def plotTwoTSeriesComparison(timeSeries1:pd.DataFrame, timeSeries2:pd.DataFrame, fileOut:str, color:str,
                             ylabel:str, adaptForDarkBackground:bool=False):
    """
        Plots two timeseries in the same graph. 
    Args:
        timeSeries1 (pd.DataFrame): Timeseries to be plotted with a solid line.
        timeSeries2 (pd.DataFrame): Timeseries to be plotted with a similar but ligther color and a cutted line. 
        fileOut (str): Path and name of the file where the created plot will be saved.
        color (str): Color to be used for the timeseries1.
        ylabel (str): Label to set on the y axis.
        ppt (bool, optional): True if the plot will be used on a dark background, False otherwise. Defaults to False.
    """    
    fig1, ax  = plt.subplots(figsize=(10,6)); #creates the figure
    colorD = util.light_hex_color(color)# Gets a ligther color 

    timeSeries2.plot(ax=ax, alpha=0.8, linewidth=2, ls='--',color= colorD); # Plots the timeseries2 with a ligther color and a cutted line
    timeSeries1.plot(ax=ax, alpha=0.8, linewidth=2 , color=color); #Plots the timeseries1 values
    
    if adaptForDarkBackground:
        ax= util.modifyForPpt(ax)
        
    ax.set_ylabel(ylabel)
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.45,-.22), framealpha=0);#puts the figure in the bottom center with 4 col
    util.removeTopRightFrame(ax)

    fig1.savefig(fileOut, dpi=200, bbox_inches='tight',transparent=True); #saves the fig

def plotVariousComparisons(colsToCompare:list[list[str]], df1:pd.DataFrame, df2:pd.DataFrame, directoryOutput:str):
    """
        Creates as many plots as elements in the colsToCompare. Each plot compares one of the timeseries (columns) of df1 with one of df2.
    Args:
        colsToCompare (list[list[str]]): Each internal list is composed of a column name in df1 and a column name in df2 to be compared.
        df1 (pd.DataFrame): Each column is a time series. Index is datetime.
        df2 (pd.DataFrame): Each column is a time series. Index is datetime.
        directoryOutput (str): Path to the directory where the plots would be saved.
    """    
    colorSeries = [ cmlib._colormaps['plasma'](x) for x in np.linspace(0, 1,len(colsToCompare))]

    for p, c in zip(colsToCompare,colorSeries):

        vals1 = df1[p[1]]
        vals2 = df2[p[0]]
        file = directoryOutput + p[0] +'.png'
        
        plotTwoTSeriesComparison(vals1,vals2,file,c,"Flow rate (m³/h)")