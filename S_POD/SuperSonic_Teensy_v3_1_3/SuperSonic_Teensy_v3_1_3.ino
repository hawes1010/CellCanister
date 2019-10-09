/* ver 1
-Uses Teensy Microcontroller

/* ver 1.1
-modified to run on teensy supersonic pcb
-deleted unused code and comments

/* ver 2
-Added remote time sync command "T" + epoch time ex: T12345678
-Added canister valve control 
-Added trigger EEPROM storage. Set by "C" + setpoint (in counts) ex: C8024
-Added Canister Arm EEPROM Storage. Set by "D" + 1 or 0 ex: D1 (arms canaster)

/* ver 2.1
-Added menu using command "?"
-Added EEPROM storage for sample time "Sxxxxx" ex: S60
Added EEPROM storage for PID averageing points "Axxx" ex: A30

/*ver 2.2
-work around for BMP sensor failure

/*ver 2.3
-Added can on/off to logging and xbee output
-fixed can trigger

/*ver 2.4
-Added SPOD serial number prefix

/*ver 3.0
-telemety is now polled

/*ver 3.1
-Address of SPOD is a declared variable changed in one location

/*ver 3.1.1
-Fixed sonic droped packet rate



  SD card datalogger with time stamp
***************************************************************
Adafruit micro-SD card info:	
*SD Card attached to the SPI bus as follows:
** MOSI - pin D12
** MISO - pin D11 
** CLK - pin D13
** CS - pin D6
 
// Note that even if it's notused as the CS pin, 
// the hardware CS pin (17 on the Fio v3) 
// must be left as an output or the SD library
// functions will not work.
 
 **************************************************************
 	 
 */

#include <SD.h>    //SD card library
#include <Wire.h>  //IC2 library
#include <Time.h>  //Used for rtc
#include <SPI.h>  //Used for RTC
#include <Adafruit_Sensor.h>  //BP&T Sensor
#include <Adafruit_BMP085_U.h> //BP&T Sensor
#include <EEPROM.h>

Adafruit_BMP085_Unified bmp = Adafruit_BMP085_Unified(10085);

const int chipSelect = 6;  //SD card chip select pin

unsigned long startrate;  //Sample rate timer


int pidarray[300];               // the pid readings from the analog input
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



void setup()
{
  pinMode(2, OUTPUT);
  digitalWrite(2, LOW);
  
  for (int thisReading = 0; thisReading < 15; thisReading++) //set array to zero
    pidarray[thisReading] = 0;          
    
  setSyncProvider(getTeensy3Time); // Call Teensy RTC subroutine
  
  analogReadRes(16); // Set Teensy analog read resolution to 16 bits
  
 // Open serial communications and wait for port to open:
  Serial.begin(9600);    //open Serial port
  Serial1.begin(38400);  //open Sonic port
  Serial2.begin(57600);  //open Xbee port
 
  startrate = millis(); // start timer
  
 // Init pressure sensor
   if(!bmp.begin())
  {
    /* There was a problem detecting the BMP085 ... check your connections */
    Serial2.println("Ooops, no BMP085 detected ... Check your wiring or I2C ADDR!");
   nobmp = 1;   
  }

  Wire.begin();

  //init SD card
  Serial2.print("Initializing SD card...");
  // make sure that the default chip select pin is set to
  // output, even if you don't use it:
  pinMode(6, OUTPUT); 
  // see if the card is present and can be initialized, pins must be in order(SS, MOSI, MISO, CLK):
  if (!SD.begin(6)) {
    Serial2.println("Card failed, or not present");
    // don't do anything more:
    return;
  }
  Serial2.println("card initialized.");
  //end SD card init
}

String winln; //sonic String
char win; //sonic build char
String sonics = ""; //sonic string holder
String datapac; //data packet string
    
void loop() 
{  
 sonic(); //get sonic string
  if ((millis()-startrate) > 900){    //check sample timer
   
   getLogger(); // logging subroutine
  }
  //delay(100);
//menu begin**************************************************  
  if (Serial2.available()) {
    char address = Serial2.read(); 
   if (address == maddress){               //if first char = main address then exicute menu change
   if (Serial2.available()) { 
    char header = Serial2.read();
   if (header == 84) {               //if first char = T set clock
    time_t t = processSyncMessage(); //call processSyncMessage subroutine & return "t"
     if (t != 0) {
      Teensy3Clock.set(t); // set the RTC
      setTime(t);
      Serial2.print("CLOCK SET TO: ");
      Serial2.print(month());
      Serial2.print("/");
      Serial2.print(day());
      Serial2.print("/");
      Serial2.print(year());
      Serial2.print(" ");
      Serial2.print(hour());
      Serial2.print(":");
      Serial2.print(minute());
      Serial2.print(":");
      Serial2.println(second());
      Serial2.println();
     }
   }
   
   else if (header == 67){       // if header = C set trigger level
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
   
   else if(header == 65){        // if header = A set trigger average time
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
   
   else if(header == 68){        //if header = D arm/disarm trigger
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
   
   else if (header == 83){      //if header = S set sample time
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

   else if (header == 82){      //if header = R send data string to xbee
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

   
   else if (header == 88){      //if header = X exit menu
    //men = 0;
   }
   
    else if(header == 63){      //if header = ? display menu
    
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
   }
  }
  Serial2.clear();
 
  }
//menu end**************************************************** 

}

void sonic() {      // begin assemble Sonic string for log: **************************
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
// end Sonic input ***********************************************

void getLogger() { 
  
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


//file date / name generator:
void getFilename(char *filename) {
    filename[0] = '2';
    filename[1] = '0';
    filename[2] = int(year()/10)%10 + '0';
    filename[3] = year()%10 + '0';
    filename[4] = month()/10 + '0';
    filename[5] = month()%10 + '0';
    filename[6] = day()/10 + '0';
    filename[7] = day()%10 + '0';
    filename[8] = '.';
    filename[9] = 'C';
    filename[10] = 'S';
    filename[11] = 'V';
    return;
  }
  
  time_t getTeensy3Time() //RTC subroutine
{
  return Teensy3Clock.get();
}
 
/*  code to process time messages from the serial port   */
//#define TIME_HEADER  "T"   // Header tag for serial time sync message

unsigned long processSyncMessage() {
  unsigned long pctime = 0L;
  const unsigned long DEFAULT_TIME = 1357041600; // Jan 1 2013 

  
     pctime = Serial2.parseInt();
     return pctime;
     if( pctime < DEFAULT_TIME) { // check the value is a valid time (greater than Jan 1 2013)
       pctime = 0L; // return 0 to indicate that the time is not valid
     }
    return pctime; 
  }
  

