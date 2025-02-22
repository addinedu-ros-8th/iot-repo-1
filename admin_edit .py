import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import mysql.connector
import serial
import struct

# MySQL 연결
local = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="Pill_guy"
)
cur = local.cursor()

from_class = uic.loadUiType("iot.ui")[0]

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("관리자 PC")

        name_list =['이명운1','이명운2','이명운3']
        self.reg_select_user.addItems(name_list)


        self.comboBox = QComboBox()
        days = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"])
        self.day_widgets = {}

        for day in days:
            day_widget = QWidget(self.stackWidget)
            self.day_widgets[day] = day_widget
            self.stackWidget.addWidget(day_widget) 

        self.stackWidget = QStackedWidget()

        self.comboBox.currentIndexChanged.connect(self.comboBox_changed)

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
        self.reg_day_of_the_week.currentIndexChanged.connect(self.week)
        
        # self.reg_dosage.clicked.connect(self.dosage_button)
        # self.reg_save.clicked.connect(self.save_button)

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


        self.reg_select_user.currentIndexChanged.connect(self.reg_find_id)
        self.conti_select_user.currentIndexChanged.connect(self.conti_find_id)
        self.manag_select_user.currentIndexChanged.connect(self.manag_find_id)
    # def week(self):

    #     for w in reg_week_list:
    #         self.comboBox.currentIndexChanged("월요일")
    #         self.setCurrentWidget(QWidget) 
    def comboBox_changed(self, day):
        self.stackpage_week.setCurrentIndex(day)
    def Reg_save(self):
        self.reg_A.setEditTriggers(QTableWidget.NoEditTriggers)
        self.reg_B.setEditTriggers(QTableWidget.NoEditTriggers)
        self.reg_C.setEditTriggers(QTableWidget.NoEditTriggers)

        #print(self.reg_A.rowCount())
        a=self.reg_A.rowCount()
        list_item = []
        time_list=[]
        time_change={'아침':'08:00','점심':'12:00','저녁':'18:00'}

        time=[]

        for i in range(a):
            #print(self.reg_A.item(i, 0).text())
            a_item = self.reg_A.item(i, 0).text()
            list_item.append(a_item)
            time.append(self.reg_A.verticalHeaderItem(i).text())
            time_list.append(time_change[time[i]])

        time=[]
        b=self.reg_B.rowCount()
        for i in range(b):
            #print(self.reg_B.item(i, 0).text())
            b_item = self.reg_B.item(i, 0).text()
            list_item.append(b_item)
            time.append(self.reg_B.verticalHeaderItem(i).text())
            time_list.append(time_change[time[i]])
        
        time=[]
        c=self.reg_C.rowCount()
        for i in range(c):
            #print(self.reg_C.item(i, 0).text())
            c_item = self.reg_C.item(i, 0).text()
            list_item.append(c_item)
            time.append(self.reg_C.verticalHeaderItem(i).text())
            time_list.append(time_change[time[i]])
        
        for i in range(len(list_item)):
            cur.execute('insert into schedule(time,dosage,user_id) values(%s,%s,%s)',(time_list[i],list_item[i],self.name_category))
            local.commit()
       
       # print(time_change[self.reg_A.verticalHeaderItem(0).text()])


    def Reg_update(self):
        self.reg_A.setEditTriggers(QTableWidget.AllEditTriggers)
        self.reg_B.setEditTriggers(QTableWidget.AllEditTriggers)
        self.reg_C.setEditTriggers(QTableWidget.AllEditTriggers)

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




if __name__ == "__main__":
    app=QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()

    sys.exit(app.exec_())