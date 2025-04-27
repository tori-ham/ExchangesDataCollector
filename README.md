# 📈 거래소 데이터 수집기
<!-- # ✅ 과제 1: 거래소 호가 데이터 수집기 -->

## 개요

Python으로 작성된 거래소 실시간 데이터 수집 프로그램입니다.
현재 호가(Orderbook)데이터만 수집 가능합니다.

현재 데이터 수집 대상 가능 거래소는 A-Z 순으로 아래와 같습니다.
  - Bithumb
  - CoinOne
  - GOPAX
  - KorBit
  - Upbit
추후, 설계 확장 후, 국내외 다른 거래소도 대응할 예정입니다.

기본적으로 WebSocket을 이용하여 호가 데이터를 수집했으며, WebSocket API를 지원하지 않는 **Bithumb만 Rest API Polling**으로 수집하고 있습니다.
- Bithumb에서 WebSocket API를 지원하는건 아니지만, Deprecated된 1.2.0 버젼과 Beta서비스중인 2.1.5버젼에서만 WebSocket이 지원되고있고, 현재 정식 지원되는 API 2.1.0 버젼에서는 WebSocket이 아닌 Rest API만 제공하고 있습니다.


거래소마다 WebSocket 메시지 구조나 API 형식이 다르기 때문에, 이를 각각 대응하는 **컨트롤러 구조로 설계**하였습니다.
기본 데이터베이스로 sqlite를 사용하였고, sqlite에서 지정된 거래소의 데이터를 JSON형식으로 추출하는 DataConverter를 갖추고 있습니다.

---

## 시스템 구성

#### 공통 구성
- 각 거래소 컨트롤러를 구동할 때마다, 별도의 `thread`에서 실행하여 **컨트롤러가 독립적으로 동작**을 보장 
- 로깅 시스템을 도입하여, 거래소 및 거래쌍 별 거래 로그 적재하고, **이벤트가 발생할때마다 로그를 수집**하여 컨트롤러의 동작 여부를 쉽게 알 수 있음 
  - 각각의 thread에서 실행되는 컨트롤러의 로그를 적재하기 위해 `RotatingFileHandler` 기반의 thread-safe 로그 수집 
- 로그를 수집하는 이벤트
  - WebSocket Connect(onConnect)
  - WebSocket Error(onError), 
  - API Error(Exception in handleMessage)
  - WebSocket Connection Close(onClose)
  - Rest API Polling -> Thread Start 
  - Rest API Polling -> API Error
  - Rest API Polling -> Unhandled Exception in handleMessage
  - Rest API Polling -> Thread Stop
- 로그 예시
  ``` [2024-04-14 20:32:01] [INFO] [GOPAX-BTC] 데이터 수집 시작 [2024-04-14 20:34:12] [ERROR] [GOPAX-BTC] WebSocket 에러: Connection reset by peer ``` 

#### CoinOne, KorBit, UpBit 거래소 수집기 구조
- 컨트롤러 추상 클래스 (WSController) 설계
  - WebSocket 연결, 메시지 수신, WebSocket 연결 종로, 데이터 저장, 에러 처리 공통화
- WSController를 상속받은 각각의 거래소 하위 클래스가 `getWSUrl()`, `getMessage()`, `handleMessage()`만 각각 구현하여 WebSocket Endpoint, WebSocket Message, 메시지 처리기 분기

#### Gopax 거래소 수집기
- API_KEY와 SECRET으로 Signature를 생성하여 WebSocket통신 시 함께 전달하여, 사용자 인증 후 데이터 수신
- 첫 사용자 인증 후, 일정시간 이후 사용자 인증 ping 수신 시, 대응 pong 전송하여 WebSocket Connection 유지

#### Bithumb 거래소 수집기
- 다른 거래소와 달리 Rest API Polling 방식으로, 통신 연결 상태를 유지하지 않음
- **0.1초 간격으로 API Request**를 전송하여 데이터를 수신
- **데이터 수신하며 에러 발생 시, 로그 기록 후, 다음 데이터 요청 / 수신 대기**

#### 데이터베이스 (SQLite)
- 테이블: `orderbook`
- 필드: 
  - `exchange` : 데이터를 적재한 거래소 명 Upper Case ( ex. KORBIT )
  - `symbol`  : 데이터를 적재하는 가상자산의 Symbol Upper Case ( ex. BTC )
  - `currency` : 데이터를 적재하는 거래 대상 통화 코드 ( ex. KRW )
  - `timestamp` : 데이터 적재 시점의 timestamp
  - `side` : 데이터 적재 타입 ( ask : 매도, bid : 매수 )
  - `price` : 가격 
  - `volume` : 수량 

---
## 실행 방법
#### 1. 환경 설정 
```
git clone https://github.com/tori-ham/DomesticExchangeDataCollector.git
cd DomesticExchangeDataCollector
python -m venv ex_venv
source ex_venv/bin/activate
pip install requirements.txt
```
환경 설정 시, `ex_venv`는 다른 이름으로 설정하셔도 무관합니다.
#### 2. `.env` 파일 설정
```
DB_PATH=
LOG_PATH=
GOPAX_API_KEY=
GOPAX_SECRET_KEY=
```
#### 3. 실행 예시 
BTC-KRW 호가 데이터 수집 시
```
python run_controller.py
```
다른 가상자산 호가 데이터 수집 시
- 
```
vi run_controller.py

~
44 symbol = "원하는 가상자산 symbol"
45 currency = "원하는 거래 통화 코드"
~ 
```
```
python run_controller.py
```

---
## 향후 추가 예정 사항
- 대응 거래소 목록 DB 관리 후, WSController를 상속받는 개별 거래소 통합 가능하도록 설계 확장
  - 현재 통합 컨트롤러 개발 완료
- 날짜 변경 시, 로그 파일 변경
- 로그 DB 적재 시스템 도입