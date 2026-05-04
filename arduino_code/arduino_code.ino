#include <Keypad.h>

const byte ROWS = 4;
const byte COLS = 4;

char keys[ROWS][COLS] = {
  {'1','2','A','3'},
  {'4','5','B','6'},
  {'7','8','C','9'},
  {'*','0','D','#'}
};

byte rowPins[ROWS] = {9, 8, 7, 6}; // R1-R4
byte colPins[COLS] = {5, 4, 3, 2}; // C1-C4

const char password[] = "2018A";
char inputBuffer[6];
byte indexPos = 0;

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

void setup() {
  Serial.begin(9600);
  pinMode(12, OUTPUT);
  digitalWrite(12, LOW);
}

void loop() {
  char key = keypad.getKey();

  if (key) {
    Serial.print("Key Pressed: ");
    Serial.println(key);

    if (key == '#') {
      Serial.println("Input cleared");
      indexPos = 0;
      memset(inputBuffer, 0, sizeof(inputBuffer));
      return;
    }

    inputBuffer[indexPos] = key;
    indexPos++;

    if (indexPos == strlen(password)) {
      inputBuffer[indexPos] = '\0';

      if (strcmp(inputBuffer, password) == 0) {
        Serial.println("Password correct");
        digitalWrite(12, HIGH);
        delay(2000);
        digitalWrite(12, LOW);
      } else {
        Serial.println("Wrong password");
        digitalWrite(12, LOW);
      }

      indexPos = 0;
      memset(inputBuffer, 0, sizeof(inputBuffer));
    }
  }

  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == '1') digitalWrite(12, HIGH);
    else if (cmd == '0') digitalWrite(12, LOW);
  }
}
