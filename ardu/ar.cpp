#include <Servo.h>

// 서보 모터 설정
Servo servo1;  // 1번 약통
Servo servo2;  // 2번 약통
Servo servo3;  // 3번 약통

// 핀 설정
#define PUMP 4        // 워터펌프 핀 번호
const int TRIG = 7;   // 초음파 TRIG 핀
const int ECHO = 8;   // 초음파 ECHO 핀

// 약통 상태 정의
enum State { IDLE, OPEN, CLOSE };

// 약통별 변수
int dosages[3] = {0, 0, 0};          // 남은 투약 횟수
State states[3] = {IDLE, IDLE, IDLE};  // 현재 상태
int cycles[3] = {0, 0, 0};           // 완료된 사이클 수
unsigned long lastTime[3] = {0, 0, 0};  // 마지막 동작 시간
const int INTERVAL = 500;           // 서보 상태 전이 주기 (0.5초)

// 초음파 센서 변수
const int DETECTION_DISTANCE = 50;  // 감지 거리 (cm)
const int TIMEOUT = 10000;          // 화면 꺼짐 대기 시간 (10초)
const int ULTRA_INTERVAL = 500;     // 초음파 측정 주기 (0.5초)
unsigned long lastDetectionTime = 0;  // 마지막으로 사람이 감지된 시간
unsigned long lastUltraTime = 0;    // 마지막 초음파 측정 시간
bool screenOn = false;              // 화면 상태

// 워터펌프 변수
const int PUMP_INTERVAL = 10000;    // 펌프 작동 시간 (10초)
bool water_pump_flag = false;       // 펌프 상태 플래그
unsigned long pump_last_time = 0;   // 펌프가 켜진 마지막 시간

Servo &getServo(int index) {
  switch (index) {
    case 0: return servo1;
    case 1: return servo2;
    case 2: return servo3;
    default: return servo1;  // 안전용 기본값
  }
}

void setup() {
  Serial.begin(9600);
  
  // 서보 모터 초기화
  servo1.attach(9);   // 서보 1번 핀
  servo2.attach(10);  // 서보 2번 핀
  servo3.attach(11);  // 서보 3번 핀
  servo1.write(0);
  servo2.write(0);
  servo3.write(0);

  // 초음파 센서 초기화
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  // 워터펌프 초기화
  pinMode(PUMP, OUTPUT);
  digitalWrite(PUMP, LOW);  // 펌프 초기 상태: 꺼짐
}

void loop() {
  unsigned long currentTime = millis();

  // 시리얼 데이터 수신 (약통 제어)
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    data.trim();  // 공백 제거
    Serial.print("Received: ");
    Serial.println(data);

    // 약통 초기화
    for (int i = 0; i < 3; i++) {
      dosages[i] = 0;
      states[i] = IDLE;
      cycles[i] = 0;
      lastTime[i] = 0;
      getServo(i).write(0);
    }

    // 데이터 파싱 (예: "1:2,2:1,3:3")
    int start = 0;
    bool validCommand = false;  // 유효한 약통 명령인지 체크
    while (start < data.length()) {
      int colonIdx = data.indexOf(':', start);
      if (colonIdx == -1) break;
      int commaIdx = data.indexOf(',', colonIdx);
      if (commaIdx == -1) commaIdx = data.length();

      int pill_id = data.substring(start, colonIdx).toInt();
      int dosage = data.substring(colonIdx + 1, commaIdx).toInt();

      if (pill_id >= 1 && pill_id <= 3) {
        dosages[pill_id - 1] = dosage;
        states[pill_id - 1] = OPEN;
        getServo(pill_id - 1).write(90);  // 약통 열기
        lastTime[pill_id - 1] = currentTime;
        validCommand = true;  // 유효한 명령으로 플래그 설정
      }
      start = commaIdx + 1;
    }

    // 유효한 약통 명령이 들어오면 워터펌프도 작동
    if (validCommand) {
      digitalWrite(PUMP, HIGH);  // 펌프 켜기
      water_pump_flag = true;
      pump_last_time = currentTime;  // 펌프 시작 시간 기록
      Serial.println("Water Pump ON");
    }
  }

  // 서보 모터 주기 제어
  for (int i = 0; i < 3; i++) {
    if (states[i] != IDLE && currentTime - lastTime[i] >= INTERVAL) {
      updateServo(i);
    }
  }

  // 초음파 센서 주기 제어
  if (currentTime - lastUltraTime >= ULTRA_INTERVAL) {
    measureDistance(currentTime);
    lastUltraTime = currentTime;
  }

  // 워터펌프 주기 제어
  if (water_pump_flag && currentTime - pump_last_time >= PUMP_INTERVAL) {
    digitalWrite(PUMP, LOW);  // 펌프 끄기
    water_pump_flag = false;
    Serial.println("Water Pump OFF after 10 seconds");
  }
}

void measureDistance(unsigned long currentTime) {
  long duration, distance;
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  duration = pulseIn(ECHO, HIGH);
  distance = duration * 17 / 1000;  // cm로 환산

  if (distance < DETECTION_DISTANCE && distance > 0) {
    if (!screenOn) {
      Serial.println("SCREEN_ON");
      screenOn = true;
    }
    lastDetectionTime = currentTime;
  } else if (screenOn && currentTime - lastDetectionTime >= TIMEOUT) {
    Serial.println("SCREEN_OFF");
    screenOn = false;
  }
}

void updateServo(int index) {
  Servo &servo = getServo(index);
  if (states[index] == OPEN) {
    servo.write(0);  // 닫기
    states[index] = CLOSE;
  } else if (states[index] == CLOSE) {
    cycles[index]++;
    if (cycles[index] < dosages[index]) {
      servo.write(90);  // 다시 열기
      states[index] = OPEN;
    } else {
      states[index] = IDLE;  // 동작 완료
    }
  }
  lastTime[index] = millis();
}

