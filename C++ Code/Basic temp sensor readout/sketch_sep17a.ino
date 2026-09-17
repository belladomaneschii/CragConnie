#include "DHT.h"

#define DHTPIN 4     // Digital pin connected to the AM2302 data pin
#define DHTTYPE DHT22   // AM2302 is functionally a DHT22 sensor

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  Serial.println(F("AM2302/DHT22 test!"));
  dht.begin();
}

void loop() {
  // Wait a few seconds between measurements (AM2302 needs ~2 seconds)
  delay(2000);

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature(); // Read temperature as Celsius

  // Check if any reads failed and exit early (to try again).
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println(F("Failed to read from AM2302 sensor!"));
    return;
  }

  Serial.print(F("Humidity: "));
  Serial.print(humidity);
  Serial.print(F("%  Temperature: "));
  Serial.print(temperature);
  Serial.println(F("°C"));
}
