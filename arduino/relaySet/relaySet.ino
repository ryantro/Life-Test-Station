String incomingStr;


#define E1 9
#define E2 2 
#define E3 3
#define E4 4
#define E5 5
#define E6 6  

const byte numChars = 32;
char receivedChars[numChars];
boolean newData = false;
boolean isMoving = false;

void setup() {
  
  // configure pins to controll the stepper motor
  
  pinMode(E1,OUTPUT);  
  pinMode(E2,OUTPUT);  
  pinMode(E3,OUTPUT);  
  pinMode(E4,OUTPUT);  
  pinMode(E5,OUTPUT);  
  pinMode(E6,OUTPUT);  
  allOpen();
  Serial.begin(9600);



}
/////



void loop() {
    recvWithStartEndMarkers();
    showNewData();
}

void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;
 
    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}

void showNewData() {
    if (newData == true) {
        //Serial.print("This just in ... ");
        //Serial.println(receivedChars);
        parseStr(receivedChars); 
        newData = false;
    }
}


/*
void loop() {
  handleSerial();
}
*/

/*
 * Function: handleSerial
 * ----------------------------
 * reads the serial input.
 */
void handleSerial() {
  
  while (Serial.available() > 0) {

  const char fda = '\n';
  
  incomingStr = Serial.readStringUntil('\r');  // read until timeout
  incomingStr.trim();                            // remove and \r \n whitespace at the end of the String
  parseStr(incomingStr);                         // parse the incoming String
  
 }
}





/*
 * Function: parseStr
 * ----------------------------
 * parses the input string read in through serial
 */
void parseStr(String command){

  /*
   * Check for relative movement command
   */
  if (command.indexOf("CLOSE") != -1) {
    int index = command.indexOf(" ");           // split string
    String sub_s = command.substring(index,-1); // find number of pulses
    sub_s.trim();                               // trim str
    int i = sub_s.toInt();                      // convert str to int
    
    switch (i) {
      case 0:
        digitalWrite(E1,HIGH);
        digitalWrite(E2,HIGH);
        digitalWrite(E3,HIGH);
        digitalWrite(E4,HIGH);
        digitalWrite(E5,HIGH);
        digitalWrite(E6,HIGH);
        break;
      case 1:
        digitalWrite(E1,HIGH);
        break;
      case 2:
        digitalWrite(E2,HIGH);
        break;
      case 3:
        digitalWrite(E3,HIGH);
        break;
      case 4:
        digitalWrite(E4,HIGH);
        break;
      case 5:
        digitalWrite(E5,HIGH);
        break;
      case 6:
        digitalWrite(E6,HIGH);
        break;

      default:
        // if nothing else matches, do the default
        // default is optional
        break;
      }
 

    // print stage position
    // Serial.println(sub_s.length());
    
    return;
  }


  
  if (command.indexOf("OPEN") != -1) {
    int index = command.indexOf(" ");           // split string
    String sub_s = command.substring(index,-1); // find number of pulses
    sub_s.trim();                               // trim str
    int i = sub_s.toInt();                      // convert str to int
    
    switch (i) {
      case 0:
        digitalWrite(E1,LOW);
        digitalWrite(E2,LOW);
        digitalWrite(E3,LOW);
        digitalWrite(E4,LOW);
        digitalWrite(E5,LOW);
        digitalWrite(E6,LOW);
        break;
      case 1:
        digitalWrite(E1,LOW);
        break;
      case 2:
        digitalWrite(E2,LOW);
        break;
      case 3:
        digitalWrite(E3,LOW);
        break;
      case 4:
        digitalWrite(E4,LOW);
        break;
      case 5:
        digitalWrite(E5,LOW);
        break;
      case 6:
        digitalWrite(E6,LOW);
        break;

      default:
        // if nothing else matches, do the default
        // default is optional
        break;
    }
 

    // print stage position
    // Serial.println(sub_s.length());
    
    return;
  }

if (command.indexOf("Q") != -1) {
    digitalWrite(E1,LOW);
    digitalWrite(E2,LOW);
    digitalWrite(E3,LOW);
    digitalWrite(E4,LOW);
    digitalWrite(E5,LOW);
    digitalWrite(E6,LOW);
    return;
  }


  /* TODO:
   * command to zero the system
   */
  if (command.indexOf("W") != -1) {
    digitalWrite(E1,HIGH);
    digitalWrite(E2,HIGH);
    digitalWrite(E3,HIGH);
    digitalWrite(E4,HIGH);
    digitalWrite(E5,HIGH);
    digitalWrite(E6,HIGH);
    return;
  }

  //Serial.println("ERROR");

}

void allOpen(){
  digitalWrite(E1,LOW);
    digitalWrite(E2,LOW);
    digitalWrite(E3,LOW);
    digitalWrite(E4,LOW);
    digitalWrite(E5,LOW);
    digitalWrite(E6,LOW);
}


