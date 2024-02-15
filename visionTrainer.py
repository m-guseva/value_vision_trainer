from PIL import Image, ImageDraw, ImageOps
import pandas as pd
from numpy import  array
import numpy as np
import streamlit as st
import math


st.set_page_config(
    page_title="Vision Training",
    page_icon="👁",
    layout="wide"
)

##################################################
# Initialize parameters

baseWidth = 600 # base width of picture, height is adjusted
epsilon = 5 # threshold value that indicates how much we allow neighboring pixels to differ from target pixel
targetX = -20 # initialize target X coordinate (negative so that the box is not visible)
targetY = -20 # initialize target Y coordinate


# Session state variables
if 'targetX' not in st.session_state:
    st.session_state['targetX'] = targetX
if 'targetY' not in st.session_state:
    st.session_state['targetY'] = targetY
if 'score' not in st.session_state:
    st.session_state['score'] = 0

##################################################
# Functions
##################################################
def resizeImage(image, baseWidth):
    """Function takes set base width and adjusts height"""
    wPercent = (baseWidth/float(image.size[0]))
    hSize = int(float(image.size[1])*float(wPercent))    
    image = image.resize((baseWidth, hSize))    
    return image

def convertImage(image):
    image = ImageOps.grayscale(image)
    image = image.convert("RGB")
    return image

def definePermissibleValues(luminanceMatrix):
    '''Not all pixels are allowed to be chosen. Only those that are in the inner
    box, padded by the radius. Else we cannot draw a box around a center pixel.'''
    radius=int(max(luminanceMatrix.shape)*0.02) # 10% of largest of width or height
    #Define permissible values (those where radius is a padding)
    permissibleCol = np.arange(0+radius, luminanceMatrix.shape[0]-radius)
    permissibleRow = np.arange(0+radius, luminanceMatrix.shape[1]-radius)
    return radius, permissibleCol, permissibleRow

def centerCoordinate(i, j, radius):
    ''' Calculate the coordinates of the bounding box given the center coordinates and radius.'''
    upperLeftX = j-radius
    upperLeftY = i-radius
    lowerRightX = j+radius
    lowerRightY = i+radius
    return upperLeftX, upperLeftY, lowerRightX, lowerRightY

def nearestNeighbours(i,j,radius,pix):
    '''Function takes permissible i and j positions of a target pixel and outputs neighboring values 
    
    Parameters:
    i:column
    j:row 
    radius:radius around target pixel'''
    cols = np.ndarray.tolist(np.arange(i-radius,i+1+radius))
    rows = np.ndarray.tolist(np.arange(j-radius,j+1+radius))
    neighbours = []
    for x in range(len(cols)):
        for y in range(len(rows)):
            if (cols[x] == i) & (rows[y]== j):
                pass
            else:
                neighbours.append(pix[cols[x], rows[y]])
    return neighbours


def chooseProbePixel(luminanceMatrix, radius, permissibleRow, permissibleCol):
    ''' While diff is greater than some value epsilon, the nearestNeighbours 
    algorithm is looking for appropriate target X and Y coordinates. It does so 
    by  choosing random X and X coordinates  extracting surrounding neighbors, 
    calculate their average tonal values and comparing it to diff.
    '''
    diff = 1+epsilon #initialize a value
    while(diff>epsilon):    
        targetX = np.random.choice(permissibleCol)
        targetY = np.random.choice(permissibleRow)
        nnVals = nearestNeighbours(targetX, targetY,radius,luminanceMatrix)
        diff = abs(luminanceMatrix[targetX, targetY]-np.mean(nnVals))
    else:
        st.session_state.targetX = targetX
        st.session_state.targetY  = targetY
    return 

def drawBox(image, luminanceMatrix, radius):
    draw = ImageDraw.Draw(image)
    probeBoxWidth =  math.ceil(max(luminanceMatrix.shape)*0.002)
    draw.rectangle(centerCoordinate(st.session_state.targetX,st.session_state.targetY,radius), outline='red',  width=probeBoxWidth) 
    return

def scoring(diffSliderReal):
    x = round(diffSliderReal)
    points = x*(-2)+100
    return points

def displaySliderBox():
    placeholder_slider = st.empty()
    sliderVal = placeholder_slider.slider("Choose the value on the slider", max_value = 100, key='10')   
    #sliderVal = col3.slider("Choose the value on the slider", max_value = 100)   
    compBox = Image.new('L', (100, 100), (int(sliderVal*2.55))) #sliderVal*2.55 because we have to change scale to 0-255
    col3.image(compBox) 
    return sliderVal, placeholder_slider

def imageUploadProcedure():
    # Open image from files
    image = Image.open(uploaded_file)    
    # Resize image to base width
    image = resizeImage(image, baseWidth)
    # Convert image to grayscale and RSB values
    image = convertImage(image)
    # Create matrix of luminance values from image
    luminanceMatrix = array(image.convert("L")) # 0 black, 255 white
    # Determine admissible radius, columns and rows 
    radius, permissibleCol, permissibleRow = definePermissibleValues(luminanceMatrix)
    return luminanceMatrix,image, radius, permissibleCol, permissibleRow


##################################################
# Streamlit display, front end stuff

st.title("👁 Value Vision Trainer 👁")
st.subheader("How it works:")
col1, col2, col3 = st.columns([0.3,0.4,0.3])    
string_tutorial = '''1. Upload an image of your choice
2. Press 'Train!', 
A box appears on some spot in the image. 
3. Choose the tonal value that is inside the box in the image by moving the slider
4. Log answer by clicking on the button "Log answer" below. 
5. Check the feedback on your performance below 😎
6. If you want to try another image, just upload it a new one below!'''

col1.markdown(string_tutorial)

# Upload file button
uploaded_file = col1.file_uploader("Upload any image to start the training! 👇🏻")
##################################################

if uploaded_file is not None:
   # Upload, convert image, define permissible area for box 
    luminanceMatrix,image, radius, permissibleCol, permissibleRow = imageUploadProcedure()        
    if st.session_state['targetX'] == -20: # before anything has started    
            start_button = col2.button('Start!', key='3')
    else:
            start_button = col2.button('👉🏻 Press for another try ', key='4', help= "Press for a new location on the image!")
    if start_button:
        chooseProbePixel(luminanceMatrix, radius, permissibleRow, permissibleCol)
    with col2:
        # Draw probe box around X and Y coordinates
        drawBox(image, luminanceMatrix, radius)
        # Display image
        st.image(image) 
    with col3:
        sliderVal, placeholder_slider = displaySliderBox()
        realVal = luminanceMatrix[st.session_state.targetX, st.session_state.targetY]
        diffSliderReal = abs(sliderVal*2.55-realVal)
        placeholder = st.empty()
        log_answer = placeholder.button('💡Log Answer!', disabled=False, key='1')
        if log_answer:            
            placeholder_slider.slider("Choose the value on the slider", max_value = 100, key='9', disabled=True)   
            placeholder.button('Try again!', disabled=True, key='2')
            st.session_state['score'] += scoring(diffSliderReal)
            if diffSliderReal < 50:
                st.write(f"You're off by only {round(diffSliderReal/2.55)} steps, great job! 🥳")
            else:
                st.write(f"You're off by {round(diffSliderReal/2.55)} steps, try again! 😢")
    col3.metric("Running score: ", st.session_state['score'])       

