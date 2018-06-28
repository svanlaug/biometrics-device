#include <SoftwareSerial.h>
#include <OneWire.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#define I2C_ADDR 0x27 //LCD address
#define Rs_pin 0
#define Rw_pin 1
#define En_pin 2
#define BACKLIGHT_PIN 3
#define D4_pin 4
#define D5_pin 5
#define D6_pin 6
#define D7_pin 7
LiquidCrystal_I2C lcd(I2C_ADDR,En_pin,Rw_pin,Rs_pin,D4_pin,D5_pin,D6_pin,D7_pin);
#define LED 9
#define SERIAL_BAUD   19200

OneWire myds(2); //Pin for thermometer
byte readstage;
byte resolution;
unsigned long starttime;
unsigned long elapsedtime;
byte dsaddr[8];

// Pins
const int GSR = A6;
int pulsePin = 0;                 // Pulse Sensor datawire
int blinkPin = 13;                // pin to blink led at each beat
const int buttonPin = 8;          // the number of the pushbutton pin
const int resetButtonPin = 7;     // the number of the pushbutton pin

//  Variables
int ledState = HIGH;              // the current state of the output pin
int buttonState;                  // the current reading from the input pin
int resetButtonState;             // the current reading from the input pin
int lastButtonState = LOW;        // the previous reading from the input pin
int lastButtonState2 = LOW;       // the previous reading from the input pin
long lastDebounceTime = 0;        // the last time the output pin was toggled
long lastDebounceTime2 = 0;       // the last time the output pin was toggled
long debounceDelay = 50;          // the debounce time

// Volatile Variables, used in the interrupt service routine!
volatile int BPM;                   // int that holds raw Analog in 0. updated every 2mS
volatile int Signal;                // holds the incoming raw data
volatile int IBI = 600;             // int that holds the time interval between beats! Must be seeded! 
volatile boolean Pulse = false;     // "True" when User's live heartbeat is detected. "False" when not a "live beat". 
volatile boolean QS = false;        // becomes true when Arduoino finds a beat.

// Regards Serial OutPut  -- Set This Up to your needs
static boolean serialVisual = false;   // Set to 'false' by Default.  Re-set to 'true' to see Arduino Serial Monitor ASCII Visual Pulse 

// Misc. parameters
boolean BackLightLCD = true;
volatile int sensorValue;
unsigned long previousMillis = 0;        
unsigned long previousMillisLCD = 0;        
const long interval = 250; 
const long intervalLCD = 700; // Refresh rate of the LCD
unsigned long StartTime = 0;
unsigned long EndTime = 0;
long teljari = 0;
float hiti = 0;


void setup(){
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(resetButtonPin, INPUT_PULLUP);
  Serial.begin(19200);             // Serial communication speed
  interruptSetup();                // sets up to read Pulse Sensor signal every 2mS 
  readstage = 0;                   // Current readstage
  resolution = 12;                 //Thermometer temperature resolution

  lcd.begin (20,4);                // initialize the lcd
  
// Switch on the backlight
  lcd.setBacklightPin(BACKLIGHT_PIN,POSITIVE);
  lcd.setBacklight(BackLightLCD);

// LCD Welcome Message
  lcd.home ();
  lcd.print("    Starting up"); 
  lcd.setCursor (0,1);
  lcd.print(" Svana's Biometrics"); 
  lcd.setCursor (0,2);
  lcd.print("        V0.7");
  delay(3500);
  lcd.clear();
}


void loop(){
  sendDataToSerial('Y',teljari);
  StartTime = millis(); //Measurement of Arduino loop speed
   
//************************Button logic******************
  int reading = digitalRead(buttonPin);

  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {

    if (reading != buttonState) {
      buttonState = reading;

      if (buttonState == HIGH) {
        teljari = teljari + 1;
      }
    }
  }

  // save the reading.  Next time through the loop,
  // it'll be the lastButtonState:
  lastButtonState = reading;
  
//************************Button logic******************

//************************Reset Button logic******************
  int reading2 = digitalRead(resetButtonPin);
  
  if (reading2 != lastButtonState2) {
    lastDebounceTime2 = millis();
  }

  if ((millis() - lastDebounceTime2) > debounceDelay) {
    if (reading2 != resetButtonState) {
      resetButtonState = reading2;

      if (resetButtonState == HIGH) {
        if (BackLightLCD == HIGH) {
          BackLightLCD = LOW;
        }
        else {
          BackLightLCD = HIGH;
        }
        }
      }
   }
  
  lastButtonState2 = reading2;
  
//************************Button logic******************

//************************LCD logic******************
  if (millis() - previousMillisLCD >= intervalLCD) {
     lcd.setCursor (0,0);
     lcd.print("BPM: ");
     lcd.print(BPM);
     lcd.print("  ");
     lcd.setCursor (9,0); 
     lcd.print("IBI: ");
     lcd.print(IBI);
     lcd.print("ms");
     lcd.print(" ");

     lcd.setCursor (0,1);
     lcd.print("Temp: ");
     lcd.print(hiti);
     lcd.print((char)223);
     lcd.print("C");
     
     lcd.setCursor (0,2);
     lcd.print("Raw GSR: ");
     lcd.print(sensorValue);
     lcd.print("  ");

     lcd.setCursor (0,3);
     lcd.print("Measurement: ");
     lcd.print((char)35);
     lcd.print(teljari);
     lcd.print("  ");
     
     previousMillisLCD = millis();
  }

//************************LCD logic******************


//************************GSR logic******************
  sendDataToSerial('G',sensorValue);
//************************GSR logic******************

//************************Temperature logic******************

  if (readstage == 0){
      getfirstdsadd(myds,dsaddr);
      dssetresolution(myds,dsaddr,resolution);
      dsconvertcommand(myds,dsaddr);
      readstage++;
    }
  else {
      if (myds.read()) {
        hiti = dsreadtemp(myds,dsaddr, resolution);
        sendDataToSerialReal('T',hiti);
        readstage=0;
      }
  }
    serialOutput() ;       
//************************Temperature logic******************


  if (QS == true){     // A Heartbeat Was Found
        serialOutputWhenBeatHappens();   // A Beat Happened, Output that to serial.     
        QS = false;                      // reset the Quantified Self flag for next time    
  }
   

  EndTime = millis();
  sendDataToSerial('C',EndTime-StartTime); //Send looptime to serial

}

// Method to find the I2C address of the thermometer or LCD
void getfirstdsadd(OneWire myds, byte firstadd[]){
  byte i;
  byte present = 0;
  byte addr[8];
  float celsius, fahrenheit;
  
  int length = 8;
  
  //Serial.print("Looking for 1-Wire devices...\n\r");
  while(myds.search(addr)) {
    //Serial.print("\n\rFound \'1-Wire\' device with address:\n\r");
    for( i = 0; i < 8; i++) {
      firstadd[i]=addr[i];
      if (addr[i] < 16) {

      }

      if (i < 7) {
      }
    }
    if ( OneWire::crc8( addr, 7) != addr[7]) {
        Serial.print("CRC is not valid!\n");
        return;
    }
    
    return;
  } 
}

//Method to set the resolution of the themometer
void dssetresolution(OneWire myds, byte addr[8], byte resolution) {
    
  // Get byte for desired resolution
  byte resbyte = 0x1F;
  if (resolution == 12){
    resbyte = 0x7F;
  }
  else if (resolution == 11) {
    resbyte = 0x5F;
  }
  else if (resolution == 10) {
    resbyte = 0x3F;
  }
  
  // Set configuration
  myds.reset();
  myds.select(addr);
  myds.write(0x4E);         // Write scratchpad
  myds.write(0);            // TL
  myds.write(0);            // TH
  myds.write(resbyte);         // Configuration Register
  
  myds.write(0x48);         // Copy Scratchpad
}

void dsconvertcommand(OneWire myds, byte addr[8]){
  myds.reset();
  myds.select(addr);
  myds.write(0x44,1);         // start conversion, with parasite power on at the end
  
}

//This method reads the temperature from the thermometer
float dsreadtemp(OneWire myds, byte addr[8], byte resolution) {
  byte present = 0;
  int i;
  byte data[12];
  byte type_s;
  float celsius;
  type_s = 0;

  
  present = myds.reset();
  myds.select(addr);    
  myds.write(0xBE);        

  for ( i = 0; i < 9; i++) {           
    data[i] = myds.read();
  }

  unsigned int raw = (data[1] << 8) | data[0];
  if (type_s) {
    raw = raw << 3; // 9 bit resolution default
    if (data[7] == 0x10) {
      raw = (raw & 0xFFF0) + 12 - data[6];
    } else {
      byte cfg = (data[4] & 0x60);
      if (cfg == 0x00) raw = raw << 3; 
        else if (cfg == 0x20) raw = raw << 2; 
        else if (cfg == 0x40) raw = raw << 1; 
    }
  }
  celsius = (float)raw / 16.0;
  return celsius;
}




