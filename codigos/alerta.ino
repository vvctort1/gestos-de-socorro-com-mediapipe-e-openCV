#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define ledWhite 13
#define ledYellow 12
#define ledRed 11
#define buz 6

LiquidCrystal_I2C lcd(0x27, 20, 4);

int buzState = 0;  
unsigned long previousMillis = 0;
const long interval = 500;
bool buzOn = false;

void setup() {
  Serial.begin(9600);
  pinMode(ledWhite, OUTPUT);
  pinMode(ledYellow, OUTPUT);
  pinMode(ledRed, OUTPUT);
  pinMode(buz, OUTPUT);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(7, 0);
  lcd.print("Sucesso");
  lcd.setCursor(1, 1);
  lcd.print("Central de Alertas");
  lcd.setCursor(5, 2);
  lcd.print("Carregando...");
  lcd.setCursor(7, 3);
  lcd.print("Aguarde");
}

void loop() {
    
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == '0') {
      buzState = 0;
      digitalWrite(ledRed, LOW);
      digitalWrite(ledYellow, LOW);
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("********************");
      lcd.setCursor(3, 1);
      lcd.print("Nenhum Chamado");
      lcd.setCursor(4, 2);
      lcd.print("Pacientes Bem");
      lcd.setCursor(0, 3);
      lcd.print("********************");
    } else if (command == '1') {
      buzState = 1;
      digitalWrite(ledWhite, LOW);
      digitalWrite(ledYellow, LOW);
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("********************");
      lcd.setCursor(1, 2);
      lcd.print("Paciente com Dores");
      lcd.setCursor(7, 1);
      lcd.print("ALERTA");
      lcd.setCursor(0, 3);
      lcd.print("********************");
    } else if (command == '2') {
      noTone(buz);
      buzState = 2;
      digitalWrite(ledRed, LOW);
      digitalWrite(ledWhite, LOW);
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("********************");
      lcd.setCursor(1, 1);
      lcd.print("Paciente necessita");
      lcd.setCursor(5, 2);
      lcd.print("de Ajuda!!");
      lcd.setCursor(0, 3);
      lcd.print("********************");
    }
  }

  if (buzState == 1) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      buzOn = !buzOn;

      if (buzOn) {
        tone(buz, 1500);
        digitalWrite(ledRed, HIGH);
      } else {
        noTone(buz);
        digitalWrite(ledRed, LOW);
      }
    }
  } else if (buzState == 0) {
    noTone(buz);
    digitalWrite(ledWhite, HIGH);
  } else if (buzState == 2) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      alertaModerado();
      delay(1000);
    }
  }
}


void alertaModerado() {
  for (int i = 0; i < 5; i++) {
    tone(buz, 1500);  // frequência um pouco mais aguda
    digitalWrite(ledYellow, HIGH);
    delay(150);
    digitalWrite(ledYellow, LOW);
    noTone(buz);
    delay(150);
  }
}
