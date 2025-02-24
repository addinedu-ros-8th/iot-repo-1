"""
import sys
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import socket
import struct
import time
import serial
import mysql.connector

class Camera(QThread):
    update = pyqtSignal()

    def __init__(self, sec=0, parent=None):
        super().__init__()
        self.main = parent
        self.running = True

    def run(self):
        while self.running:
            self.update.emit()
            time.sleep(0.05)

    def stop(self):
        self.running = False

class WindowClass(QMainWindow):
    def __init__(self):
        super().__init__()

        self.isCameraOn = False
        self.pixmap = QPixmap()
        self.captured_images = []
        self.count = 0
        self.total_count = 1
        self.camera = None

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.addWidget(self.stacked_widget)

        self.page0 = QWidget()
        self.page0_layout = QVBoxLayout(self.page0)
        self.pill_receive_btn = QPushButton("약받기")
        self.new_reg_btn = QPushButton("신규등록")
        self.pill_info_btn = QPushButton("약 정보 확인")
        self.page0_layout.addWidget(self.pill_receive_btn)
        self.page0_layout.addWidget(self.new_reg_btn)
        self.page0_layout.addWidget(self.pill_info_btn)
        self.page0_layout.addStretch()

        self.page1 = QWidget()
        self.page1_layout = QVBoxLayout(self.page1)
        self.receive1_name = QLineEdit("이름", self.page1)
        self.receive1_name.mousePressEvent = lambda event: self.clear_on_click(self.receive1_name, event)
        self.receive2_user_sex = QComboBox(self.page1)
        self.receive2_user_sex.addItems(['성별을 선택하세요', 'F', 'M'])
        self.receive3_phone = QLineEdit("전화번호", self.page1)
        self.receive3_phone.mousePressEvent = lambda event: self.clear_on_click(self.receive3_phone, event)
        self.receive4_address = QLineEdit("주소", self.page1)
        self.receive4_address.mousePressEvent = lambda event: self.clear_on_click(self.receive4_address, event)
        self.cap_btn = QPushButton("사진촬영", self.page1)
        self.recap_btn = QPushButton("다시 촬영", self.page1)
        self.recap_btn.setEnabled(False)
        self.reg_ok_btn = QPushButton("등록", self.page1)
        self.back_btn_page1 = QPushButton("뒤로가기", self.page1)
        self.label_capfinish = QLabel("촬영 완료 됐습니다 !", self.page1)
        self.label_capfinish.setVisible(False)
        self.label_count = QLabel("0/1", self.page1)
        self.user_check_pixmap = QLabel(self.page1)
        self.page1_layout.addWidget(self.user_check_pixmap)
        self.page1_layout.addWidget(self.receive1_name)
        self.page1_layout.addWidget(self.receive2_user_sex)
        self.page1_layout.addWidget(self.receive3_phone)
        self.page1_layout.addWidget(self.receive4_address)
        self.page1_layout.addWidget(self.cap_btn)
        self.page1_layout.addWidget(self.recap_btn)
        self.page1_layout.addWidget(self.label_count)
        self.page1_layout.addWidget(self.label_capfinish)
        self.page1_layout.addWidget(self.reg_ok_btn)
        self.page1_layout.addWidget(self.back_btn_page1)

        self.page2 = QWidget()
        self.page2_layout = QVBoxLayout(self.page2)
        self.user_check_pixmap2 = QLabel(self.page2)
        self.capture_btn = QPushButton("사진촬영", self.page2)
        self.back_btn_page2 = QPushButton("뒤로가기", self.page2)
        self.label_result = QLabel("결과: ", self.page2)
        self.page2_layout.addWidget(self.user_check_pixmap2)
        self.page2_layout.addWidget(self.capture_btn)
        self.page2_layout.addWidget(self.label_result)
        self.page2_layout.addWidget(self.back_btn_page2)

        self.stacked_widget.addWidget(self.page0)
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.setCurrentIndex(0)

        self.pill_receive_btn.clicked.connect(self.Pill_receive)
        self.new_reg_btn.clicked.connect(self.New_reg)
        self.reg_ok_btn.clicked.connect(self.Reg_ok)
        self.back_btn_page1.clicked.connect(self.back_to_main)
        self.pill_info_btn.clicked.connect(self.Pill_info)
        self.back_btn_page2.clicked.connect(self.back_to_main)
        self.cap_btn.clicked.connect(self.cap)
        self.recap_btn.clicked.connect(self.recap)

        self.SERVER_IP = "127.0.0.1"
        self.SERVER_PORT = 11113
        self.client_socket = None
        self.connect_to_server()

        # 시리얼 포트 설정
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            time.sleep(2)
            print("아두이노 시리얼 연결 성공")
        except serial.SerialException as e:
            print(f"시리얼 포트 연결 실패: {e}")

        # 로컬 MySQL 설정
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '7625',
            'database': 'abcl'
        }

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.SERVER_IP, self.SERVER_PORT))
            print(f"서버({self.SERVER_IP}:{self.SERVER_PORT})에 연결되었습니다.")
        except socket.error as e:
            print(f"서버 연결 실패: {e}")

    def cameraStart(self):
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            print("Error: Camera not found or not accessible!")
            return
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.video.set(cv2.CAP_PROP_FPS, 30)
        self.camera = Camera(self)
        self.camera.daemon = True
        self.camera.start()
        self.camera.update.connect(self.updateCamera)
        self.isCameraOn = True

    def cameraStop(self):
        if self.camera:
            self.camera.running = False
            self.camera.quit()
            self.camera.wait()
        self.count = 0
        self.video.release()
        self.isCameraOn = False

    def updateCamera(self):
        retval, image = self.video.read()
        if retval:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, c = image_rgb.shape
            qimage = QImage(image_rgb.data, w, h, w * c, QImage.Format_RGB888)
            self.pixmap = QPixmap.fromImage(qimage)
            self.pixmap = self.pixmap.scaled(320, 240, Qt.KeepAspectRatio)
            current_page = self.stacked_widget.currentIndex()
            if current_page == 1:
                self.user_check_pixmap.setPixmap(self.pixmap)
            elif current_page == 2:
                self.user_check_pixmap2.setPixmap(self.pixmap)

    def send_frame(self, frame, mode="RC"):
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
            if result:
                data_bytes = encoded_img.tobytes()
                data_size = len(data_bytes)
                mode_bytes = mode.encode()
                self.client_socket.sendall(mode_bytes)
                self.client_socket.sendall(struct.pack(">I", data_size))
                self.client_socket.sendall(data_bytes)
                result_size = struct.unpack(">I", self.client_socket.recv(4))[0]
                result = self.client_socket.recv(result_size).decode()
                return result
            return "Encoding Error"
        except socket.error as e:
            print(f"Socket error: {e}")
            return "Connection Error"

    def get_pill_schedule(self, user_name):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("SELECT user_id FROM users WHERE user_name = %s", (user_name,))
            user_id = cursor.fetchone()
            if not user_id:
                print(f"사용자 '{user_name}'의 user_id 없음")
                return ""
            user_id = user_id[0]
            print(f"사용자 '{user_name}'의 user_id: {user_id}")

            # 요일, 시간 조건 제거, 사용자 ID로만 조회
            cursor.execute(
                "SELECT s.pill_id, p.barrel_id, s.dosage FROM schedule s "
                "JOIN pills p ON s.pill_id = p.pill_id "
                "WHERE s.user_id = %s",
                (user_id,)
            )
            rows = cursor.fetchall()
            print(f"쿼리 결과: {rows}")

            if not rows:
                print(f"사용자 '{user_name}'의 스케줄 없음")
                return ""

            schedule_str = ",".join([f"{row[1]}:{row[2]}" for row in rows if row[0] is not None])
            print(f"스케줄 문자열: {schedule_str}")
            return schedule_str  # 예: "1:2,2:1,3:3"
        except mysql.connector.Error as e:
            print(f"DB 오류: {e}")
            return ""
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def send_to_arduino(self, pill_schedule):
        if pill_schedule:
            print(f"아두이노로 전송: {pill_schedule}")
            try:
                self.serial_port.write(f"{pill_schedule}\n".encode())
            except serial.SerialException as e:
                print(f"아두이노 전송 실패: {e}")

    def capture_photo(self):
        ret, frame = self.video.read()
        if ret:
            result = self.send_frame(frame, "RC")
            if "Error" not in result:
                name, distance = result.split(",")
                output = f"인식 결과: {name} (거리: {distance})" if name != "Unknown" else "없는 사람"
                print(output)
                self.label_result.setText(output)

                if name != "Unknown":
                    pill_schedule = self.get_pill_schedule(name)
                    if pill_schedule:
                        self.send_to_arduino(pill_schedule)
                    else:
                        self.label_result.setText(f"{name}에 대한 약 스케줄 없음")
            else:
                output = f"인식 실패: {result}"
                print(output)
                self.label_result.setText(output)

    def cap(self):
        if self.count < self.total_count:
            self.label_count.setVisible(True)
            self.count += 1
            self.label_count.setText(f'{self.count}/{self.total_count}')
            ret, frame = self.video.read()
            if ret:
                self.captured_images.append(frame)
                print(f"{self.count}번째 이미지 캡처")
                self.cap_btn.setEnabled(False)
                self.recap_btn.setEnabled(True)
            if self.count == self.total_count:
                self.label_capfinish.setVisible(True)
                self.label_count.setVisible(False)

    def recap(self):
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)

    def send_registration_data(self, reg_list):
        try:
            mode = "RG".encode()
            self.client_socket.sendall(mode)
            for i, frame in enumerate(self.captured_images, 1):
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                if result:
                    data_bytes = encoded_img.tobytes()
                    data_size = len(data_bytes)
                    self.client_socket.sendall(struct.pack(">I", data_size))
                    self.client_socket.sendall(data_bytes)
                    print(f"{i}번째 이미지를 전송했습니다.")
            user_info_str = ",".join(reg_list)
            info_size = len(user_info_str.encode())
            self.client_socket.sendall(struct.pack(">I", info_size))
            self.client_socket.sendall(user_info_str.encode())
            print("사용자 정보를 전송했습니다.")
        except socket.error as e:
            print(f"Registration failed: {e}")

    def Pill_receive(self):
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(2)
        try:
            self.capture_btn.clicked.disconnect()
        except TypeError:
            pass
        self.capture_btn.clicked.connect(self.capture_photo)
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def New_reg(self):
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(1)
        self.label_result.setText("결과: ")

    def clear_on_click(self, line_edit, event):
        if line_edit.text() in ["이름", "전화번호", "주소"]:
            line_edit.setText("")
        QLineEdit.mousePressEvent(line_edit, event)

    def Reg_ok(self):
        reg_list = [
            self.receive2_user_sex.currentText(),
            self.receive3_phone.text(),
            self.receive1_name.text(),
            self.receive4_address.text()
        ]
        print("사용자 정보:", reg_list)
        self.send_registration_data(reg_list)
        self.captured_images = []
        self.cameraStop()
        self.stacked_widget.setCurrentIndex(0)
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def back_to_main(self):
        self.cameraStop()
        self.stacked_widget.setCurrentIndex(0)
        try:
            self.capture_btn.clicked.disconnect()
        except TypeError:
            pass
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def Pill_info(self):
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(2)
        try:
            self.capture_btn.clicked.disconnect()
        except TypeError:
            pass
        self.capture_btn.clicked.connect(self.capture_pill_info)
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def capture_pill_info(self):
        ret, frame = self.video.read()
        if ret:
            result = self.send_frame(frame, mode="PI")
            if "Error" not in result:
                output = f"약 정보: {result}"
            else:
                output = f"약 정보 조회 실패: {result}"
            print(output)
            self.label_result.setText(output)

    def keyPressEvent(self, event: QKeyEvent):
        focused_widget = self.focusWidget()
        if event.key() == Qt.Key_Tab:
            if isinstance(focused_widget, QTextEdit):
                self.focusNextChild()
            else:
                super().keyPressEvent(event)
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            if isinstance(focused_widget, QComboBox):
                focused_widget.showPopup()
            elif isinstance(focused_widget, QPushButton):
                focused_widget.click()
            else:
                super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    sys.exit(app.exec_())
"""








"""
import sys
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import socket
import struct
import time
import serial
import mysql.connector

class Camera(QThread):
    update = pyqtSignal()

    def __init__(self, sec=0, parent=None):
        super().__init__()
        self.main = parent
        self.running = True

    def run(self):
        while self.running:
            self.update.emit()
            time.sleep(0.05)

    def stop(self):
        self.running = False

class WindowClass(QMainWindow):
    def __init__(self):
        super().__init__()

        # 해상도 설정 (LCD에 맞게 조정)
        self.screen_width = 800  # 800x480 또는 1024로 변경 가능
        self.screen_height = 480  # 480 또는 600
        self.setFixedSize(self.screen_width, self.screen_height)

        self.isCameraOn = False
        self.pixmap = QPixmap()
        self.captured_images = []
        self.count = 0
        self.total_count = 1
        self.camera = None

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.addWidget(self.stacked_widget)

        # 페이지 0 (메인 화면)
        self.page0 = QWidget()
        self.page0_layout = QVBoxLayout(self.page0)
        self.pill_receive_btn = QPushButton("약받기")
        self.new_reg_btn = QPushButton("신규등록")
        self.pill_info_btn = QPushButton("약 정보 확인")
        self.page0_layout.addWidget(self.pill_receive_btn)
        self.page0_layout.addWidget(self.new_reg_btn)
        self.page0_layout.addWidget(self.pill_info_btn)
        self.page0_layout.addStretch()

        # 페이지 1 (신규 등록)
        self.page1 = QWidget()
        self.page1_layout = QVBoxLayout(self.page1)
        self.user_check_pixmap = QLabel(self.page1)
        self.user_check_pixmap.setAlignment(Qt.AlignCenter)
        self.user_check_pixmap.setFixedSize(self.screen_width - 20, self.screen_height // 2)
        self.receive1_name = QLineEdit("이름", self.page1)
        self.receive1_name.mousePressEvent = lambda event: self.clear_on_click(self.receive1_name, event)
        self.receive2_user_sex = QComboBox(self.page1)
        self.receive2_user_sex.addItems(['성별을 선택하세요', 'F', 'M'])
        self.receive3_phone = QLineEdit("전화번호", self.page1)
        self.receive3_phone.mousePressEvent = lambda event: self.clear_on_click(self.receive3_phone, event)
        self.receive4_address = QLineEdit("주소", self.page1)
        self.receive4_address.mousePressEvent = lambda event: self.clear_on_click(self.receive4_address, event)
        self.cap_btn = QPushButton("사진촬영", self.page1)
        self.recap_btn = QPushButton("다시 촬영", self.page1)
        self.recap_btn.setEnabled(False)
        self.reg_ok_btn = QPushButton("등록", self.page1)
        self.back_btn_page1 = QPushButton("뒤로가기", self.page1)
        self.label_capfinish = QLabel("촬영 완료 됐습니다 !", self.page1)
        self.label_capfinish.setVisible(False)
        self.label_count = QLabel("0/1", self.page1)
        self.page1_layout.addWidget(self.user_check_pixmap)
        self.page1_layout.addWidget(self.receive1_name)
        self.page1_layout.addWidget(self.receive2_user_sex)
        self.page1_layout.addWidget(self.receive3_phone)
        self.page1_layout.addWidget(self.receive4_address)
        self.page1_layout.addWidget(self.cap_btn)
        self.page1_layout.addWidget(self.recap_btn)
        self.page1_layout.addWidget(self.label_count)
        self.page1_layout.addWidget(self.label_capfinish)
        self.page1_layout.addWidget(self.reg_ok_btn)
        self.page1_layout.addWidget(self.back_btn_page1)
        self.page1_layout.addStretch()

        # 페이지 2 (약받기/정보 확인)
        self.page2 = QWidget()
        self.page2_layout = QVBoxLayout(self.page2)
        self.user_check_pixmap2 = QLabel(self.page2)
        self.user_check_pixmap2.setAlignment(Qt.AlignCenter)
        self.user_check_pixmap2.setFixedSize(self.screen_width - 20, self.screen_height // 2)
        self.capture_btn = QPushButton("사진촬영", self.page2)
        self.back_btn_page2 = QPushButton("뒤로가기", self.page2)
        self.label_result = QLabel("결과: ", self.page2)
        self.page2_layout.addWidget(self.user_check_pixmap2)
        self.page2_layout.addWidget(self.capture_btn)
        self.page2_layout.addWidget(self.label_result)
        self.page2_layout.addWidget(self.back_btn_page2)
        self.page2_layout.addStretch()

        self.stacked_widget.addWidget(self.page0)
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.setCurrentIndex(0)

        for btn in [self.pill_receive_btn, self.new_reg_btn, self.pill_info_btn,
                    self.cap_btn, self.recap_btn, self.reg_ok_btn, self.back_btn_page1,
                    self.capture_btn, self.back_btn_page2]:
            btn.setMinimumHeight(40)

        self.pill_receive_btn.clicked.connect(self.Pill_receive)
        self.new_reg_btn.clicked.connect(self.New_reg)
        self.reg_ok_btn.clicked.connect(self.Reg_ok)
        self.back_btn_page1.clicked.connect(self.back_to_main)
        self.pill_info_btn.clicked.connect(self.Pill_info)
        self.back_btn_page2.clicked.connect(self.back_to_main)
        self.cap_btn.clicked.connect(self.cap)
        self.recap_btn.clicked.connect(self.recap)

        self.SERVER_IP = "127.0.0.1"
        self.SERVER_PORT = 11113
        self.client_socket = None
        self.connect_to_server()

        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            time.sleep(2)
            print("아두이노 시리얼 연결 성공")
        except serial.SerialException as e:
            print(f"시리얼 포트 연결 실패: {e}")

        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '7625',
            'database': 'abcl'
        }

        self.showFullScreen()

    def updateCamera(self):
        retval, image = self.video.read()
        if retval:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, c = image_rgb.shape
            qimage = QImage(image_rgb.data, w, h, w * c, QImage.Format_RGB888)
            self.pixmap = QPixmap.fromImage(qimage)
            self.pixmap = self.pixmap.scaled(self.user_check_pixmap.size(), Qt.KeepAspectRatio)
            current_page = self.stacked_widget.currentIndex()
            if current_page == 1:
                self.user_check_pixmap.setPixmap(self.pixmap)
            elif current_page == 2:
                self.user_check_pixmap2.setPixmap(self.pixmap)

    def cameraStart(self):
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            print("Error: Camera not found or not accessible!")
            return
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.video.set(cv2.CAP_PROP_FPS, 30)
        self.camera = Camera(self)
        self.camera.daemon = True
        self.camera.start()
        self.camera.update.connect(self.updateCamera)
        self.isCameraOn = True

    def cameraStop(self):
        if self.camera:
            self.camera.running = False
            self.camera.quit()
            self.camera.wait()
        self.count = 0
        self.video.release()
        self.isCameraOn = False

    def log_to_db(self, log_type, dose_status=None, motor_status=None, schedule_id=None):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT MAX(log_id) FROM logs")
            max_id = cursor.fetchone()[0]
            log_id = (max_id + 1) if max_id else 1
            cursor.execute(
                "INSERT INTO logs (log_id, dose_status, motor_status, time, log_type, schedule_id) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (log_id, dose_status, motor_status, timestamp, log_type, schedule_id)
            )
            conn.commit()
            print(f"로그 기록: {log_type}, ID: {log_id}")
        except mysql.connector.Error as e:
            print(f"DB 로그 오류: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.SERVER_IP, self.SERVER_PORT))
            print(f"서버({self.SERVER_IP}:{self.SERVER_PORT})에 연결되었습니다.")
        except socket.error as e:
            print(f"서버 연결 실패: {e}")

    def send_frame(self, frame, mode="RC"):
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
            if result:
                data_bytes = encoded_img.tobytes()
                data_size = len(data_bytes)
                mode_bytes = mode.encode()
                self.client_socket.sendall(mode_bytes)
                self.client_socket.sendall(struct.pack(">I", data_size))
                self.client_socket.sendall(data_bytes)
                result_size = struct.unpack(">I", self.client_socket.recv(4))[0]
                result = self.client_socket.recv(result_size).decode()
                return result
            return "Encoding Error"
        except socket.error as e:
            print(f"Socket error: {e}")
            return "Connection Error"

    def get_pill_schedule(self, user_name):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_name = %s", (user_name,))
            user_id = cursor.fetchone()
            if not user_id:
                print(f"사용자 '{user_name}'의 user_id 없음")
                return ""
            user_id = user_id[0]
            cursor.execute(
                "SELECT s.pill_id, p.barrel_id, s.dosage FROM schedule s "
                "JOIN pills p ON s.pill_id = p.pill_id "
                "WHERE s.user_id = %s",
                (user_id,)
            )
            rows = cursor.fetchall()
            if not rows:
                print(f"사용자 '{user_name}'의 스케줄 없음")
                return ""
            schedule_str = ",".join([f"{row[1]}:{row[2]}" for row in rows if row[0] is not None])
            print(f"스케줄 문자열: {schedule_str}")
            return schedule_str
        except mysql.connector.Error as e:
            print(f"DB 오류: {e}")
            return ""
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def send_to_arduino(self, pill_schedule):
        if pill_schedule:
            print(f"아두이노로 전송: {pill_schedule}")
            try:
                self.serial_port.write(f"{pill_schedule}\n".encode())
                self.log_to_db("MOTOR_SEND", motor_status="success")
            except serial.SerialException as e:
                print(f"아두이노 전송 실패: {e}")
                self.log_to_db("MOTOR_SEND", motor_status="error")

    def capture_photo(self):
        ret, frame = self.video.read()
        if ret:
            result = self.send_frame(frame, "RC")
            if "Error" not in result:
                name, distance = result.split(",")
                output = f"인식 결과: {name} (거리: {distance})" if name != "Unknown" else "없는 사람"
                print(output)
                self.label_result.setText(output)
                self.log_to_db("RECOG")
                if name != "Unknown":
                    pill_schedule = self.get_pill_schedule(name)
                    if pill_schedule:
                        self.send_to_arduino(pill_schedule)
                    else:
                        self.label_result.setText(f"{name}에 대한 약 스케줄 없음")
            else:
                output = f"인식 실패: {result}"
                print(output)
                self.label_result.setText(output)

    def cap(self):
        if self.count < self.total_count:
            self.label_count.setVisible(True)
            self.count += 1
            self.label_count.setText(f'{self.count}/{self.total_count}')
            ret, frame = self.video.read()
            if ret:
                self.captured_images.append(frame)
                print(f"{self.count}번째 이미지 캡처")
                self.cap_btn.setEnabled(False)
                self.recap_btn.setEnabled(True)
            if self.count == self.total_count:
                self.label_capfinish.setVisible(True)
                self.label_count.setVisible(False)

    def recap(self):
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)

    def send_registration_data(self, reg_list):
        try:
            mode = "RG".encode()
            self.client_socket.sendall(mode)
            for i, frame in enumerate(self.captured_images, 1):
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                if result:
                    data_bytes = encoded_img.tobytes()
                    data_size = len(data_bytes)
                    self.client_socket.sendall(struct.pack(">I", data_size))
                    self.client_socket.sendall(data_bytes)
                    print(f"{i}번째 이미지를 전송했습니다.")
            user_info_str = ",".join(reg_list)
            info_size = len(user_info_str.encode())
            self.client_socket.sendall(struct.pack(">I", info_size))
            self.client_socket.sendall(user_info_str.encode())
            print("사용자 정보를 전송했습니다.")
            self.log_to_db("REG")
        except socket.error as e:
            print(f"Registration failed: {e}")

    def Pill_receive(self):
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(2)
        try:
            self.capture_btn.clicked.disconnect()
        except TypeError:
            pass
        self.capture_btn.clicked.connect(self.capture_photo)
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def New_reg(self):
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(1)
        self.label_result.setText("결과: ")

    def clear_on_click(self, line_edit, event):
        if line_edit.text() in ["이름", "전화번호", "주소"]:
            line_edit.setText("")
        QLineEdit.mousePressEvent(line_edit, event)

    def Reg_ok(self):
        reg_list = [
            self.receive2_user_sex.currentText(),
            self.receive3_phone.text(),
            self.receive1_name.text(),
            self.receive4_address.text()
        ]
        print("사용자 정보:", reg_list)
        self.send_registration_data(reg_list)
        self.captured_images = []
        self.cameraStop()
        self.stacked_widget.setCurrentIndex(0)
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def back_to_main(self):
        self.cameraStop()
        self.stacked_widget.setCurrentIndex(0)
        try:
            self.capture_btn.clicked.disconnect()
        except TypeError:
            pass
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def Pill_info(self):
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(2)
        try:
            self.capture_btn.clicked.disconnect()
        except TypeError:
            pass
        self.capture_btn.clicked.connect(self.capture_pill_info)
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def capture_pill_info(self):
        ret, frame = self.video.read()
        if ret:
            result = self.send_frame(frame, mode="PI")
            if "Error" not in result:
                output = f"약 정보: {result}"
                self.log_to_db("PILL_INFO")
            else:
                output = f"약 정보 조회 실패: {result}"
            print(output)
            self.label_result.setText(output)

    def keyPressEvent(self, event: QKeyEvent):
        focused_widget = self.focusWidget()
        if event.key() == Qt.Key_Q:  # 'q' 키를 눌렀을 때 종료
            print("Q 키 눌림: 프로그램 종료")
            QApplication.quit()  # 애플리케이션 완전히 종료
            # 또는 self.close()로 창만 닫기 가능
        elif event.key() == Qt.Key_Tab:
            if isinstance(focused_widget, QTextEdit):
                self.focusNextChild()
            else:
                super().keyPressEvent(event)
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            if isinstance(focused_widget, QComboBox):
                focused_widget.showPopup()
            elif isinstance(focused_widget, QPushButton):
                focused_widget.click()
            else:
                super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    sys.exit(app.exec_())

"""



import sys
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import socket
import struct
import time
import serial
import mysql.connector

class Camera(QThread):
    update = pyqtSignal()

    def __init__(self, sec=0, parent=None):
        super().__init__()
        self.main = parent
        self.running = True

    def run(self):
        while self.running:
            self.update.emit()
            time.sleep(0.05)

    def stop(self):
        self.running = False

class WindowClass(QMainWindow):
    def __init__(self):
        super().__init__()

        # 해상도 설정
        self.screen_width = 800  # 800x480 또는 1024로 변경 가능
        self.screen_height = 480  # 480 또는 600
        self.setFixedSize(self.screen_width, self.screen_height)

        self.isCameraOn = False
        self.pixmap = QPixmap()
        self.captured_images = []
        self.count = 0
        self.total_count = 1
        self.camera = None
        self.user_info = []

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.addWidget(self.stacked_widget)

        # 페이지 0 (메인 화면)
        self.page0 = QWidget()
        self.page0_layout = QVBoxLayout(self.page0)
        self.pill_receive_btn = QPushButton("약받기")
        self.new_reg_btn = QPushButton("신규등록")
        self.pill_info_btn = QPushButton("약 정보 확인")
        self.page0_layout.addWidget(self.pill_receive_btn)
        self.page0_layout.addWidget(self.new_reg_btn)
        self.page0_layout.addWidget(self.pill_info_btn)
        self.page0_layout.addStretch()

        # 페이지 1 (신규 등록 - 인적사항 입력, 버튼 좌우 배치)
        self.page1 = QWidget()
        self.page1_layout = QVBoxLayout(self.page1)
        self.receive1_name = QLineEdit("이름", self.page1)
        self.receive1_name.mousePressEvent = lambda event: self.clear_on_click(self.receive1_name, event)
        self.receive2_user_sex = QComboBox(self.page1)
        self.receive2_user_sex.addItems(['성별을 선택하세요', 'F', 'M'])
        self.receive3_phone = QLineEdit("전화번호", self.page1)
        self.receive3_phone.mousePressEvent = lambda event: self.clear_on_click(self.receive3_phone, event)
        self.receive4_address = QLineEdit("주소", self.page1)
        self.receive4_address.mousePressEvent = lambda event: self.clear_on_click(self.receive4_address, event)

        # 버튼을 좌우로 배치하기 위한 QHBoxLayout
        self.button_layout1 = QHBoxLayout()
        self.back_btn_page1 = QPushButton("뒤로가기", self.page1)
        self.next_to_photo_btn = QPushButton("사진촬영", self.page1)
        self.button_layout1.addWidget(self.back_btn_page1)  # 좌측
        self.button_layout1.addWidget(self.next_to_photo_btn)  # 우측

        self.page1_layout.addWidget(self.receive1_name)
        self.page1_layout.addWidget(self.receive2_user_sex)
        self.page1_layout.addWidget(self.receive3_phone)
        self.page1_layout.addWidget(self.receive4_address)
        self.page1_layout.addLayout(self.button_layout1)
        self.page1_layout.addStretch()

        # 페이지 2 (신규 등록 - 사진 촬영)
        self.page2 = QWidget()
        self.page2_layout = QVBoxLayout(self.page2)
        self.user_check_pixmap = QLabel(self.page2)
        self.user_check_pixmap.setAlignment(Qt.AlignCenter)
        self.user_check_pixmap.setFixedSize(self.screen_width - 20, self.screen_height - 200)
        self.label_count = QLabel("0/1", self.page2)
        self.label_count.setAlignment(Qt.AlignCenter)
        self.label_capfinish = QLabel("촬영 완료 됐습니다 !", self.page2)
        self.label_capfinish.setAlignment(Qt.AlignCenter)
        self.label_capfinish.setVisible(False)

        self.button_grid2 = QGridLayout()
        self.cap_btn = QPushButton("사진촬영", self.page2)
        self.recap_btn = QPushButton("다시촬영", self.page2)
        self.recap_btn.setEnabled(False)
        self.back_btn_page2 = QPushButton("뒤로가기", self.page2)
        self.reg_ok_btn = QPushButton("등록", self.page2)
        self.button_grid2.addWidget(self.cap_btn, 0, 0)
        self.button_grid2.addWidget(self.recap_btn, 0, 1)
        self.button_grid2.addWidget(self.back_btn_page2, 1, 0)
        self.button_grid2.addWidget(self.reg_ok_btn, 1, 1)

        self.page2_layout.addWidget(self.user_check_pixmap)
        self.page2_layout.addWidget(self.label_count)
        self.page2_layout.addWidget(self.label_capfinish)
        self.page2_layout.addLayout(self.button_grid2)

        # 페이지 3 (약받기)
        self.page3 = QWidget()
        self.page3_layout = QVBoxLayout(self.page3)
        self.user_check_pixmap3 = QLabel(self.page3)
        self.user_check_pixmap3.setAlignment(Qt.AlignCenter)
        self.user_check_pixmap3.setFixedSize(self.screen_width - 20, self.screen_height - 150)
        self.label_result = QLabel("결과: ", self.page3)
        self.label_result.setAlignment(Qt.AlignCenter)

        self.button_grid3 = QGridLayout()
        self.back_btn_page3 = QPushButton("뒤로가기", self.page3)
        self.capture_btn = QPushButton("사진촬영", self.page3)
        self.button_grid3.addWidget(self.back_btn_page3, 0, 0)
        self.button_grid3.addWidget(self.capture_btn, 0, 1)

        self.page3_layout.addWidget(self.user_check_pixmap3)
        self.page3_layout.addWidget(self.label_result)
        self.page3_layout.addLayout(self.button_grid3)
        self.page3_layout.addStretch()

        self.stacked_widget.addWidget(self.page0)
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)
        self.stacked_widget.setCurrentIndex(0)

        for btn in [self.pill_receive_btn, self.new_reg_btn, self.pill_info_btn,
                    self.next_to_photo_btn, self.back_btn_page1, self.cap_btn,
                    self.recap_btn, self.back_btn_page2, self.reg_ok_btn,
                    self.capture_btn, self.back_btn_page3]:
            btn.setMinimumHeight(40)

        self.pill_receive_btn.clicked.connect(self.Pill_receive)
        self.new_reg_btn.clicked.connect(self.New_reg)
        self.next_to_photo_btn.clicked.connect(self.go_to_photo_page)
        self.back_btn_page1.clicked.connect(self.back_to_main)
        self.pill_info_btn.clicked.connect(self.Pill_info)
        self.back_btn_page2.clicked.connect(self.back_to_main_from_page2)
        self.back_btn_page3.clicked.connect(self.back_to_main)
        self.cap_btn.clicked.connect(self.cap)
        self.recap_btn.clicked.connect(self.recap)
        self.reg_ok_btn.clicked.connect(self.Reg_ok)

        self.SERVER_IP = "127.0.0.1"
        self.SERVER_PORT = 11113
        self.client_socket = None
        self.connect_to_server()

        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            time.sleep(2)
            print("아두이노 시리얼 연결 성공")
        except serial.SerialException as e:
            print(f"시리얼 포트 연결 실패: {e}")

        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '7625',
            'database': 'abcl'
        }

        self.showFullScreen()

    def updateCamera(self):
        retval, image = self.video.read()
        if retval:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, c = image_rgb.shape
            qimage = QImage(image_rgb.data, w, h, w * c, QImage.Format_RGB888)
            self.pixmap = QPixmap.fromImage(qimage)
            current_page = self.stacked_widget.currentIndex()
            if current_page == 2:
                self.pixmap = self.pixmap.scaled(self.user_check_pixmap.size(), Qt.KeepAspectRatio)
                self.user_check_pixmap.setPixmap(self.pixmap)
            elif current_page == 3:
                self.pixmap = self.pixmap.scaled(self.user_check_pixmap3.size(), Qt.KeepAspectRatio)
                self.user_check_pixmap3.setPixmap(self.pixmap)

    def cameraStart(self):
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            print("Error: Camera not found or not accessible!")
            return
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.video.set(cv2.CAP_PROP_FPS, 30)
        self.camera = Camera(self)
        self.camera.daemon = True
        self.camera.start()
        self.camera.update.connect(self.updateCamera)
        self.isCameraOn = True

    def cameraStop(self):
        if self.camera:
            self.camera.running = False
            self.camera.quit()
            self.camera.wait()
        self.count = 0
        self.video.release()
        self.isCameraOn = False

    def log_to_db(self, log_type, dose_status=None, motor_status=None, schedule_id=None):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT MAX(log_id) FROM logs")
            max_id = cursor.fetchone()[0]
            log_id = (max_id + 1) if max_id else 1
            cursor.execute(
                "INSERT INTO logs (log_id, dose_status, motor_status, time, log_type, schedule_id) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (log_id, dose_status, motor_status, timestamp, log_type, schedule_id)
            )
            conn.commit()
            print(f"로그 기록: {log_type}, ID: {log_id}")
        except mysql.connector.Error as e:
            print(f"DB 로그 오류: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.SERVER_IP, self.SERVER_PORT))
            print(f"서버({self.SERVER_IP}:{self.SERVER_PORT})에 연결되었습니다.")
        except socket.error as e:
            print(f"서버 연결 실패: {e}")

    def send_frame(self, frame, mode="RC"):
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
            if result:
                data_bytes = encoded_img.tobytes()
                data_size = len(data_bytes)
                mode_bytes = mode.encode()
                self.client_socket.sendall(mode_bytes)
                self.client_socket.sendall(struct.pack(">I", data_size))
                self.client_socket.sendall(data_bytes)
                result_size = struct.unpack(">I", self.client_socket.recv(4))[0]
                result = self.client_socket.recv(result_size).decode()
                return result
            return "Encoding Error"
        except socket.error as e:
            print(f"Socket error: {e}")
            return "Connection Error"

    def get_pill_schedule(self, user_name):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_name = %s", (user_name,))
            user_id = cursor.fetchone()
            if not user_id:
                print(f"사용자 '{user_name}'의 user_id 없음")
                return ""
            user_id = user_id[0]
            cursor.execute(
                "SELECT s.pill_id, p.barrel_id, s.dosage FROM schedule s "
                "JOIN pills p ON s.pill_id = p.pill_id "
                "WHERE s.user_id = %s",
                (user_id,)
            )
            rows = cursor.fetchall()
            if not rows:
                print(f"사용자 '{user_name}'의 스케줄 없음")
                return ""
            schedule_str = ",".join([f"{row[1]}:{row[2]}" for row in rows if row[0] is not None])
            print(f"스케줄 문자열: {schedule_str}")
            return schedule_str
        except mysql.connector.Error as e:
            print(f"DB 오류: {e}")
            return ""
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def send_to_arduino(self, pill_schedule):
        if pill_schedule:
            print(f"아두이노로 전송: {pill_schedule}")
            try:
                self.serial_port.write(f"{pill_schedule}\n".encode())
                self.log_to_db("MOTOR_SEND", motor_status="success")
            except serial.SerialException as e:
                print(f"아두이노 전송 실패: {e}")
                self.log_to_db("MOTOR_SEND", motor_status="error")

    def capture_photo(self):
        ret, frame = self.video.read()
        if ret:
            result = self.send_frame(frame, "RC")
            if "Error" not in result:
                name, distance = result.split(",")
                output = f"인식 결과: {name} (거리: {distance})" if name != "Unknown" else "없는 사람"
                print(output)
                self.label_result.setText(output)
                self.log_to_db("RECOG")
                if name != "Unknown":
                    pill_schedule = self.get_pill_schedule(name)
                    if pill_schedule:
                        self.send_to_arduino(pill_schedule)
                    else:
                        self.label_result.setText(f"{name}에 대한 약 스케줄 없음")
            else:
                output = f"인식 실패: {result}"
                print(output)
                self.label_result.setText(output)

    def cap(self):
        if self.count < self.total_count:
            self.label_count.setVisible(True)
            self.count += 1
            self.label_count.setText(f'{self.count}/{self.total_count}')
            ret, frame = self.video.read()
            if ret:
                self.captured_images.append(frame)
                print(f"{self.count}번째 이미지 캡처")
                self.cap_btn.setEnabled(False)
                self.recap_btn.setEnabled(True)
            if self.count == self.total_count:
                self.label_capfinish.setVisible(True)
                self.label_count.setVisible(False)

    def recap(self):
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)

    def send_registration_data(self, reg_list):
        try:
            mode = "RG".encode()
            self.client_socket.sendall(mode)
            for i, frame in enumerate(self.captured_images, 1):
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                if result:
                    data_bytes = encoded_img.tobytes()
                    data_size = len(data_bytes)
                    self.client_socket.sendall(struct.pack(">I", data_size))
                    self.client_socket.sendall(data_bytes)
                    print(f"{i}번째 이미지를 전송했습니다.")
            user_info_str = ",".join(reg_list)
            info_size = len(user_info_str.encode())
            self.client_socket.sendall(struct.pack(">I", info_size))
            self.client_socket.sendall(user_info_str.encode())
            print("사용자 정보를 전송했습니다.")
            self.log_to_db("REG")
        except socket.error as e:
            print(f"Registration failed: {e}")

    def Pill_receive(self):
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(3)
        try:
            self.capture_btn.clicked.disconnect()
        except TypeError:
            pass
        self.capture_btn.clicked.connect(self.capture_photo)
        self.label_result.setText("결과: ")

    def New_reg(self):
        self.stacked_widget.setCurrentIndex(1)
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.user_info = []

    def go_to_photo_page(self):
        self.user_info = [
            self.receive2_user_sex.currentText(),
            self.receive3_phone.text(),
            self.receive1_name.text(),
            self.receive4_address.text()
        ]
        print("저장된 인적사항:", self.user_info)
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(2)
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)

    def Reg_ok(self):
        if self.user_info and self.captured_images:
            self.send_registration_data(self.user_info)
            self.captured_images = []
            self.cameraStop()
            self.stacked_widget.setCurrentIndex(0)
        else:
            print("인적사항 또는 사진이 누락됨")

    def back_to_main(self):
        self.cameraStop()
        self.stacked_widget.setCurrentIndex(0)
        self.receive1_name.setText("이름")
        self.receive2_user_sex.setCurrentIndex(0)
        self.receive3_phone.setText("전화번호")
        self.receive4_address.setText("주소")
        self.captured_images = []
        self.count = 0
        self.label_count.setVisible(True)
        self.label_count.setText(f'{self.count}/{self.total_count}')
        self.label_capfinish.setVisible(False)
        self.cap_btn.setEnabled(True)
        self.recap_btn.setEnabled(False)
        self.label_result.setText("결과: ")

    def back_to_main_from_page2(self):
        self.cameraStop()
        self.back_to_main()

    def Pill_info(self):
        self.cameraStart()
        self.stacked_widget.setCurrentIndex(3)
        try:
            self.capture_btn.clicked.disconnect()
        except TypeError:
            pass
        self.capture_btn.clicked.connect(self.capture_pill_info)
        self.label_result.setText("결과: ")

    def capture_pill_info(self):
        ret, frame = self.video.read()
        if ret:
            result = self.send_frame(frame, mode="PI")
            if "Error" not in result:
                output = f"약 정보: {result}"
                self.log_to_db("PILL_INFO")
            else:
                output = f"약 정보 조회 실패: {result}"
            print(output)
            self.label_result.setText(output)

    def clear_on_click(self, line_edit, event):
        if line_edit.text() in ["이름", "전화번호", "주소"]:
            line_edit.setText("")
        QLineEdit.mousePressEvent(line_edit, event)

    def keyPressEvent(self, event: QKeyEvent):
        focused_widget = self.focusWidget()
        if event.key() == Qt.Key_Q:
            print("Q 키 눌림: 프로그램 종료")
            QApplication.quit()
        elif event.key() == Qt.Key_Tab:
            if isinstance(focused_widget, QTextEdit):
                self.focusNextChild()
            else:
                super().keyPressEvent(event)
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            if isinstance(focused_widget, QComboBox):
                focused_widget.showPopup()
            elif isinstance(focused_widget, QPushButton):
                focused_widget.click()
            else:
                super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    sys.exit(app.exec_())
    