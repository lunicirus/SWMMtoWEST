
import colorsys

#- factor: lightness factor (default is 0.5)
#Returns:
#- light color .
def light_hex_color(color, factor=0.3):

    new_color = tuple(max(0.0, min(channel + factor, 1.0)) for channel in color[:3])
    return new_color + (color[3],)

def removeTopRightFrame(ax):
    
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    return ax

def modifyForPpt(ax):
    
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.tick_params(axis='x',which='both', colors='white')
    ax.tick_params(axis='y',which='both', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    
    return ax