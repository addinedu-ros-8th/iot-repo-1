# Pill Guy - 스마트 알약 디스펜서
 
**A Smart Pill Dispenser with Face Recognition**

**현대인을 위한 스마트 약 관리 솔루션**

"Pill Guy"는 얼굴 인식 기술과 IoT를 활용해 현대인의 약 복용 경험을 개선하고, 병원 및 요양원에서 발생할 수 있는 인적 실수를 줄이는 스마트 알약 디스펜서입니다. 정확한 스케줄 관리와 직관적인 사용자 인터페이스를 통해 약 복용의 편리함과 안전성을 제공합니다.

---

## 🚀 프로젝트 개요

현대인들은 비타민이나 영양제를 자주 섭취하며, 병원이나 요양원에서는 많은 환자들이 정해진 시간에 약을 복용해야 합니다. 하지만 인간의 실수로 인해 약을 빼먹거나 잘못 복용하는 문제가 발생할 수 있습니다.

**Pill Guy**는 이러한 문제를 해결하기 위한 **스마트 알약 디스펜서**입니다. 얼굴 인식을 통해 사용자를 식별하고, 등록된 스케줄에 따라 정확한 시간에 알약과 물을 제공합니다. 또한, 약이 부족하면 LED 표시로 사용자에게 알림을 제공합니다.

---

## 🏗️ 프로젝트 주요 기능

✔ **얼굴 인식 기반 사용자 인증** (FaceNet512 활용)  
✔ **스케줄 기반 알약 분배** (약 복용 시간 ±30분 허용)  
✔ **자동 물 제공 기능** (컵이 감지될 경우 워터펌프 작동)  
✔ **약 부족 알림** (적외선 센서를 이용한 감지 후 LED 점등)  
✔ **사용자 및 약 정보 관리** (신규 등록 및 정보 조회)  
✔ **관리자 기능 제공** (약 및 스케줄 관리, 전체 사용자 조회)

---

## 🛠️ 시스템 아키텍처

```
[얼굴인식 서버] ← TCP → [라즈베리파이 GUI] ← Serial → [아두이노]
                           ↑
                           |
                         TCP
                           ↓
                     [관리자 PC]
```

### 📌 하드웨어 구성

1. **서버 컴퓨터** : 얼굴 인식을 위한 서버 (FaceNet512 모델 사용)
2. **라즈베리파이** : 유저 GUI 및 메인 로직 (터치스크린 및 카메라 포함)
3. **아두이노** : 알약 배분 및 센서 제어 (서보모터, 워터펌프, LED 등)
4. **관리자 PC** : 원격으로 약 및 스케줄을 관리하는 인터페이스 제공

### 📡 IO 구성

| 장치        | 연결 방식  | 설명 |
|------------|----------|----------------|
| **터치스크린** | Raspberry Pi | 사용자 GUI 제공 |
| **카메라** | Raspberry Pi | 얼굴 인식 수행 |
| **워터펌프** | Arduino | 컵 감지 시 물 제공 |
| **적외선 센서** | Arduino | 약 부족 감지 (LED ON) |
| **LED** | Arduino | 약 부족 경고 표시 |
| **초음파 센서** | Arduino | 사용자 접근 감지 (화면 ON/OFF) |
| **조도 센서** | Arduino | 컵 감지 후 물 제공 제어 |
| **서보모터** | Arduino | 알약 배분 (각 약통별로 서보 제어) |

---

## 🏛️ 데이터베이스 구조 (MySQL)

### 📌 테이블 정의

#### **1. 사용자 정보 (`users` 테이블)**
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `user_id` | INT (PK, AUTO_INCREMENT) | 사용자 ID |
| `face_encoding` | TEXT | 얼굴 임베딩 데이터 |
| `phone` | VARCHAR(20) | 전화번호 |
| `user_name` | VARCHAR(100) | 사용자 이름 |
| `sex` | ENUM('M', 'F') | 성별 |
| `address` | VARCHAR(255) | 주소 |

#### **2. 약 정보 (`pills` 테이블)**
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `pill_id` | INT (PK, AUTO_INCREMENT) | 약 ID |
| `user_id` | INT (FK) | 사용자 ID |
| `pill_name` | VARCHAR(100) | 약 이름 |
| `barrel_id` | INT | 약통 번호 |

#### **3. 스케줄 (`schedule` 테이블)**
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `schedule_id` | INT (PK, AUTO_INCREMENT) | 스케줄 ID |
| `user_id` | INT (FK) | 사용자 ID |
| `pill_id` | INT (FK) | 약 ID |
| `time` | TEXT | 복용 시간 |
| `day_of_the_week` | TEXT ('월', '화', '수', '목', '금', '토', '일') | 복용 요일 |
| `dosage` | INT | 복용 횟수 |
| `period` | TEXT | 복용 기간 (일 단위) |

#### **4. 로그 (`logs` 테이블)**
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `log_id` | INT (PK, AUTO_INCREMENT) | 로그 ID |
| `schedule_id` | INT (FK) | 스케줄 ID |
| `dose_status` | VARCHAR(50) | 복용 상태 |
| `motor_status` | VARCHAR(50) | 모터 상태 |
| `time` | DATETIME | 기록 시간 |
| `log_type` | VARCHAR(50) | 로그 유형 |

#### **5. 관리자 정보 (`admin` 테이블)**
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `admin_id` | INT (PK, AUTO_INCREMENT) | 관리자 ID |
| `admin_name` | VARCHAR(100) | 관리자 이름 |
| `sex` | ENUM('M', 'F') | 성별 |
| `phone` | VARCHAR(20) | 전화번호 |
| `address` | VARCHAR(255) | 주소 |

---

## ⚡ 기술 스택

| 분류 | 사용 기술 |
|------|----------|
| **프로그래밍 언어** | Python, C++ |
| **프레임워크 & 라이브러리** | OpenCV, PyQt5, DeepFace (FaceNet512), MySQL Connector |
| **데이터베이스** | MySQL |
| **통신 프로토콜** | TCP, Serial (UART) |
| **버전 관리** | Git |
| **협업 도구** | Jira, Confluence |

---


## 요구 사항
- **하드웨어**: 라즈베리파이, 아두이노, 서버 컴퓨터, 관리자 PC
- **소프트웨어**:
  - Python 3.8+ (`deepface`, `PyQt5`, `mysql-connector-python`)
  - Arduino IDE
  - MySQL

---

## 📜 라이선스

MIT License를 따릅니다. 자유롭게 수정 및 배포 가능합니다.

---


