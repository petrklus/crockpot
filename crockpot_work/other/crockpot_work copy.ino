/*

 AC Light Dimmer v.2 - Inmojo 
 AC Voltage dimmer with Zero cross detection
 
 Author: Charith Fernanado http://www.inmojo.com charith@inmojo.com 
 License: Released under the Creative Commons Attribution Share-Alike 3.0 License. 
 http://creativecommons.org/licenses/by-sa/3.0
 Target:  Arduino
 
 Attach the Zero cross pin of the module to Arduino External Interrupt pin
 Select the correct Interrupt # from the below table
 
 Pin    |  Interrrupt # | Arduino Platform
 ---------------------------------------
 2      |  0            |  All
 3      |  1            |  All
 18     |  5            |  Arduino Mega Only
 19     |  4            |  Arduino Mega Only
 20     |  3            |  Arduino Mega Only
 21     |  2            |  Arduino Mega Only
 
 Please select your utility power frequency from frq variable.
 
 */
#define  fullOn    10
#define  fullOff   127
#define  FQ_50      1 // in case of 50Hz
#define  FQ_60      0 // in case of 50Hz
#define  VER       "2.0"

// digital temp sensor
#include "Wire.h"
//wire library
#define address 0x4d

int inbyte;
int AC_LOAD = 3;    // Output to Opto Triac pin
int dimming = fullOff;  // Dimming level (0-128)  0 = ON, 128 = OFF

boolean frq = FQ_50;     // change the frequency here. 

byte val = 0;

void setup()
{
  pinMode(AC_LOAD, OUTPUT);	      // Set the AC Load as output
  pinMode(7, OUTPUT);	      // we just need another 5V somewhere... 
  digitalWrite(7, HIGH);      // ditto

  attachInterrupt(0, zero_crosss_int, RISING);  // Choose the zero cross interrupt # from the table above
  Serial.begin(115200);
  Wire.begin();
  Serial.println("Starting bitches");
}

void zero_crosss_int()  // function to be fired at the zero crossing to dim the light
{
  // Firing angle calculation
  // 50Hz-> 10ms (1/2 Cycle) → (10000us - 10us) / 128 = 78 (Approx)
  // 60Hz-> 8.33ms (1/2 Cycle) → (8333us - 8.33us) / 128 = 65 (Approx)
  int dimtime = 0;
  float propTime = 0;
  if(frq){
    dimtime = (77*dimming);
    propTime = 10.0; 
  }
  else{
    dimtime = (65*dimming);
    propTime = 8.33; 
  }
  delayMicroseconds(dimtime);    // Off cycle
  digitalWrite(AC_LOAD, HIGH);   // triac firing
  delayMicroseconds(propTime);         // triac On propogation delay
  digitalWrite(AC_LOAD, LOW);    // triac Off

}

long last_time = 0; // last time of reporting
void loop()
{

  if (Serial.available() > 0)
    _serial_int();

  long cur_time = millis();
  if (cur_time - last_time > 2000) {
       // pause in dimming
       detachInterrupt(0); 
    
      Serial.print("[[DP");
      last_time = millis();
      
      int temp_resistor = analogRead(A0);
      // get current temperature from sensor
      Wire.beginTransmission(address);
      //start the transmission
      Wire.write(val);
      int temperature;
   
      Wire.requestFrom(address, 1);
      delay(100);
      if (Wire.available()) {
         temperature = Wire.read();
         Serial.print(temperature);
      } else {
        // TODO shutdown, error state
        Serial.println("No response from temp");
      }
      Serial.print(", ");
      
      Serial.print(temp_resistor);
      Serial.print(", ");
      
      Serial.print(dimming);
      Serial.println("]]");
      if (dimming != fullOff && dimming != fullOn) {
         attachInterrupt(0, zero_crosss_int, RISING);
      }
  }
  

}



void displayMenu() {
  Serial.println(" -------- Crockpot controller (based on InMojo Digital Dimmer v.2) -------- ");
  Serial.println("");
  Serial.println("[m] Menu");
  Serial.println("[2] Set dimming to 50%");
  Serial.println("[1] Turn ON Light");
  Serial.println("[0] Turn OFF Light");
  Serial.println("[v] Version");
  Serial.println("");
}



void _serial_int(){
  while (Serial.available() > 0) {
    inbyte = Serial.read();

    switch (inbyte) {
    case 'm':
      displayMenu(); 
      break;
    case '2':
      dimming = 96;
      attachInterrupt(0, zero_crosss_int, RISING);
      break;  
    case '3':
      dimming = 64;
      attachInterrupt(0, zero_crosss_int, RISING);
      break;    

    case '4':
      dimming = 32;
      attachInterrupt(0, zero_crosss_int, RISING);
      break;    
      
    case '1':
      dimming = fullOn;
      detachInterrupt(0); 
      digitalWrite(AC_LOAD, HIGH); 
      break;      
    case '0':
      dimming = fullOff;
      detachInterrupt(0); 
      digitalWrite(AC_LOAD, LOW); 
      break;       
    case 'v':
      Serial.println(VER);
      break;
    }    

  }
}







