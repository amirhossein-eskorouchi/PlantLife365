// Pin where the pulse output from the HV board is connected
const int GEIGER_PIN = 23;   // GPIO 23 (input only)

// Shared between ISR and main code; must be volatile
volatile unsigned long pulseCount = 0;

// Timing
unsigned long lastMeasureMillis = 0;
const unsigned long measureInterval = 5000;   // 1 second

// Conversion factor (rough for SBM‑20, adjust after calibration):
// µSv/h = CPS * 0.57
const float CPS_TO_USVH = 0.57f;

void IRAM_ATTR handleGeigerPulse() {
  pulseCount++;
}

void setup() {
  Serial.begin(115200);
  delay(5000);

  pinMode(GEIGER_PIN, INPUT);      // or INPUT_PULLDOWN if your circuit allows
  attachInterrupt(digitalPinToInterrupt(GEIGER_PIN),
                  handleGeigerPulse,
                  RISING);         // or FALLING depending on pulse polarity


  lastMeasureMillis = millis();
  Serial.println("SBM‑20 Geiger counter started");
}

void loop() {
  unsigned long now = millis();

  if (now - lastMeasureMillis >= measureInterval) {
    // Copy and reset count atomically
    noInterrupts();
    unsigned long counts = pulseCount;
    pulseCount = 0;
    interrupts();

    // Counts per second
    float cps = counts * 1000.0f / (now - lastMeasureMillis);

    // Counts per minute
    float cpm = cps * 60.0f;

    // Approximate dose rate in µSv/h
    float uSv_h = cps * CPS_TO_USVH;

    Serial.print("CPS: ");
    Serial.print(cps, 2);
    Serial.print("  CPM: ");
    Serial.print(cpm, 1);
    Serial.print("  Dose: ");
    Serial.print(uSv_h, 3);
    Serial.println(" uSv/h");

    lastMeasureMillis = now;
  }
}
