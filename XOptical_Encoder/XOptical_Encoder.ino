#include <Wire.h>

// Interrupt Optical Encoder Code

static int pinA = 2; // Our first hardware interrupt pin is digital pin 2
static int pinB = 3; // Our second hardware interrupt pin is digital pin 3
volatile byte aFlag = 0; // let's us know when we're expecting a rising edge on pinA to signal that the encoder has arrived at a detent
volatile byte bFlag = 0; // let's us know when we're expecting a rising edge on pinB to signal that the encoder has arrived at a detent (opposite direction to when aFlag is set)
int XencoderPos = 0; //this variable stores our current value of the X encoder position. Change to int or uin16_t instead of byte if you want to record a larger range than 0-255
int YencoderPos = 0; //this variable stores our current value of the Y encoder position. Change to int or uin16_t instead of byte if you want to record a larger range than 0-255
volatile byte XoldEncPos = 0; //stores the last encoder position value so we can compare to the current reading and see if it has changed (so we know when to print to the serial monitor)
volatile byte YoldEncPos = 0; //stores the last encoder position value so we can compare to the current reading and see if it has changed (so we know when to print to the serial monitor)
volatile byte reading = 0; //somewhere to store the direct values we read from our interrupt pins before checking to see if we have moved a whole detent
byte incoming_register; // the incoming register
byte REGISTER_ENC_POS = 0x02;

void setup() {
  pinMode(pinA, INPUT_PULLUP); // set pinA as an input, pulled HIGH to the logic voltage (5V or 3.3V for most cases)
  pinMode(pinB, INPUT_PULLUP); // set pinB as an input, pulled HIGH to the logic voltage (5V or 3.3V for most cases)
  attachInterrupt(0, PinA, CHANGE); // set an interrupt on PinA, looking for a rising edge signal and executing the "PinA" Interrupt Service Routine (below)
  attachInterrupt(1, PinB, CHANGE); // set an interrupt on PinB, looking for a rising edge signal and executing the "PinB" Interrupt Service Routine (below)
  Serial.begin(115200); // start the serial monitor link
  Wire.begin();
  // Wire.onReceive(receiveEvent);
  //  Wire.onRequest(requestEvent);
}

void PinA() {
  cli(); //stop interrupts happening before we read pin values (same as noInterrupts())
  reading = PIND & 0xC; // read all eight pin values then strip away all but pinA and pinB's values
  if (reading == B00001100 && aFlag) { //check that we have both pins at detent (HIGH) and that we are expecting detent on this pin's rising edge
    XencoderPos --; //decrement the encoder's position count
    bFlag = 0; //reset flags for the next turn
    aFlag = 0; //reset flags for the next turn
  }
  else if (reading == B00000100) bFlag = 1; //signal that we're expecting pinB to signal the transition to detent from free rotation
  sei(); //restart interrupts (same as Interrupts())
}

void PinB() {
  cli(); //stop interrupts happening before we read pin values (same as noInterrupts())
  reading = PIND & 0xC; //read all eight pin values then strip away all but pinA and pinB's values
  if (reading == B00001100 && bFlag) { //check that we have both pins at detent (HIGH) and that we are expecting detent on this pin's rising edge
    XencoderPos ++; //increment the encoder's position count
    bFlag = 0; //reset flags for the next tu
    aFlag = 0; //reset flags for the next turn
  }
  else if (reading == B00001000) aFlag = 1; //signal that we're expecting pinA to signal the transition to detent from free rotation
  sei(); //restart interrupts (same as Interrupts())
}

void loop() {
  byte a, b; // bytes for buffering incoming i2c values
  int bigNum, smallNum; // values for manipulating incoming i2c values
  Wire.requestFrom(0x40, 2); // ask arduino at address 0x40 for 2 bytes of data
  while (Wire.available()) { // start a while loop and keep it open for as long as there is an incoming data packet
    a = Wire.read();
    b = Wire.read();
    smallNum = a;
    YencoderPos = smallNum << 8 | b;
    Serial.print(XencoderPos); // Send the x encoder position value to the pi
    Serial.print(",");
    Serial.println(YencoderPos); // Send the y encoder position value ot the pi
  }
  delay(50); // pull at a rate of 20Hz
}
