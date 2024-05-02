from __future__ import division
import time
import math as m
import numpy as np
import array as arr 
import timeit
import threading
# Import the PCA9685 module.

import Adafruit_PCA9685

# Uncomment to enable debug output.
#import logging
#logging.basicConfig(level=logging.DEBUG)

# Initialise the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685()
# mpu = Adafruit_PCA9685.MPU6050()

# Configure min and max servo pulse lengths
servo_min = 100  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096

###
# Roll = 0
# Pitch = 0
# # preTimeGet = 0
# def getRollPitch_MPU():
#     global Roll, Pitch # ,preTimeGet
#     Roll, Pitch = mpu.get_RP_Angle()
#     print("Goc truc X: %.1f" %Roll  ,  "Goc truc Y: %.1f" %Pitch)
#     threading.Timer(0.5,getRollPitch_MPU).start()
#     # timeGet = timeit.default_timer()
#     # print(timeGet - preTimeGet, " (seconds)")
#     # preTimeGet = timeGet
###

l1=46.4 #mm
l2=100 #mm
l3=100 #mm

RH = -130 # mm -> Robot height
SH = 35 # mm -> Swing height

A_z = -10 #mm -> add z position(rear legs)
A_x = 20 #mm -> add x position(all legs)(dieu chinh trong tam)
### NOTICE ###
# move forward: A_x = -25
# move bachward: A_x = 20
# move left_right: A_x = 0

#Define side
Front = 30
Rear = 31

#Define leg adress
front_left = 0
front_right = 3
rear_left = 6
rear_right = 9

# Offset matrix [t1,t2,t3] <=> [0,45,90]
FL = arr.array('i', [90, 27, 12])   # -> <Front Left>
RL = arr.array('i', [98, 70, 13])   # -> <Rear Left>
FR = arr.array('i', [90, 83, 160])  # -> <Front Right>
RR = arr.array('i', [90, 84, 170])  # -> <Front Right>

posFL = np.array([0, 0, 0])   # -> <Front Left>
posRL = np.array([0, 0, 0])   # -> <Rear Left>
posFR = np.array([0, 0, 0])  # -> <Front Right>
posRR = np.array([0, 0, 0])  # -> <Front Right>

# angle to pulse
def angle2pulse(angle):
    return (int)(100+500*angle/180)

# Control leg
def setLegAngles(LegAdress, Theta1, Theta2, Theta3):
    #offset
    if(LegAdress == front_left):
        Theta1 = 180 - (Theta1 + FL[0])
        Theta2 = Theta2 + FL[1]
        Theta3 = Theta3 + FL[2]
    elif(LegAdress == front_right):
        Theta1 = 180 - (Theta1 + FR[0])
        Theta2 = Theta2 + FR[1]
        Theta3 = Theta3 + FR[2]
    elif(LegAdress == rear_left):
        Theta1 = Theta1 + RL[0]
        Theta2 = Theta2 + RL[1]
        Theta3 = Theta3 + RL[2]
    elif(LegAdress == rear_right):
        Theta1 = Theta1 + RR[0]
        Theta2 = Theta2 + RR[1]
        Theta3 = Theta3 + RR[2]
    else: 
        print("Wrong Leg Adress")
        exit()
    # print('Theta1= ',Theta1,'Theta2= ',Theta2,'Theta3= ',Theta3)
    pwm.set_pwm_servo(LegAdress,0,angle2pulse(Theta1),angle2pulse(Theta2),angle2pulse(Theta3))
    
def Calib():
    setLegAngles(front_left, 0, 45, 90)
    setLegAngles(front_right, 0, -45, -90)
    setLegAngles(rear_left, 0, 45, 90)
    setLegAngles(rear_right, 0, -45, -90)
    exit()
    
# Helper function to make setting a servo pulse width simpler.
def set_servo_pulse(channel, pulse):
    pulse_length = 1000000    # 1,000,000 us per second
    pulse_length //= 60       # 60 Hz
    print('{0}us per period'.format(pulse_length))
    pulse_length //= 4096     # 12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length
    pwm.set_pwm(channel, 0, pulse)

def Check_work_space(x,y,z):
    k1 = x**2 + y**2 + z**2
    k2 = y**2 + z**2
    if( k2< l1**2 or k1> (l1**2 + (l2 + l3)**2)):
        print("The position :(",x,y,z,") is Out of workspace")
        exit()

def LEFT_Inverse_Kinematics(leg,x,y,z):
    #check work space
    Check_work_space(x,y,z)
    # Theta1
    alpha = m.acos(y/np.sqrt(y**2 + z**2))
    t1 = -(m.acos(l1/np.sqrt(z**2 + y**2)) - alpha)
    c1 = np.cos(t1)
    s1 = np.sin(t1)
    # Theta3
    A = -x
    if(t1!=0):
        B = (l1*c1 - y)/s1
    else:
        B = (-l1*s1 - z)/c1
    c3 = (A**2 + B**2 - l2**2 - l3**2) / (2 * l2 * l3)
    s3 = np.sqrt(m.fabs(1 - c3**2))
    t3 = m.atan2(s3, c3)
    # Kiem tra dk theta3
    if (t3 < 0):
        print("Error Theta3")
        exit()
    # Theta2
    s2 = (A * (l2 + l3 * c3) + B * l3 * s3)  
    c2 = (B * (l2 + l3 * c3) - A * l3 * s3)  
    t2 = m.atan2(s2, c2)

    # Convert Rad -> Deg
    t1 = t1*180/np.pi
    t2 = t2*180/np.pi
    t3 = t3*180/np.pi

    if(leg == Rear):
        setLegAngles(rear_left,t1,t2,t3)
    elif(leg == Front):
        setLegAngles(front_left,t1,t2,t3)

def RIGHT_Inverse_Kinematics(leg,x,y,z):
    #check work space
    Check_work_space(x,y,z)
    # Theta1
    alpha = m.asin(y/np.sqrt(y**2 + z**2))
    t1 = -(m.asin(l1/np.sqrt(z**2 + y**2)) + alpha)
    c1 = np.cos(t1)
    s1 = np.sin(t1)
    # Theta3
    A = -x
    if(t1!=0):
        B = (-l1*c1 - y)/s1
    else:
        B = (l1*s1 - z)/c1
    c3 = (A**2 + B**2 - l2**2 - l3**2) / (2 * l2 * l3)
    s3 = np.sqrt(m.fabs(1 - c3**2))
    t3 = -m.atan2(s3, c3)
    # Kiem tra dk theta3
    if (t3 > 0):
        print("Error Theta3")
        exit()
    # Theta2
    s2 = (A * (l2 + l3 * c3) + B * l3 * s3)  
    c2 = (B * (l2 + l3 * c3) - A * l3 * s3)  
    t2 = -m.atan2(s2, c2)
    
    # Convert Rad -> Deg
    t1 = t1*180/np.pi
    t2 = t2*180/np.pi
    t3 = t3*180/np.pi
    
    if(leg == Rear):
        setLegAngles(rear_right,t1,t2,t3)
    elif(leg == Front):
        setLegAngles(front_right,t1,t2,t3)
    
    
def initial_position():
    global posFL, posRL, posFR, posRR
    LEFT_Inverse_Kinematics(Front, 0,l1,RH)
    RIGHT_Inverse_Kinematics(Front, 0,-l1,RH)
    LEFT_Inverse_Kinematics(Rear, 0,l1,RH)
    RIGHT_Inverse_Kinematics(Rear, 0,-l1,RH) 
    posFL= [0,l1,RH]
    posFR = [0,-l1,RH]
    posRL = [0,l1,RH] 
    posRR = [0,-l1,RH]
    time.sleep(2)

def R_P_Y(roll, pitch, yaw):
    pass

def all_Move(x, y, z, Time_delay): # di chuyen tat ca cac chan 1 doan theo huong x,y,z
    global posFL, posRL, posFR, posRR
    for t in np.arange(0.125, 1.005, 0.125):
        RIGHT_Inverse_Kinematics(Front, posFR[0] - x*t, posFR[1] + y*t, posFR[2] - z*t)
        RIGHT_Inverse_Kinematics(Rear, posRR[0] - x*t, posRR[1] + y*t, posRR[2] - z*t)
        LEFT_Inverse_Kinematics(Rear, posRL[0] - x*t, posRL[1] + y*t, posRL[2] - z*t)
        LEFT_Inverse_Kinematics(Front, posFL[0] - x*t, posFL[1] + y*t, posFL[2] - z*t)
        time.sleep(Time_delay)
    posFR = [posFR[0] - x, posFR[1] + y, posFR[2] - z]
    posFL = [posFL[0] - x, posFL[1] + y, posFL[2] - z]
    posRR = [posRR[0] - x, posRR[1] + y, posRR[2] - z]
    posRL = [posRL[0] - x, posRL[1] + y, posRL[2] - z]
    
def all_To_initial(Time_delay):
    global posFL, posRL, posFR, posRR
    for t in np.arange(0, 1.005, 0.25):
        RIGHT_Inverse_Kinematics(Front, posFR[0] - posFR[0]*t, posFR[1] - (posFR[1]+l1)*t, posFR[2] - (posFR[2]-RH)*t)
        RIGHT_Inverse_Kinematics(Rear, posRR[0] - posRR[0]*t, posRR[1] - (posRR[1]+l1)*t, posRR[2] - (posRR[2]-RH)*t)
        LEFT_Inverse_Kinematics(Rear, posRL[0] - posRL[0]*t, posRL[1] - (posRL[0]-l1)*t, posRL[2] - (posRL[2]-RH)*t)
        LEFT_Inverse_Kinematics(Front, posFL[0] - posFL[0]*t, posFL[1] - (posFL[1]-l1)*t, posFL[2] - (posFL[2]-RH)*t)
        time.sleep(Time_delay)
    posFL= [0,l1,RH]
    posFR = [0,-l1,RH]
    posRL = [0,l1,RH] 
    posRR = [0,-l1,RH]
    
def startWalk(SL_x, SL_y, Time_delay):
    if(SL_x > 0):   A_x = -25   # forward
    elif(SL_x < 0): A_x = 20    # backward
    else:           A_x = -10
    
    if(SL_y > 0):   A_y = 20    # right
    elif(SL_y < 0): A_y = -20   # left
    else:           A_y = 0
    
    for t in np.arange(0,0.505,0.125):
        x = -SL_x*t + A_x
        y = -l1 + SL_y*(t) + A_y
        z = RH 
        RIGHT_Inverse_Kinematics(Rear,x,y,z)
        z += A_z
        y = l1 + SL_y*(t) + A_y
        LEFT_Inverse_Kinematics(Front,x,y,z)

        alpha= np.pi*(1-2*t)
        x = (SL_x/4)*np.cos(alpha) + A_x + SL_x/4
        y = l1 - (SL_y/4)*np.cos(alpha) + A_y - SL_y/4
        z = RH/2 + SH*np.sin(alpha)
        LEFT_Inverse_Kinematics(Rear,x,y,z)
        z += A_z
        y = -l1 - (SL_y/4)*np.cos(alpha) + A_y - SL_y/4
        RIGHT_Inverse_Kinematics(Front,x,y,z)
        time.sleep(Time_delay)
        
def endWalk():
    pass

def Walk(SL_x, SL_y, Time_delay):
    start = timeit.default_timer()
    # adjust center of mass
    if(SL_x > 0):   A_x = -25   # forward
    elif(SL_x < 0): A_x = 20    # backward
    else:           A_x = -10
    
    if(SL_y > 0):   A_y = 20    # right
    elif(SL_y < 0): A_y = -20   # left
    else:           A_y = 0
    
    for t in np.arange(0,1.005,0.125):
        x = -SL_x*t+(SL_x/2) + A_x
        y = -l1 + SL_y*(t)-(SL_y/2) + A_y
        z = RH 
        RIGHT_Inverse_Kinematics(Front,x,y,z)
        z += A_z
        y = l1 + SL_y*(t)-(SL_y/2) + A_y
        LEFT_Inverse_Kinematics(Rear,x,y,z)

        alpha= np.pi*(1-t)
        x = (SL_x/2)*np.cos(alpha) + A_x
        y = l1 - (SL_y/2)*np.cos(alpha) + A_y
        z = RH+SH*np.sin(alpha)
        LEFT_Inverse_Kinematics(Front,x,y,z)
        z += A_z
        y = -l1 - (SL_y/2)*np.cos(alpha) + A_y
        RIGHT_Inverse_Kinematics(Rear,x,y,z)
        time.sleep(Time_delay)
   
    for t in np.arange(0,1.005,0.125):
        alpha= np.pi*(1-t)
        x = (SL_x/2)*np.cos(alpha) + A_x
        y = -l1 - (SL_y/2)*np.cos(alpha) + A_y
        z = RH+SH*np.sin(alpha) 
        RIGHT_Inverse_Kinematics(Front,x,y,z)
        z += A_z
        y = l1 - (SL_y/2)*np.cos(alpha) + A_y
        LEFT_Inverse_Kinematics(Rear,x,y,z)
        
        x = -SL_x*(t)+(SL_x/2) + A_x
        y = l1 + SL_y*(t)-(SL_y/2) + A_y
        z = RH
        LEFT_Inverse_Kinematics(Front,x,y,z)
        z += A_z
        y = -l1 + SL_y*(t)-(SL_y/2) + A_y
        RIGHT_Inverse_Kinematics(Rear,x,y,z)
        time.sleep(Time_delay)
    stop = timeit.default_timer()
    print(stop - start, " (seconds)")
        

def Walk_C(SL_xleft, SL_xright, Time_delay):
    start = timeit.default_timer()
    # adjust center of mass
    if(SL_xleft > 0):   A_x = -25   # forward
    elif(SL_xleft < 0): A_x = 20    # backward
    else:               A_x = -10

    for t in np.arange(0,1.005,0.125):
        x = -SL_xright*t+(SL_xright/2) + A_x
        y = -l1 
        z = RH 
        RIGHT_Inverse_Kinematics(Front,x,y,z)
        x = -SL_xleft*t+(SL_xleft/2) + A_x
        z += A_z
        y = l1 
        LEFT_Inverse_Kinematics(Rear,x,y,z)

        alpha= np.pi*(1-t)
        x = (SL_xleft/2)*np.cos(alpha) + A_x
        y = l1 
        z = RH+SH*np.sin(alpha)
        LEFT_Inverse_Kinematics(Front,x,y,z)
        x = (SL_xright/2)*np.cos(alpha) + A_x
        z += A_z
        y = -l1 
        RIGHT_Inverse_Kinematics(Rear,x,y,z)
        time.sleep(Time_delay)
        
    for t in np.arange(0,1.005,0.125):
        alpha= np.pi*(1-t)
        x = (SL_xright/2)*np.cos(alpha) + A_x
        y = -l1 
        z = RH+SH*np.sin(alpha) 
        RIGHT_Inverse_Kinematics(Front,x,y,z)
        x = (SL_xleft/2)*np.cos(alpha) + A_x
        z += A_z
        y = l1 
        LEFT_Inverse_Kinematics(Rear,x,y,z)
        
        x = -SL_xleft*(t)+(SL_xleft/2) + A_x
        y = l1 
        z = RH
        LEFT_Inverse_Kinematics(Front,x,y,z)
        x = -SL_xright*(t)+(SL_xright/2) + A_x
        z += A_z
        y = -l1 
        RIGHT_Inverse_Kinematics(Rear,x,y,z)
        time.sleep(Time_delay)
    stop = timeit.default_timer()
    print(stop - start, " (seconds)")

def Turn(CW,CCW):
    pass

def Move_around_CW():
    for t in np.arange(0,2.01,0.1):
        if(t<=1):
            x = 0
            y = l1 + SL*(t)-(SL/2)
            z = RH
            LEFT_Inverse_Kinematics(Front,x,y,z)
            y = -l1 - SL*(t) - (SL/2)
            RIGHT_Inverse_Kinematics(Rear,x,y,z)

            alpha= np.pi*(t)
            x = 0
            y = -l1 + (SL/2)*np.cos(alpha)
            z = RH + SH*np.sin(alpha)
            RIGHT_Inverse_Kinematics(Front,x,y,z)
            y = l1-(SL/2)*np.cos(alpha)
            LEFT_Inverse_Kinematics(Rear,x,y,z)
            
            time.sleep(0.01)

        else:
            x = 0
            y = l1 - SL*(t-1)+(SL/2)
            z = -120
            LEFT_Inverse_Kinematics(Rear,x,y,z)
            y = -l1+SL*(t-1)-SL/2 
            RIGHT_Inverse_Kinematics(Front,x,y,z)

            alpha= np.pi*(2-t)
            x = 0
            y = -l1 +(SL/2)*np.cos(alpha)
            z = RH+SH*np.sin(alpha)
            RIGHT_Inverse_Kinematics(Rear,x,y,z)
            y = l1-(SL/2)*np.cos(alpha)
            LEFT_Inverse_Kinematics(Front,x,y,z)

            time.sleep(0.01)

def Move_around_CCW():
    for t in np.arange(0,2.1,0.1):
        if(t<=1):
            x = 0
            y = l1 +SL*(t)-(SL/2)
            z = RH
            LEFT_Inverse_Kinematics(Rear,x,y,z)
            y = -l1-SL*(t)+(SL/2) 
            RIGHT_Inverse_Kinematics(Front,x,y,z)

            alpha= np.pi*(t)
            x = 0
            y = -l1 + (SL/2)*np.cos(alpha)
            z = RH+SH*np.sin(alpha)
            RIGHT_Inverse_Kinematics(Rear,x,y,z)
            y = l1-(SL/2)*np.cos(alpha)
            LEFT_Inverse_Kinematics(Front,x,y,z)
            
            time.sleep(0.01)

        else:
            x = 0
            y = l1 -SL*(t-1)+(SL/2)
            z = RH
            LEFT_Inverse_Kinematics(Front,x,y,z)
            y = -l1+SL*(t-1)-(SL/2) 
            RIGHT_Inverse_Kinematics(Rear,x,y,z)

            alpha= np.pi*(2-t)
            x = 0
            y = -l1 + (SL/2)*np.cos(alpha)
            z = RH+SH*np.sin(alpha)
            RIGHT_Inverse_Kinematics(Front,x,y,z)
            y = l1-(SL/2)*np.cos(alpha)
            LEFT_Inverse_Kinematics(Rear,x,y,z)

            time.sleep(0.01)
            
def Sit(): 
    t1=0;t2=0;t3=0
    for t in np.arange(0,3.01,0.1):
        if(t<=1):
            t2=(45+25*t)
            t3=(90+50*t)
            setLegAngles(rear_left,t1,t2,t3)
            setLegAngles(front_left,t1,t2,t3)
            t2=-t2
            t3=-t3
            setLegAngles(front_right,t1,t2,t3)
            setLegAngles(rear_right,t1,t2,t3)
            
        elif(t <= 2):
            t2=(70-20*(t-1))
            setLegAngles(rear_left,t1,t2,t3)
            setLegAngles(front_left,t1,t2,t3)
            t2=-t2
            setLegAngles(front_right,t1,t2,t3)
            setLegAngles(rear_right,t1,t2,t3)
            
        elif(t <= 3):
            t2=(50-50*(t-2))
            t3=(140-50*(t-2))
            setLegAngles(rear_left,t1,t2,t3)
            setLegAngles(front_left,t1,t2,t3)
            t2=-t2
            t3=-t3
            setLegAngles(front_right,t1,t2,t3)
            setLegAngles(rear_right,t1,t2,t3)
            time.sleep(0.02)
            
        time.sleep(0.01)

def Stand():   
    t1=0;t2=0;t3=0
    for t in np.arange(3,6.01,0.1):  
        if(t<=4):
            t2 = (50 * (t-3));
            t3 = (90 + 50 * (t-3));
            setLegAngles(rear_left,t1,t2,t3)
            setLegAngles(front_left,t1,t2,t3)
            t2=-t2
            t3=-t3
            setLegAngles(front_right,t1,t2,t3)
            setLegAngles(rear_right,t1,t2,t3)
            time.sleep(0.02)
            
        elif(t <= 5):
            t2 = (50 + 20 * (t - 4))
            setLegAngles(rear_left,t1,t2,t3)
            setLegAngles(front_left,t1,t2,t3)
            t2=-t2
            setLegAngles(front_right,t1,t2,t3)
            setLegAngles(rear_right,t1,t2,t3)
            
        else:
            t2 = (70 - 25 * (t - 5));
            t3 = (140 - 50 * (t - 5));
            setLegAngles(rear_left,t1,t2,t3)
            setLegAngles(front_left,t1,t2,t3)
            t2=-t2
            t3=-t3
            setLegAngles(front_right,t1,t2,t3)
            setLegAngles(rear_right,t1,t2,t3)
            
        time.sleep(0.01)
    

### Main code ###
# Set frequency to 60hz, good for servos.
pwm.set_pwm_freq(60)

# Move servo on channel O between extremes.
# Calib()
initial_position()
# getRollPitch_MPU()
# startWalk(60,0,1)


while True:
    ### Dung ngoi (theo initial())
    # all_Move(0,0,-60, 0.025)
    # all_Move(0,0,60, 0.025)
    
    ### chom len, xuong (theo initial())
    # all_Move(30,0,0, 0.025)
    # all_Move(-30,0,0, 0.025)
    # all_Move(-30,0,0, 0.025)
    # all_Move(30,0,0, 0.025)
    
    ### chom trai, phai (theo initial())
    # all_Move(0,30,0, 0.025)
    # all_Move(0,-30,0, 0.025)
    # all_Move(0,-30,0, 0.025)
    # all_Move(0,30,0, 0.025)
    
    ### test all_To_initial()
    all_Move(30,0,60, 0.025)
    time.sleep(1)
    all_Move(0,30,-30, 0.025)
    time.sleep(1)
    all_To_initial(0.025)
    time.sleep(1)
    
    ### forward
    # Walk(60, 0, 0.01)  
      
    ### bachward
    # Walk(-60, 0, 0.01)   
    
    ### move right
    # Walk(0, 40, 0.01) 
    
    ### move left
    # Walk(0, -40, 0.01)    
    
    ###
    # Walk(40, -40, 0.01)  
    # Walk(-40, 40, 0.01)

    # Walk_C(-60,-60,0.01)
    


    
