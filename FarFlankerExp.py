 ############################################################################
# %%
import os
from psychopy.hardware import keyboard
from psychopy import core, visual, data, event, monitors, logging#, gui #`psychopy.gui` doesn't work in lab
from psychopy.tools.filetools import fromFile, toFile
import numpy as np
import random
import itertools
import math
import re
import pickle
import pandas as pd
import glob
import pylink
from importlib import reload
import sys

sys.path.append('/Users/harrysteinharter/Documents/MSc/Timo Internship/7LineSegments')
import otherFunctions as OF # Has to go after changing directory bc of it's location
reload(OF) # Allows me to edit OF w/out restartig VSCode

def SubNumber(filename):
#    os.chdir("/Users/harrysteinharter/Documents/Programming/Timo Internship")
    with open(filename, 'r', encoding='utf-8-sig') as file:
        content = int(file.read().strip())

    content_int = int(content)
    new_content = (content_int + 1)
    
    with open(filename, 'w') as file:
        file.write(str(new_content))
    return new_content

nSubject = SubNumber('subjectNumber.txt')
dateStr = data.getDateStr(fractionalSecondDigits = 1)

ShouldLog = True
if ShouldLog:

    # Possible levels (in ascending order): logging.DEBUG|INFO|EXP|DATA|WARNING|ERROR|CRITICAL
    # CRITICAL is not used by psychopy, so nothing should appear
    logLevel = logging.DEBUG
    # logging.console.setLevel(logLevel) # Logs in the console
    logging.LogFile(f'Logging/{nSubject}_log.txt',level=logLevel, filemode='w') # Logs to a file
############################################################################
# %%

SubjectInfo = "Subject_"+str(nSubject)+"_"

fileName = SubjectInfo+dateStr
pathName = os.path.join(os.getcwd(),"Outputs/")
fullFile = pathName + fileName
############################################################################
# %%
# EYETRACKER SETUP
eyeHostFile = str(nSubject)+'.edf'
eyeLocalFile = "EyeLink/"+eyeHostFile
dummy = True
if dummy == True:
    tracker = pylink.EyeLink(None)
else:
    tracker = pylink.EyeLink("100.1.1.2:255.255.255.0")  # our eyelink is at 100.1.1.2:255.255.255.0. default is 100.1.1.1:...

tracker.openDataFile(eyeHostFile)
tracker.sendCommand("screen_pixel_coords = 0 0 1919 1079")

def closeTracker(tracker,eyeHostFile,eyeLocalFile):
    tracker.closeDataFile()
    tracker.receiveDataFile(eyeHostFile, eyeLocalFile) # Takes closed data file from 'src' on host PC and copies it to 'dest' at Stimulus PC
    tracker.close()
if not dummy:
    pylink.openGraphics()
    tracker.doTrackerSetup()
    pylink.closeGraphics()
############################################################################
# %%
# Open a CSV file to store the data
dataFile = open(fullFile+'.csv', 'w') 
dataFile.write('Participant_Number,Trial_Number,Condition,FCfar,FCmed,FCclose,Target_Contrast,Correct_Response,Reaction_Time\n')

# Set up the window and visual elements   #####REMEMBER TO CHANGE MONITOR to `flanders` from `myMacbook`#######
mywin = visual.Window(fullscr=True, monitor="Flanders", units="deg",colorSpace='rgb',color = [0,0,0],bpc=(10,10,10),depthBits=10)

subInfo = visual.TextStim(mywin,f"""Subject Number: {nSubject}\n{dateStr}""",color='black')
OF.drawOrder(subInfo,mywin)
event.waitKeys()

line_Length = 0.5
# Lines go 1-7, top to bottom. `line1` is top, `line4` is the target, `line7` is the bottom
line1=visual.Line(win=mywin, start=(0,2.75), end=(0,3.25),  lineWidth=4.2, pos=(0,0),  colorSpace='rgb')
line2=visual.Line(win=mywin, start=(0,1.75), end=(0,2.25),  lineWidth=4.2, pos=(0,0),  colorSpace='rgb')
line3=visual.Line(win=mywin, start=(0,.75), end=(0,1.25),  lineWidth=4.2, pos=(0,0),  colorSpace='rgb')

line4=visual.Line(win=mywin, start=(0,-0.25), end=(0,0.25),  lineWidth=4.2, pos=(0,0),  colorSpace='rgb')

line5=visual.Line(win=mywin, start=(0,-.75), end=(0,-1.25), lineWidth=4.2, pos=(0,0), colorSpace='rgb')
line6=visual.Line(win=mywin, start=(0,-1.75), end=(0,-2.25), lineWidth=4.2, pos=(0,0), colorSpace='rgb')
line7=visual.Line(win=mywin, start=(0,-2.75), end=(0,-3.25), lineWidth=4.2, pos=(0,0), colorSpace='rgb')
#Use the link below to easily calculate visual angle measurements for lineWidth which is ALWAYS IN PIXELS
#https://elvers.us/perception/visualAngle/

# Set line colors to black
lines = [line1,line2,line3,line4,line5,line6,line7]
lines_null = [line1,line2,line3,line5,line6,line7]
for line in lines:
    line.color = 'black'

# Set up the fixation point
#fixation = visual.Circle(win=mywin, color=-1, colorSpace='rgb', radius = .3, edges = 'circle', fillColor = None, lineWidth=2)
# I don't like that one ^
fixation = visual.GratingStim(win = mywin, color=-1, colorSpace='rgb',tex=None, mask='circle', size=0.1)

# Initialize clocks for global and trial timing (We might delete it)
globalClock = core.Clock()
trialClock = core.Clock()
break_t = 10 # Mandatory duration of breaks (in seconds).

#### Define the messages that appear ####
message1 = visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [-1,-1,-1],
    text='During the study, press RIGHT if you see stimulus in the center of the screen. Press LEFT if you do not. Respond during the blank screen after the stimulus has disappeared. Press any key when ready.')

message2 = visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [0,0,0],
    text="Is there a target?\ LEFT for YES\nor\nRIGHT for NO")
    # Message 2 cannot be seen because the color is the same as the background. It is used to clear the screen.

pause = visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [-1,-1,-1],
    text = f"Take a break. Do not press any keys until you are ready to begin again. Then press any key. You cannot continue until at least {break_t} seconds have passed. The next section will be identical to the previous.")

continue_m = visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [-1,-1,-1],
    text = f"Take a break. Do not press any keys until you are ready to begin again. Then press any key. You cannot continue until at least {break_t} seconds have passed. The next section will be identical to the previous. {break_t} seconds has elapsed. Press any key to continue.")

inbetweeners = visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [-1,-1,-1],
    text = f"That was practice. The actual test will begin after this. The actual test will be faster, and it will not tell you which button you pressed. The actual test will contain different stimuli, it will not be the circles. Press any key when you are ready. You must wait at least {break_t} seconds.")

welcome = visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [-1,-1,-1],
    text = 'Welcome to the experiment. The next section will be training. Press RIGHT on the keyboard after you see the stimulus in the center of the screen. Press LEFT when you do not. You should respond during the blank screen after the stimuli disappear.')

#Blank stim debug
blankdebug = visual.TextStim(win=mywin, pos=[0,2],colorSpace='rgb',color = [-1,-1,-1],
    text = "BLANK")
# Eyelink photodiode
diode = visual.GratingStim(mywin,color='black',colorSpace='rgb',tex=None,mask='circle',units='pix',size=80,pos=[-780,-440],autoDraw=True)

welcome.draw()
mywin.flip()
event.waitKeys()#keyList=["space"]

offset = math.cos(math.radians(60))*(6/12)
############################################################################
# %%
#### Establish some stuff ####
nup = 1
ndown = 1
nBlocks = 10
nReal = 18 # 18 was last experiment
nNull = 2 # 2 was last experiment4646
# Define experimental conditions (Different staircase procedures which run independently and randomly)
conditions=[
    {"label":"FarHighNarrow",'startVal': .1, "FCfar":0.2, "FCmed":0.15, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarLowNarrow",'startVal': .1,  "FCfar":0.1, "FCmed":0.15, "FCclose":0.2,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarHighWide",'startVal': .1,   "FCfar":0.5, "FCmed":0.25, "FCclose":0.03, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarLowWide",'startVal': .1,    "FCfar":0.03, "FCmed":0.25, "FCclose":0.5, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"Constant",'startVal': .1,      "FCfar":0.1, "FCmed":0.1, "FCclose":0.1,   "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    
#Null conditions. Are identical, except some (or all) lines do not get drawn
        # Calculate p' = (p-fp)/(1-fp) where p = positive rate, fp = false positive rate
        # Calculate it for each shape at each contrast level

    #C_null shapes
    {"label":"FarHighNarrow_null",'startVal': .1, "FCfar":0.2, "FCmed":0.15, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarLowNarrow_null",'startVal': .1,  "FCfar":0.1, "FCmed":0.15, "FCclose":0.2,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarHighWide_null",'startVal': .1,   "FCfar":0.5, "FCmed":0.25, "FCclose":0.03, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarLowWide_null",'startVal': .1,    "FCfar":0.03, "FCmed":0.25, "FCclose":0.5, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"Constant_null",'startVal': .1,      "FCfar":0.1, "FCmed":0.1, "FCclose":0.1,   "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    # Control w/ 3 lines
    {"label":"ThreeLinesControl",'startVal': .1, "FCfar":0.0, "FCmed":0.0, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"ThreeLinesControl_null",'startVal': .1, "FCfar":0.0, "FCmed":0.0, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},

]

exp_cons = [
    {"label":"FarHighNarrow",'startVal': .1, "FCfar":0.2, "FCmed":0.15, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarLowNarrow",'startVal': .1,  "FCfar":0.1, "FCmed":0.15, "FCclose":0.2,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarHighWide",'startVal': .1,   "FCfar":0.5, "FCmed":0.25, "FCclose":0.03, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarLowWide",'startVal': .1,    "FCfar":0.03, "FCmed":0.25, "FCclose":0.5, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"Constant",'startVal': .1,      "FCfar":0.1, "FCmed":0.1, "FCclose":0.1,   "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"ThreeLinesControl",'startVal': .1, "FCfar":0.0, "FCmed":0.0, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1},

]

null_cons = [
    #_null shapes
    {"label":"FarHighNarrow_null",'startVal': .1, "FCfar":0.2, "FCmed":0.15, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarLowNarrow_null",'startVal': .1,  "FCfar":0.1, "FCmed":0.15, "FCclose":0.2,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarHighWide_null",'startVal': .1,   "FCfar":0.5, "FCmed":0.25, "FCclose":0.03, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"FarLowWide_null",'startVal': .1,    "FCfar":0.03, "FCmed":0.25, "FCclose":0.5, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"Constant_null",'startVal': .1,      "FCfar":0.1, "FCmed":0.1, "FCclose":0.1,   "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
    {"label":"ThreeLinesControl_null",'startVal': .1, "FCfar":0.0, "FCmed":0.0, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1},
]

global condition_counters
condition_counters = [
    # Exp
    [{"label":"FarHighNarrow",'startVal': .1, "FCfar":0.2, "FCmed":0.15, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1}, 1, nReal*nBlocks],
    [{"label":"FarLowNarrow",'startVal': .1,  "FCfar":0.1, "FCmed":0.15, "FCclose":0.2,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1}, 1, nReal*nBlocks],
    [{"label":"FarHighWide",'startVal': .1,   "FCfar":0.5, "FCmed":0.25, "FCclose":0.03, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1}, 1, nReal*nBlocks],
    [{"label":"FarLowWide",'startVal': .1,    "FCfar":0.03, "FCmed":0.25, "FCclose":0.5, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1}, 1, nReal*nBlocks],
    [{"label":"Constant",'startVal': .1,      "FCfar":0.1, "FCmed":0.1, "FCclose":0.1,   "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1}, 1, nReal*nBlocks],
    [{"label":"ThreeLinesControl",'startVal': .1, "FCfar":0.0, "FCmed":0.0, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nReal*nBlocks, "minVal":0, "maxVal":.1}, 1, nReal*nBlocks],
    # Null
    # C
    [{"label":"FarHighNarrow_null",'startVal': .1, "FCfar":0.2, "FCmed":0.15, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1}, 1, nNull*nBlocks],
    [{"label":"FarLowNarrow_null",'startVal': .1,  "FCfar":0.1, "FCmed":0.15, "FCclose":0.2,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1}, 1, nNull*nBlocks],
    [{"label":"FarHighWide_null",'startVal': .1,   "FCfar":0.5, "FCmed":0.25, "FCclose":0.03, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1}, 1, nNull*nBlocks],
    [{"label":"FarLowWide_null",'startVal': .1,    "FCfar":0.03, "FCmed":0.25, "FCclose":0.5, "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1}, 1, nNull*nBlocks],
    [{"label":"Constant_null",'startVal': .1,      "FCfar":0.1, "FCmed":0.1, "FCclose":0.1,   "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1}, 1, nNull*nBlocks],
    [{"label":"ThreeLinesControl_null",'startVal': .1, "FCfar":0.0, "FCmed":0.0, "FCclose":0.1,  "nReversals":1, "stepType":'log', "stepSizes":0.1, "nUp":nup, "nDown":ndown, "nTrials":nNull*nBlocks, "minVal":0, "maxVal":.1}, 1, nNull*nBlocks]
]

############################################################################
# %%
#trialNum = 0
maxTrials = (nReal+nNull) * nBlocks * len(exp_cons)
maxWait = 1.3#1.3
#### Define my own personal hell #### 

stairs = data.MultiStairHandler(stairType="simple",conditions=conditions, nTrials=maxTrials,method="random") 

def trialRandomizer():
    randNum = random.randint(1,10)
    if randNum == 1:
        trialType = 'null'
    else:
        trialType = 'exp'
    return trialType
    
def trialChecker(trialType):
    global condition_counters
    
    # Filter active staircases that haven't reached their trial limit
    active_stairs = []
    for stair in stairs.staircases:
        if stair.finished:
            continue
        
        counter = next((c for c in condition_counters if c[0] == stair.condition), None)
        if counter is None:
            print(f"Warning: No counter found for condition {stair.condition}")
            continue
        
        current_count, max_count = counter[1], counter[2]
        if current_count <= max_count:
            active_stairs.append(stair)

    if not active_stairs:
        return None  # All staircases are finished or at their limit

    if trialType == 'exp':
        curr_stairs = [stair for stair in active_stairs if stair.condition in exp_cons]
        if not curr_stairs:
            curr_stairs = [stair for stair in active_stairs if stair.condition in null_cons]
    elif trialType == 'null':
        curr_stairs = [stair for stair in active_stairs if stair.condition in null_cons]
        if not curr_stairs:
            curr_stairs = [stair for stair in active_stairs if stair.condition in exp_cons]
    else:
        print('Error in trialChecker()')
        core.quit()

    if curr_stairs:
        chosen_stair = random.choice(curr_stairs)
        # Increment the counter for the chosen condition
        for counter in condition_counters:
            if counter[0] == chosen_stair.condition:
                counter[1] += 1
                break
        return chosen_stair
    else:
        print('!!! No More Staircases !!!')
        return None  # No suitable staircases found


def trialCheckerOG(trialType):
    active_stairs = [stair for stair in stairs.staircases if not stair.finished]
    if not active_stairs:
        return None  # All staircases are finished

    if trialType == 'exp':
        curr_stairs = [stair for stair in active_stairs if stair.condition in exp_cons]
        if not curr_stairs:
            curr_stairs = [stair for stair in active_stairs if stair.condition in null_cons]
    elif trialType == 'null':
        curr_stairs = [stair for stair in active_stairs if stair.condition in null_cons]
        if not curr_stairs:
            curr_stairs = [stair for stair in active_stairs if stair.condition in exp_cons]
    else:
        print('Error in trialChecker()')
        core.quit()

    if curr_stairs:
        return random.choice(curr_stairs)
    else:
        print('!!! No More Staircases !!!')
        return None  # No suitable staircases found+

############################################################################
# %%
#### Define the experimental loop ####
breakTrials = np.int16(np.linspace(0,maxTrials,nBlocks+1,endpoint=True)[1:-1]).tolist()
fixation_t = .2 #pre-stim fixation period duration
stim_t = .2 # stimulus duration (0.2)
response_t = 1.3 # max time to respond

def pilot():
    global trialTracker
    
    
    for trialNum in range(maxTrials):
        currStair = trialChecker(trialRandomizer())
        stairs.currentStaircase = currStair
        
        thisCondition = stairs.currentStaircase.condition
        thisIntensity = stairs.currentStaircase.intensity
        stairs.currentStaircase.intensities.append(thisIntensity)
        
#        just for checking on things
#        print('||||||||||||||||||||||||||||||||||||||||||||||||||||||')
#        print(stairs.currentStaircase.condition)
#        print(stairs.currentStaircase.condition['cntrst'])
#        print(stairs.currentStaircase.intensity)
#        print('||||||||||||||||||||||||||||||||||||||||||||||||||||||')
#        print(stairs.currentStaircase.intensities)
#        print(stairs.currentStaircase.intensities)
#        print('||||||||||||||||||||||||||||||||||||||||||||||||||||||')
        
     #   trialTracker[conditions.index(thisCondition),1] += 1
        # print(trialNum)
        if trialNum in breakTrials:
            print('-------------------- BREAK TIME --------------------')
            pause.text = f"You have just finished {breakTrials.index(trialNum)+1}. Take a break. Do not press any keys until you are ready to begin again. Then press any key. You cannot continue until at least {break_t} seconds have passed. The next section will be identical to the previous."
            OF.drawOrder(pause,mywin)
            core.wait(break_t)
            OF.drawOrder(continue_m,mywin)
            event.waitKeys()
            OF.countdown(mywin)
        
        tracker.startRecording(1,1,1,1)
        # Set line properties based on the current condition
        logging.log(f"Trial {trialNum} begins: {thisCondition['label']} | {thisIntensity}",logging.DATA)
        tracker.sendMessage(f"TRIAL_START {trialNum} | {thisCondition['label']} | {thisIntensity}")
        line1.contrast = thisCondition['FCfar']
        line7.contrast = thisCondition['FCfar']

        line2.contrast = thisCondition['FCmed']
        line6.contrast = thisCondition['FCmed']

        line3.contrast = thisCondition['FCclose']
        line5.contrast = thisCondition['FCclose']
  
        line4.contrast = thisIntensity
        
        #set debug messages
        DebugIntensity = visual.TextStim(win=mywin, pos=[0,-2],colorSpace='rgb',color = [-1,-1,-1],text=thisIntensity)
        #DebugIntensity.draw()
            
        # Draw the first fixation point
        diode.color *= -1 # Diode white now
        OF.drawOrder(fixation,mywin)
        core.wait(fixation_t)
        diode.color *= -1 # Diode black now
        mywin.flip()
        core.wait(2/60) # 2 frames
        
        if thisCondition['label'].endswith('_null'):
            # Don't draw the target (`line4`)
            diode.color *= -1 # Diode white now
            OF.drawOrder(lines_null,mywin)
            logging.log("Stim Appears",logging.DATA)
            core.wait(stim_t)
            diode.color *= -1 # Diode back to black
            OF.drawOrder(message2,mywin)
            logging.log("Stim Disappears",logging.DATA)
            trialClock.reset()
            thisResp=None
            rt = None
        else:
            # Draw the lines
            diode.color *= -1 # Diode white now
            OF.drawOrder(lines,mywin)
            logging.log("Stim Appears",logging.DATA)
            core.wait(stim_t)
            diode.color *= -1 # Diode back to black
            OF.drawOrder(message2,mywin)
            logging.log("Stim Disappears",logging.DATA)
            trialClock.reset()
            thisResp=None
            rt = None
        # Wait for a response with a maximum wait time

        allKeys = event.waitKeys(maxWait = response_t) #1.3
        formatted_number = "{:.3f}".format(thisIntensity)
        formatted_number=float(formatted_number)
        
         # Process the response
        if allKeys:
            for thisKey in allKeys:
                rt = trialClock.getTime()
                if thisKey in ['left','num_4']:
                    if thisCondition['label'].endswith('_null'): 
                        thisResp = 1
                        thisResp = 1
                    else: thisResp = 0
                elif thisKey in ['right','num_6']:
                    if thisCondition['label'].endswith('_null'): 
                        thisResp = 0
                    else: thisResp = 1              
                elif thisKey in ['q', 'escape']:
                    stairs.saveAsPickle(f"PickledStaircases/{nSubject}_stairData.pkl",fileCollisionMethod='overwrite')
                    event.clearEvents()
                    closeTracker(tracker,eyeHostFile,eyeLocalFile) #close and save eye data
                    core.quit()  
        else:
            thisResp = 0
            rt = 99 # fill in rt w/ 99 if they don't respond
        tracker.sendMessage(f"TRIAL_END {trialNum} | {thisCondition['label']} | {thisIntensity}")
        core.wait(response_t-rt)
        # Add the response to the staircase handler    
        stairs.currentStaircase.addResponse(thisResp)
        stairs.totalTrials += 1

        # Write the correct response to the data file
        dataFile.write(f"{nSubject},{trialNum},{thisCondition['label']},{thisCondition['FCfar']},{thisCondition['FCmed']},{thisCondition['FCclose']},{thisIntensity},{thisResp},{rt}\n")
        tracker.stopRecording()

#### Define the practice loop ####
def training():
    trials = np.linspace(0,19,20,True,dtype=int).tolist()
    trialContrast = np.linspace(0,.2,20).tolist()
    random.shuffle(trials)
    random.shuffle(trialContrast)

    maxWait = 1
    tStim = 1 # actual EXP is 0.2
        # Why is `visual.Circle(...) broken??`
    topBall =       visual.GratingStim(win=mywin, colorSpace='rgb', color='black', size=0.5, pos=(0,1), tex=None, mask='circle')
    bottomBall =    visual.GratingStim(win=mywin, colorSpace='rgb', color='black', size=0.5, pos=(0,-1), tex=None, mask='circle')
    midBall =       visual.GratingStim(win=mywin, colorSpace='rgb', color='black', size=0.5, pos=(0,0), tex=None, mask='circle')
    fix =           visual.GratingStim(win = mywin, color=-1, colorSpace='rgb',tex=None, mask='circle', size=0.1)
    respLEFT =      visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [-1,-1,-1],text="You pressed LEFT")
    respRIGHT =     visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [-1,-1,-1],text="You pressed RIGHT")
    debug = False
    
    i = .5
    for trial in trials:
        debug_i = visual.TextStim(win=mywin, pos=[0,3],colorSpace='rgb',color = [-1,-1,-1],text=f"{i}")
        midBall.contrast = trialContrast[trial]
#        midBall.fillColor = i

        OF.drawOrder(fix,mywin)
        core.wait(.5)
        if trial % 2:
            OF.drawOrder(midBall if not debug else [midBall,debug_i],mywin)
            core.wait(tStim)
            OF.drawOrder(message2,mywin)
        else:
            OF.drawOrder([topBall,midBall,bottomBall] if not debug else [topBall,midBall,bottomBall,debug_i],mywin)
            core.wait(tStim)
            OF.drawOrder(message2,mywin)
        
        trialClock.reset()
        allKeys = event.waitKeys(maxWait=maxWait)
        
        # Process the response
        if allKeys:
            print(allKeys)  # Add this line temporarily
            for thisKey in allKeys:
                rt = trialClock.getTime()
                if thisKey in ['left','num_4']:
                    resp = respLEFT
                elif thisKey in ['right','num_6']:
                    resp = respRIGHT
                elif thisKey in ['q', 'escape']:
                    closeTracker(tracker,eyeHostFile,eyeLocalFile) #close and save eye data
                    core.quit()  
        else:
            resp = message2
            rt = maxWait

        OF.drawOrder(resp,mywin)
        core.wait(maxWait-rt)
        if trials.index(trial) % 2:
            i -= .05

############################################################################
# %%
#### Run the functions w/ the break in between ####
doTraining = True
if doTraining:
    training()

    OF.drawOrder(inbetweeners,mywin)
    core.wait(break_t)
    OF.drawOrder(continue_m,mywin)
    event.waitKeys()
    OF.countdown(mywin)

pilot()

#### Close it all out ####
# Close the data file
dataFile.close()
thanks = visual.TextStim(win=mywin, pos=[0,0],colorSpace='rgb',color = [-1,-1,-1],
    text="Thanks for Participating! It's finally over!")
OF.drawOrder(thanks,mywin)
event.waitKeys(maxWait=5)
mywin.close()
closeTracker(tracker,eyeHostFile,eyeLocalFile) #close and save eye data
# Save the staircase data to a pickle file
stairs.saveAsPickle(f"PickledStaircases/{nSubject}_stairData.pkl",fileCollisionMethod='overwrite')
print('Success!!')
# %%
