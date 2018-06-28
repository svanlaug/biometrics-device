# Under Construction!

My hopes with this repo are that people will be able to build upon this work, and start quantifying their biometrics.

## Improvements I need to do
- [ ] Put in instructions how to install the required Python packages to run the Python GUI. (as soon as I manage to install them myself, it's been 3 years since I did last time) - Remarkably hard
- [ ] Put in instructions how to build a biosignal aqusition device (the hardware), what parts are needed etc
- [ ] Put in wisdom about biosignals 
- [ ] Put in example csv files, and put in my Matlab scripts I made to process them

## Background: 
I wrote my M.Sc. thesis in collaboration with SoundCloud, a company that creates an open platform that allows anyone to share and discover new music and audio. At the time, wearables were becoming increasingly available and ...

My M.Sc. thesis explored the relation between physiological signals and experienced musical emotions from a practical viewpoint. This was done in order to evaluate the feasibility of using physiological signals as input for music recommendations. For this purpose I conducted a study on 24 participants where their subjective and physiological measurements were recorded while they listened to self-selected musical stimuli. When I conducted the study, in January 2016, wearables on the market were not sparse, but their sensors however were very limited and their public API was not great. That's why, I built my own biosignal aquicsition device, to get full access to the raw data from sensors and to be able to determine the sampling frequency. 

![The beautiful device](https://user-images.githubusercontent.com/6841437/42059438-6168bb36-7b1b-11e8-8f8c-811e8cdc0b79.png)

## Atmel Microcontroller 
Atmel code is split into 3 files;

1. **Main Code.ino:** Is the main file. It reads digital inputs from buttons and writes measurement data to the LCD display. It also calculates temperature from raw data from the temperature sensor. 

2. **Interrupt.ino:** Reads the analog inputs for Galvanic Skin Response (GSR) and pulse at specific time intervals. Calculates Interbeat Interval (IBI) as well.

3. **AllSerialHandling.ino:** Controls how the data is sent over the serial link to the Python GUI.

## Python GUI
![The GUI](https://user-images.githubusercontent.com/6841437/42060712-a5e90dca-7b1f-11e8-80dc-63f47b8d02b0.png)

The Python GUI is split into 3 files; 

1. **AtmelPythonMainProgram.py:** Is the main file. It builds the user interface and writes data to a CSV file.

2. **Comunication.py:** Controls the communication over serial link.

3. **Globals.py:** Global variables and debug tools.

To run the Python GUI for a biosignal acquisition device:
1. Install [pySerial](http://pyserial.readthedocs.io/en/latest/pyserial.html) + all the other Python packages that is remarkably hard to do
2. Clone the project to your computer
3. Navigate to the folder that contains the code for the Python GUI in the terminal: 
4. Run the program: `$ python AtmelPythonMainProgram.py`
