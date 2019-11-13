/*
SPod.h
*/
#include "SPod.h"
#include "Arduino.h"
#define PID_READINGS 300
#include <EEPROM.h>

#include <SD.h>    //SD card library
#include <Wire.h>  //IC2 library
#include <Time.h>  //Used for rtc
#include <SPI.h>  //Used for RTC
#include <Adafruit_Sensor.h>  //BP&T Sensor
#include <Adafruit_BMP085_U.h> //BP&T Sensor
#include <EEPROM.h>
// Constructor
Spod::Spod()
{
  // initialize this instance's variables
int pidarray[PID_READINGS];               // the pid readings from the analog input
int pidindex = 0;                  // the index of the current reading
int pidtot = 0;                  // the running total
int pidave = 0;                // the average
int trigger;                // canaster trigger level in 16int counts 
int ena;                    // canaster arm enable 0 or 1
int ave;
int can;
int z = 0;
int x = 0;
int men = 0;
int nobmp = 0;              //BMP sensor error flag
int pressure;
float temperature = 0;
int HUM;
int pid;
char maddress = 'd';  // ****CHANGE ADDRESS OF SPOD HERE****
  if (!Serial){
  Serial.begin(9600);    //open Serial port
  }
if (!Serial1){
  Serial1.begin(38400);  //open Sonic port
}
if (!Serial2){
  Serial2.begin(57600);  //open Xbee port
}
}
//PRIVATE FUNCTIONS


// PUBLIC FUNCTIONS

void SPod::getLogger() { 

  
// begin analog input ******************************************
  pid = analogRead(0); // PID labeled A0
  HUM = analogRead(1); // humidity labeled A1
// end analog input ********************************************

//PID can trigger start*************************************
EEPROM.get(100,ena);        //get enable from memory
EEPROM.get(200,ave);        // get trigger level average from memory
//Serial.println(ena);
if (ena == 1){          //run if enabled

  pidtot= pidtot - pidarray[pidindex];     // subtract the last reading:     
  pidarray[pidindex] = pid;                // read from the sensor:   
  pidtot= pidtot + pidarray[pidindex];      // add the reading tDo the total:   
  pidindex = pidindex + 1;             // advance to the next position in the array:   
  if (pidindex >= ave){   pidindex = 0; }    // if at the end of the array, zero
  pidave = pidtot / ave;         // calculate the average:
    
  EEPROM.get(0,trigger);        // get trigger level from memory
  EEPROM.get(300,can);        // get trigger level average from memory
  //Serial.println(trigger);
  int trig = trigger * 18;      // convert ppb to int15
  
  if (pidave > trig) {          //open can if pid average is above trigger level
    digitalWrite(2, HIGH);
    x = 1;
  } 
  if(x == 1){
    z = z + 1;  
    if (z > can) {                //keep can open for can seconds
      digitalWrite(2,LOW);        //close can
      EEPROM.put(100,0);            //set enable to zero and store in memory
      z = 0;
      x = 0;
      for (int thisReading = 0; thisReading < 15; thisReading++) //set array to zero
       pidarray[thisReading] = 0; 
      pidave = 0; pidindex = 0; pidtot = 0;
    }
  } 
}
else{
     digitalWrite(2,LOW);        //close can
      z = 0;
      x = 0;
      for (int thisReading = 0; thisReading < ave; thisReading++) //set array to zero
       pidarray[thisReading] = 0; 
      pidave = 0; pidindex = 0; pidtot = 0;
}
//PID can trigger end***************************************  

// begin pressure and temp**************************************
  if (nobmp == 0){
    sensors_event_t event;
    bmp.getEvent(&event);    
    pressure = (event.pressure);
    bmp.getTemperature(&temperature);
  }         
// End pressure and temp****************************************    

//Begin Write data to file *************************************   
  // open file. note that only one file can be open at a time,
  // so you have to close this one before opening another.
     char filename[] = "00000000.CSV"; //default file name
     getFilename(filename); //daily file name
     File dataFile = SD.open(filename, FILE_WRITE);
  // if the file is available, write to it:
    if (dataFile) {        
      //write to file
      dataFile.print(maddress); //Station Serial #
      dataFile.print(", ");
      dataFile.print(month());
      dataFile.print("/");
      dataFile.print(day());
      dataFile.print("/");
      dataFile.print(year());
      dataFile.print(", ");
      dataFile.print(hour());
      dataFile.print(":");
      dataFile.print(minute());
      dataFile.print(":");
      dataFile.print(second());
      dataFile.print(", ");      
      dataFile.print(pid); //write PID
      dataFile.print(", ");
      dataFile.print(temperature); //write temperature
      dataFile.print(", ");
      dataFile.print(HUM); //write humidity
      dataFile.print(", ");      
      dataFile.print(pressure); //write pressure 
      dataFile.print(", ");
      dataFile.print(x); //write can open/close 
      dataFile.print(", ");
      dataFile.println(sonics); //write Sonic string
      dataFile.close(); //close file          
      
   // print to the USB serial port for debug purposes. Uncomment to use
      //Serial.print("SS1"); //Station Serial #
      //Serial.print(", ");
      Serial.print(hour());
      Serial.print(":");
      Serial.print(minute());
      Serial.print(":");
      Serial.print(second());
      Serial.print(", ");
      Serial.print(maddress); //output with 4 dec.places
      //Serial.print(", ");
      //Serial.print(ena); //output with 4 dec.places
      //Serial.print(", ");
      //Serial.print(x); //output with 4 dec.places
      //Serial.print(", ");
      //Serial.print(trigger); //output with 4 dec.places
      //Serial.print(", ");
      //Serial.print(pressure); //output with 4 dec.places
      //Serial.print(", ");
      Serial.println(sonics);
     
    }  
     //if the file isn't open, pop up an error:
    else {
      Serial2.println("error opening datalog file");
    }
// End write data to file  ************************************

 

startrate = millis(); // reset timer
}


void Spod::sonic() {      // begin assemble Sonic string for log: **************************
 Serial1.clear(); //clear sonic port
 winln = "";  //clear Sonic string
 Serial1.println("MA!");  //send Sonic poll char.
  delay(350);
  while (Serial1.available() > 0) {
   char win = {Serial1.read()}; // read Sonic char.
   if (win == 13){
    sonics = winln; 
    break; //if Sonic char = CR then end while loop
   } 
    winln = winln + win;  //build Sonic string  
    //delay(5);
  }
 
}
void SPod::read_C(){
	int trigger = 250;
    trigger = Serial2.parseInt();
    if (trigger <= 2000 && trigger >= 1){
     EEPROM.put(0,trigger);
     Serial2.print("TRIGGER SET TO: ");
     Serial2.println(trigger);
     Serial2.println();
    }
    else{
      EEPROM.put(0,250);
      Serial2.println("TRIGGER LEVEL OUT OF RANGE (1 TO 2000");
      Serial2.println("TRIGGER LEVEL SET TO DEFAULT OF 250");
      Serial2.println();
    }
   }
}
void Spod::read_A(){
	 ave = 10;
    ave = Serial2.parseInt();
    if (ave <= 300 && ave >= 1){
     EEPROM.put(200,ave);
     Serial2.print("TRIGGER AVERAGE SET TO: ");
     Serial2.println(ave);
     Serial2.println();
    }    
    else{
      EEPROM.put(200,10);
      Serial2.println("TRIGGER AVERAGE OUT OF RANGE (1 TO 300)");
      Serial2.println("TRIGGER AVERAGE SET TO 10 ");
      Serial2.println();      
    }  
}
void Spod::read_D(){
	int ena = 0;
    ena = Serial2.parseInt();
    if (ena == 0 || ena == 1){
    EEPROM.put(100,ena);
     if (ena == 1){
      Serial2.println("CANASTER TRIGGER ARMED");
      Serial2.println();
      Serial2.clear();
     }
     else{
       Serial2.println("CANASTER TRIGGER DISARMED");
       Serial2.println();
       //Serial2.clear();
     }
    }
}
void Spod::read_S(){
	 can = 60;
    can = Serial2.parseInt();
    if (can <= 86400 && can >= 1){
     EEPROM.put(300,can);
     Serial2.print("CANASTER SAMPLE TIME SET TO: ");
     Serial2.println(can);
     Serial2.println();
     //Serial2.clear();
    }
    else{
       Serial2.println("CANASTER SAMPLE TIME OUT OF RANGE (1 TO 86400)");
       Serial2.println("CANASTER SAMPLE TIME SET TO DEFAULT 60");
       Serial2.println();
       Serial2.clear();
    } 
}
void Spod::read_R(){
 String mo = month();
        String dy = day();
        String ye = year();
        String ho = hour();
        String mi = minute();
        String se = second();
        datapac =  ", " + mo + "/" + dy + "/" + ye + ", " + ho + ":" + mi + ":" + se + ", " + pid + ", " + temperature + ", " + HUM + ", " + pressure + ", " + x + ", " + sonics;
        Serial2.print(maddress); //Station Serial #
        Serial2.println(datapac); //data pack
        Serial2.flush(); //clear sonic port
}
void Spod::read_?(){
	 Serial2.println("SUPER SONIC MENU:");
    Serial2.println();
    Serial2.print("  ");
    Serial2.print(maddress);
    Serial2.println("Txxxxx TO SET TIME (xxxx = EPOCH TIME). EX: aT12345678");
    Serial2.println();
    Serial2.print("  ");
    Serial2.print(maddress);
    Serial2.println("Cxxxx TO SET CANASTER TRIGGER LEVEL (1 ppb to 2000 ppb). EX: aC350");
    Serial2.println();
    Serial2.print("  ");
    Serial2.print(maddress);    
    Serial2.println("Dx TO ARM CANASTER TRIGGER. 0 (OFF) OR 1 (ARMED). EX: aD1");
    Serial2.println();
    Serial2.print("  ");
    Serial2.print(maddress);    
    Serial2.println("Sxxxxx TO SET CANASTER SAMPLE TIME IN SECONDS (1 to 86400). EX: aS300");
    Serial2.println();
    Serial2.print("  ");
    Serial2.print(maddress);    
    Serial2.println("Axxx TO SET CANASTER TRIGGER LEVEL AVERING TIME IN SECONDS (1 to 300). EX: aA60");
    Serial2.println();
    Serial2.print("  ");
    Serial2.print(maddress);
    Serial2.println("R SENDS DATA PACKET");
    Serial2.println();    
    Serial2.print("  ");
    Serial2.print(maddress);    
    Serial2.println("? THIS MENU");
    Serial2.println();
    Serial2.print("  ");
    Serial2.print(maddress);    
    Serial2.println("X TO EXIT MENU");
    Serial2.println();
}



