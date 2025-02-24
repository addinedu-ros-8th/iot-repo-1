import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import mysql.connector
import serial
import struct

# MySQL 연결
local = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1111",
    database="Pill_guy"
)
cur = local.cursor()

from_class = uic.loadUiType("./iot_project/adminedit.ui")[0]

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("관리자 PC")

        self.uid = bytes(4)
        self.conn = \
            serial.Serial(port='/dev/ttyACM0',baudrate=9600, timeout=1)
        self.recv = Receiver(self.conn)
        self.recv.start()

        self.timer = QTimer()
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.getStatus)
        self.timer.start()

        self.pill_list = []
        self.reg_total_info=[]
        cur.execute('select pill_name from pills')
        pill_names = cur.fetchall()
        print(pill_names)
        
        for i in pill_names:
            for t in i:
                self.pill_list.append(t)
        
        self.reg_choose_pill.addItems(self.pill_list)


        self.stackedWidget.setCurrentIndex(5)
        
        self.pixmap = QPixmap()
        self.pixmap.load('./pillguy.png')
        self.pixmap = self.pixmap.scaled(self.home_img.width(),self.home_img.height())
        self.home_img.setPixmap(self.pixmap)
        
        self.upCnt=0
        self.backStatus=False
        #home 관련
        self.reg_to_home.setIcon(QIcon("./homebutton.png"))
        self.conti_to_home.setIcon(QIcon("./homebutton.png"))
        self.manag_to_home.setIcon(QIcon("./homebutton.png"))

        self.reg_pill.clicked.connect(self.Home_to_regpill)
        self.user_conti.clicked.connect(self.Home_to_conti)
        self.user_manag.clicked.connect(self.Home_to_manag)

        self.reg_to_home.clicked.connect(self.Reg_to_home)
        self.conti_to_home.clicked.connect(self.Conti_to_home)
        self.manag_to_home.clicked.connect(self.Manag_to_home)
        self.reg_addpill_btn.clicked.connect(self.Reg_addpill_btn)

        self.add_cancel.clicked.connect(self.Add_cancel)
        self.add_save.clicked.connect(self.Add_save)
        self.reg_week_list = {"월요일":0,"화요일":1,"수요일":2,"목요일":3,"금요일":4,"토요일":5,"일요일":6}
        # self.reg_dosage.clicked.connect(self.dosage_button)
        # self.reg_save.clicked.connect(self.save_button)
        for i in range(24):
            time_str = f"{i:02d}:00"  # 00:00, 01:00, ..., 23:00 형식의 문자열 생성
            self.reg_choose_time.addItem(time_str)  # 리스트가 아닌 단일 항목을 추가

        self.reg_backbtn.clicked.connect(self.Backbtn)
        self.reg_nextbtn.clicked.connect(self.Nextbtn)

        # '셀' 편집 활성화
        self.reg_save.clicked.connect(self.Reg_save)
        self.reg_update.clicked.connect(self.Reg_update)
        self.groupBox_delete.setVisible(False)
        self.groupBox_modify.setVisible(False)

        #manag_delete
        self.manag_delete_btn.clicked.connect(self.delete_btn)
        self.manag_delete_Y.clicked.connect(self.delete_Y)
        self.manag_delete_N.clicked.connect(self.delete_N)
        #manag_modify
        self.manag_modi.clicked.connect(self.Manag_modi)
        self.modi_back_btn.clicked.connect(self.Modi_back_btn)
        self.modi_complete_btn.clicked.connect(self.Modi_complete_btn)

        #self.reg_choose_pill.currentIndexChanged.connect(self.find_pill_id)
        self.reg_select_user.currentIndexChanged.connect(self.reg_find_id)
        self.conti_select_user.currentIndexChanged.connect(self.conti_find_id)
        self.manag_select_user.currentIndexChanged.connect(self.manag_find_id)
        self.reg_choose_pill.currentIndexChanged.connect(self.find_pill_id)

        #admin 페이지 연결 함수 등록 취소
        self.move_reg_card.clicked.connect(self.move_reg)
        self.move_del_card.clicked.connect(self.move_del)
        self.reg_admin_save.clicked.connect(self.admin_save)
        self.reg_admin_cancel.clicked.connect(self.admin_cancel)

        #시그널 연결 함수
        self.recv.detected.connect(self.detected)
        self.next_list =[]

    

        
    def keyPressEvent(self, event: QKeyEvent):
        focused_widget = self.focusWidget()

        # Tab 키: QTextEdit이면 기본 동작 차단하고 다음 위젯으로 포커스 이동
        if event.key() == Qt.Key_Tab:
            if isinstance(focused_widget, QTextEdit):
                self.focusNextChild()  # 다음 위젯으로 이동
            else:
                super().keyPressEvent(event)  # 기본 동작 수행
        # Enter 키: ComboBox면 드롭다운 열기, 버튼이면 클릭 실행
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            if isinstance(focused_widget, QComboBox):
                focused_widget.showPopup()  # 콤보박스 드롭다운 열기
            elif isinstance(focused_widget, QPushButton):
                focused_widget.click()
            else:
                super().keyPressEvent(event)
                
    def Reg_addpill_btn(self):
        self.stackedWidget.setCurrentIndex(4)
    def Add_save(self):
        say_pill = self.say.toPlainText()
        if str(say_pill) in self.pill_list:
            QMessageBox.warning(self, 'Warning', 'Already registered !')
        else:
            cur.execute('insert into pills(pill_name) values (%s)',(say_pill,))
            local.commit()
            self.reg_choose_pill.addItem(str(say_pill))
            self.stackedWidget.setCurrentIndex(1)

    def Add_cancel(self):
        self.stackedWidget.setCurrentIndex(1)

    def Home_to_regpill(self):
        self.stackedWidget.setCurrentIndex(1)
    
    def Reg_to_home(self):
        self.stackedWidget.setCurrentIndex(0)

    def Home_to_conti(self):
        self.stackedWidget.setCurrentIndex(2)
    
    def Conti_to_home(self):
        self.stackedWidget.setCurrentIndex(0)

    def Home_to_manag(self):
        self.stackedWidget.setCurrentIndex(3)
    
    def Manag_to_home(self):
        self.stackedWidget.setCurrentIndex(0)

    def manag_find_id(self):
        mn_each_name = self.manag_select_user.currentText()
        cur.execute("SELECT user_id FROM users WHERE user_name = %s",(mn_each_name,))
        rows = cur.fetchall()
        for x in rows:
            for y in x:
               self.manag_name_category =y
               
    def reg_find_id(self):
        each_name = self.reg_select_user.currentText()
        cur.execute("select user_id from users where user_name = %s", (each_name,))
        rows = cur.fetchall()
        for x in rows:
            for y in x:
               self.name_category =y
               #print(name_category)
    def Nextbtn(self):
        if self.backStatus == True:
            self.cnt += 1
            try:
                self.reg_choose_time.setCurrentText(self.reg_total_info[self.cnt][0])
                self.reg_day_of_the_week.setCurrentText(self.reg_total_info[self.cnt][1])
                self.count_pill.setText(self.reg_total_info[self.cnt][2])
                self.reg_backbtn.setDisabled(False)
            except:
                self.backStatus = False
                self.reg_choose_time.setCurrentText('복용시간 선택')
                self.reg_day_of_the_week.setCurrentText('요일선택')
                self.count_pill.setText('')
        else:
            self.reg_info=[]

            self.reg_info.append(self.reg_choose_time.currentText())
            self.reg_info.append(self.reg_day_of_the_week.currentText())
            self.reg_info.append(self.count_pill.text())

            self.reg_total_info.append(self.reg_info)
            self.cnt = len(self.reg_total_info)
            #print(self.reg_info)
            #안버림
            #cur.execute('insert into schedule(user_id,pill_id, time, day_of_the_week, dosage) values(%s,%s,%s,%s,%s)', (self.name_category,pill_id,self.reg_info[0],self.reg_info[1],self.reg_info[2]))
            #local.commit()

            
            self.reg_choose_time.setCurrentText('복용시간 선택')
            self.reg_day_of_the_week.setCurrentText('요일선택')
            self.count_pill.setText('')

    def Backbtn(self):
        try:
            self.backStatus=True
            self.cnt -= 1

            if self.cnt == 0:
                self.reg_backbtn.setDisabled(True)

            self.reg_choose_time.setCurrentText(self.reg_total_info[self.cnt][0])
            self.reg_day_of_the_week.setCurrentText(self.reg_total_info[self.cnt][1])
            self.count_pill.setText(self.reg_total_info[self.cnt][2])
        except:
            QMessageBox.warning(self, "경고", "뒤로갈 데이터가 없습니다.")

    def find_pill_id(self):
        pill_name = self.reg_choose_pill.currentText()
        cur.execute('select pill_id from pills where pill_name = %s',(pill_name,))
        self.pill_id = cur.fetchall()
        self.pill_id = self.pill_id[0][0]
    
    def Reg_save(self):
        for i in range(len(self.reg_total_info)):
            cur.execute('insert into schedule(user_id,pill_id, time, day_of_the_week, dosage) values(%s,%s,%s,%s,%s)', (self.name_category,self.pill_id,self.reg_total_info[i][0],self.reg_total_info[i][1],self.reg_total_info[i][2]))
            local.commit()
    #수정필요
    def Reg_update(self):
        self.reg_info=[]

        self.reg_info.append(self.reg_choose_time.currentText())
        self.reg_info.append(self.reg_day_of_the_week.currentText())
        self.reg_info.append(self.count_pill.text())
        cur.execute('update schedule set pill_id=%s,time=%s, day_of_the_week = %s, dosage = %s where user_id = %s', (self.pill_id,self.reg_total_info[0],self.reg_total_info[1],self.reg_total_info[2],self.name_category))
        local.commit()

    def conti_find_id(self):
        each_name = self.conti_select_user.currentText()
        cur.execute("select user_id from users where user_name = %s",((each_name,)))
        rows = cur.fetchall()
        for x in rows:
            for y in x:
               name_category =y
               print(name_category)
        cur.execute("select time,dose_status from logs where user_id = %s",((int(name_category),)))
        rows=cur.fetchall()
        print(len(rows))
        conti_pack = []
        self.conti_user_status.setRowCount(len(rows))

        for list in rows:
            for idx,item in enumerate(list):
                print(item)
                conti_pack.append(item)
                self.conti_user_status.setItem(0,idx,QTableWidgetItem(item))
        
    #삭제 할래말래 ?
    def delete_btn(self):
        self.groupBox_delete.setVisible(True)
    def delete_Y(self):
        each_name = self.manag_select_user.currentText()
        cur.execute("""DELETE FROM users WHERE user_name = %s""", ((each_name,)))
        local.commit()
        self.groupBox_delete.setVisible(False)
    def delete_N(self):
        self.groupBox_delete.setVisible(False)

    #수정 할래말래 ?
    def Manag_modi(self):
        self.groupBox_modify.setVisible(True)
    def Modi_complete_btn(self):
        modi_phn=self.modi_phone.toPlainText()
        modi_adr=self.modi_address.toPlainText()
        modi_dise=self.modi_disease.toPlainText()
        cur.execute("UPDATE users SET phone=%s,address=%s,disease_name=%s WHERE user_id=%s",(modi_phn,modi_adr,modi_dise,self.manag_name_category))
        local.commit()
        self.groupBox_modify.setVisible(False)
    def Modi_back_btn(self):
        self.groupBox_modify.setVisible(False)

    #admin 버튼(등록완료, 취소) 클릭 동작
    def admin_save(self):
        self.admin_info=[]
        self.admin_info.append(self.receive1_name.toPlainText())
        self.admin_info.append(self.receive2_sex.currentText())
        self.admin_info.append(self.receive3_phone.toPlainText())
        self.admin_info.append(self.receive4_address.toPlainText())
        self.admin_info.append(self.receive5_uid.toPlainText())
        cur.execute('insert into admin(admin_name,sex,phone,address,uid) values(%s,%s,%s,%s,%s)',(self.admin_info))
        local.commit()
        self.stackedWidget.setCurrentIndex(5)
    def admin_cancel(self):    
        self.stackedWidget.setCurrentIndex(5)
    
    def move_reg(self):
        self.stackedWidget.setCurrentIndex(6)
    def move_del(self):
        p=1
    #시리얼 통신부분
    def detected(self, uid):
        print("detected")
        self.uid = uid
        self.uid_list=[]
        cur.execute('select uid from admin')
        uid_info=cur.fetchall()
        for uid in uid_info:
            for id in uid:
                self.uid_list.append(id)
        if self.uid.hex() in self.uid_list:
            self.stackedWidget.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "경고", "등록되지 않은 카드입니다.")

        self.receive5_uid.setText(self.uid.hex())
        #self.timer.stop()
        #self.enable(0)
        return
    
    def send(self, command, data=0):
        print("send")
        req_data = struct.pack('<2s4sic', command, self.uid, data, b'\n')
        self.conn.write(req_data)
        return
    
    def getStatus(self):
        print("getStatus")
        self.send(b'GS')
        return
    
class Receiver(QThread):

    detected = pyqtSignal(bytes)

    def __init__(self, conn, parent=None):
        super(Receiver, self).__init__(parent)
        self.is_running = False
        self.conn = conn
        print("recv init")
    
    def run(self):
        print("recv start")
        self.is_running = True
        while (self.is_running == True):
            if self.conn.readable():
                res = self.conn.read_until(b'\n')
                #print(res)
                if len(res) > 2:
                    #print("res: ", res)
                    res = res[:-2]
                    cmd = res[:2].decode()
                    if cmd == 'GS' and res[2] == 0:
                        print("recv detected")
                        self.detected.emit(res[3:])
                        print(res[3:].hex())
                    else:
                        print("unknown error")
                        print(cmd)

if __name__ == "__main__":
    app=QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()

    sys.exit(app.exec_())