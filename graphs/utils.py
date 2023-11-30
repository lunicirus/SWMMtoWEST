
import matplotlib.colors as mcolors

#Darken a color in hex format by multiplying each RGB component by a factor.
#Parameters:
#- hex_color: String representing the color in hex format (e.g., "#FF0000" for red)
#- factor: Darkening factor (default is 0.7)
#Returns:
#- Darkened color in hex format.
def darken_hex_color(hex_color, factor=0.5):
    
    rgb_color = mcolors.hex2color(hex_color)
    darkened_rgb = [int(component * factor) for component in rgb_color]
    darkened_hex = mcolors.rgb2hex(darkened_rgb)

    return darkened_hex


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