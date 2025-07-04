# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '界面.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QPushButton


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1800, 1200)
        MainWindow.setStyleSheet("QScrollBar:horizontal{\n"
                                 "    height:8px;\n"
                                 "    background:rgba(0,0,0,0%);\n"
                                 "border-radius:4px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::handle:horizontal{\n"
                                 "    background:rgba(125,125,125,50%);\n"
                                 "border-radius:4px;\n"
                                 "}\n"
                                 "QScrollBar::handle:horizontal:hover{\n"
                                 "    background:rgba(125,125,125,100%);\n"
                                 "    min-width:0;\n"
                                 "}\n"
                                 "QScrollBar::add-line:horizontal{\n"
                                 "    height:0px;width:0px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::sub-line:horizontal{\n"
                                 "    height:0px;width:0px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::add-line:horizontal:hover{\n"
                                 "    height:0px;width:0px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::sub-line:horizontal:hover{\n"
                                 "    height:0px;width:0px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal\n"
                                 "{\n"
                                 "    background:rgba(0,0,0,10%);\n"
                                 "    border-radius:4px;\n"
                                 "}\n"
                                 "\n"
                                 "QScrollBar:vertical{\n"
                                 "    width:8px;\n"
                                 "    background:rgba(0,0,0,0%);\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::handle:vertical{\n"
                                 "    width:0px;\n"
                                 "    background:rgba(125,125,125,50%);\n"
                                 "    border-radius:4px;\n"
                                 "}\n"
                                 "QScrollBar::handle:vertical:hover{\n"
                                 "    width:0px;\n"
                                 "    background:rgba(125,125,125,100%);\n"
                                 "    border-radius:4px;\n"
                                 "    min-width:20;\n"
                                 "}\n"
                                 "QScrollBar::add-line:vertical{\n"
                                 "    height:0px;width:0px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::sub-line:vertical{\n"
                                 "    height:0px;width:0px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::add-line:vertical:hover{\n"
                                 "    height:0px;width:0px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::sub-line:vertical:hover{\n"
                                 "    height:0px;width:0px;\n"
                                 "\n"
                                 "}\n"
                                 "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical\n"
                                 "{\n"
                                 "    background:rgba(0,0,0,10%);\n"
                                 "    border-radius:4px;\n"
                                 "}\n"
                                 "")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setStyleSheet("QFrame#frame{\n"
                                 "    background-color: rgba(255, 255, 255, 150);\n"
                                 "    border-radius:20px;\n"
                                 "}")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7.setSpacing(12)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.frame_2 = QtWidgets.QFrame(self.frame)
        self.frame_2.setStyleSheet("QFrame#frame_2{\n"
                                   "    background-color: rgba(255, 255, 255, 255);\n"
                                   "    border-radius:20px;\n"
                                   "}")
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_2.setContentsMargins(-1, -1, -1, 36)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame_5 = QtWidgets.QFrame(self.frame_2)
        self.frame_5.setStyleSheet("border:none")
        self.frame_5.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_5.setObjectName("frame_5")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.frame_5)
        self.horizontalLayout_6.setContentsMargins(-1, 24, -1, -1)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.widget_6 = QtWidgets.QWidget(self.frame_5)
        self.widget_6.setMinimumSize(QtCore.QSize(150, 150))
        self.widget_6.setMaximumSize(QtCore.QSize(150, 150))
        self.widget_6.setStyleSheet("image:url(./data/icon.png);\n"
                                    "border-radius:45px;\n"
                                    "background-color: rgb(223, 223, 223);")
        self.widget_6.setObjectName("widget_6")
        self.horizontalLayout_6.addWidget(self.widget_6)
        self.verticalLayout_2.addWidget(self.frame_5)
        self.label_2 = QtWidgets.QLabel(self.frame_2)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, 1)
        self.label_2.setFont(font)
        self.label_2.setStyleSheet("color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(42, 146, 138, 255), stop:1 rgba(90, 216, 212, 255));\n"
                                  "text-shadow: 2px 2px 3px rgba(0, 0, 0, 50);\n"
                                  "padding: 5px;\n"
                                  "font-weight: bold;")
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.listWidget = QtWidgets.QListWidget(self.frame_2)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.listWidget.setFont(font)
        self.listWidget.setStyleSheet("QListView {\n"
                                      "    padding-top:24px;\n"
                                      "    border-radius: 20px;\n"
                                      "    color: rgb(106, 106, 106);\n"
                                      "}\n"
                                      "QListView::item{\n"
                                      "background-color: transparent;\n"
                                      "height:40px;\n"
                                      "padding-left:12px;\n"
                                      "padding:12px;\n"
                                      "}\n"
                                      "QListView::item:hover {\n"
                                      "    background-color: rgba(216, 216, 216, 50);\n"
                                      "\n"
                                      "}\n"
                                      "QListView::item:selected {\n"
                                      "    /*background-color: transparent;*/\n"
                                      "    background-color: rgba(90, 216, 212,50);\n"
                                      "    color: rgb(40, 92, 90);\n"
                                      "border-left: 2px solid rgb(90, 216, 212)\n"
                                      "\n"
                                      "\n"
                                      "}\n"
                                      "")
        self.listWidget.setIconSize(QtCore.QSize(24, 24))
        self.listWidget.setObjectName("listWidget")
        item = QtWidgets.QListWidgetItem()
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/buttom/img/buttom/任天堂游戏_switch-nintendo.svg"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        item.setIcon(icon1)
        self.listWidget.addItem(item)
        item = QtWidgets.QListWidgetItem()
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/buttom/img/buttom/仪表盘_dashboard-one.svg"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        item.setIcon(icon2)
        self.listWidget.addItem(item)
        item = QtWidgets.QListWidgetItem()
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/buttom/img/buttom/中指_middle-finger.svg"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        item.setIcon(icon3)
        self.listWidget.addItem(item)

        item = QtWidgets.QListWidgetItem()
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/buttom/img/buttom/任天堂游戏_switch-nintendo.svg"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        item.setIcon(icon4)
        self.listWidget.addItem(item)

        item = QtWidgets.QListWidgetItem()
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/buttom/img/buttom/浏览器_browser.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        item.setIcon(icon5)
        self.listWidget.addItem(item)

        self.verticalLayout_2.addWidget(self.listWidget)
        self.clearButton = QtWidgets.QPushButton(self.frame_2)
        self.clearButton.setMinimumSize(QtCore.QSize(120, 50))
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.clearButton.setFont(font)
        self.clearButton.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 8px 16px;
                border-radius: 15px;
                background-color: rgb(180, 180, 180);
                color: white;
                font-weight: bold;
                border: 2px solid rgb(160, 160, 160);
                margin: 10px 20px;
            }
            QPushButton:hover {
                background-color: rgb(150, 150, 150);
                border: 2px solid rgb(130, 130, 130);
            }
            QPushButton:pressed {
                background-color: rgb(130, 130, 130);
                border: 2px solid rgb(110, 110, 110);
            }
        """)
        self.clearButton.setObjectName("clearButton")
        self.verticalLayout_2.addWidget(self.clearButton)
        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(2, 2)
        self.verticalLayout_2.setStretch(3, 1)
        self.horizontalLayout_7.addWidget(self.frame_2)
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setSpacing(12)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.frame_3 = QtWidgets.QFrame(self.frame)
        self.frame_3.setStyleSheet(".QFrame{\n"
                                   "    background-color: rgba(255, 255, 255, 0);\n"
                                   "    border-radius:20px;\n"
                                   "}")
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout_3.setContentsMargins(-1, 24, -1, -1)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_6.addWidget(self.frame_3)
        self.frame_4 = QtWidgets.QFrame(self.frame)
        self.frame_4.setStyleSheet(".QFrame{\n"
                                   "    background-color: rgba(255, 255, 255, 0);\n"
                                   "    border-radius:20px;\n"
                                   "}")
        self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_4.setObjectName("frame_4")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.frame_4)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.widget = QtWidgets.QWidget(self.frame_4)
        self.widget.setStyleSheet(".QFrame{\n"
                                  "    background-color: rgba(0, 0, 0, 0);\n"
                                  "    border-radius:20px;\n"
                                  "}\n"
                                  "")
        self.widget.setObjectName("widget")
        self.verticalLayout_4.addWidget(self.widget)
        self.verticalLayout_6.addWidget(self.frame_4)
        self.verticalLayout_6.setStretch(1, 1)
        self.horizontalLayout_7.addLayout(self.verticalLayout_6)
        self.horizontalLayout_7.setStretch(0, 1)
        self.horizontalLayout_7.setStretch(1, 4)
        self.closeButton = QtWidgets.QPushButton(self.frame)
        self.closeButton.setGeometry(QtCore.QRect(1750, 20, 30, 30))
        self.closeButton.setStyleSheet("QPushButton {\n"
                                       "    border: none;\n"
                                       "    background-color: rgba(255, 255, 255, 0);\n"
                                       "    image: url(:/resource/svg_icons/icon_close.svg);\n"
                                       "}\n"
                                       "\n"
                                       "QPushButton:hover {\n"
                                       "    background-color: rgba(255, 0, 0, 100);\n"
                                       "    border-radius: 15px;\n"
                                       "}")
        self.closeButton.setText("")
        self.closeButton.setObjectName("closeButton")
        self.minimizeButton = QtWidgets.QPushButton(self.frame)
        self.minimizeButton.setGeometry(QtCore.QRect(1710, 20, 30, 30))
        self.minimizeButton.setStyleSheet("QPushButton {\n"
                                          "    border: none;\n"
                                          "    background-color: rgba(255, 255, 255, 0);\n"
                                          "    image: url(:/resource/svg_icons/icon_minimize.svg);\n"
                                          "}\n"
                                          "\n"
                                          "QPushButton:hover {\n"
                                          "    background-color: rgba(0, 0, 255, 50);\n"
                                          "    border-radius: 15px;\n"
                                          "}")
        self.minimizeButton.setText("")
        self.minimizeButton.setObjectName("minimizeButton")
        self.horizontalLayout_8.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label_2.setText(_translate("MainWindow", "未来城智能垃圾处理平台"))
        self.clearButton.setText(_translate("MainWindow", "清除"))
        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        item = self.listWidget.item(0)
        item.setText(_translate("MainWindow", "丢垃圾指路"))
        item = self.listWidget.item(1)
        item.setText(_translate("MainWindow", "垃圾分类识别"))
        item = self.listWidget.item(2)
        item.setText(_translate("MainWindow", "垃圾桶信息查询"))
        item = self.listWidget.item(3)
        item.setText(_translate("MainWindow", "垃圾车最优遍历"))
        item = self.listWidget.item(4)
        item.setText(_translate("MainWindow", "网页端"))
        self.listWidget.setSortingEnabled(__sortingEnabled)
        # 关闭按钮
        self.close_btn = QPushButton("✕", MainWindow)
        self.close_btn.setFixedSize(45, 45)
        self.close_btn.setStyleSheet("""
            /* window-control-button-style */
            QPushButton {
                border-radius: 12px;
                background: rgba(200, 200, 200, 180);
                border: none;
                color: #555;
                font-family: Arial;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 0, 0, 120);
                color: white;
            }
        """)
        self.close_btn.setToolTip("关闭")
        self.close_btn.clicked.connect(MainWindow.close)
        self.close_btn.raise_()

        # toggle按钮
        self.toggle_btn = QPushButton("□", MainWindow)
        self.toggle_btn.setFixedSize(60, 60)
        self.toggle_btn.setStyleSheet("""
            /* window-control-button-style */
            QPushButton {
                border-radius: 12px;
                background: rgba(200, 200, 200, 180);
                border: none;
                color: #555;
                font-family: Arial;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(0, 255, 0, 120);
                color: white;
            }
        """)
        self.toggle_btn.setToolTip("窗口化/全屏化")
        self.toggle_btn.clicked.connect(
            lambda: MainWindow.showNormal() if MainWindow.isMaximized() else MainWindow.showMaximized())
        self.toggle_btn.raise_()

        # minimize按钮
        self.minimize_btn = QPushButton("−", MainWindow)
        self.minimize_btn.setFixedSize(60, 60)
        self.minimize_btn.setStyleSheet("""
            /* window-control-button-style */
            QPushButton {
                border-radius: 12px;
                background: rgba(200, 200, 200, 180);
                border: none;
                color: #555;
                font-family: Arial;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(0, 0, 255, 120);
                color: white;
            }
        """)
        self.minimize_btn.setToolTip("最小化")
        self.minimize_btn.clicked.connect(MainWindow.showMinimized)
        self.minimize_btn.raise_()

        self._update_top_btns_pos()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_top_btns_pos()

    def _update_top_btns_pos(self):
        margin_top = 18
        margin_right = 18
        btn_size = self.close_btn.width()
        # 关闭按钮最右
        self.close_btn.move(self.centralwidget.width() - btn_size - margin_right, margin_top)
        # toggle按钮在左侧
        self.toggle_btn.move(self.centralwidget.width() - btn_size * 2 - margin_right - 10, margin_top)
        # minimize按钮再左侧
        self.minimize_btn.move(self.centralwidget.width() - btn_size * 3 - margin_right - 20, margin_top)

    def get_window_control_btn_style(self, btn_type):
        """返回窗口控制按钮的样式
        
        Args:
            btn_type: 按钮类型，'close', 'toggle', 或 'minimize'
            
        Returns:
            按钮样式和文本
        """
        base_style = """
            QPushButton {
                border-radius: 12px;
                background: rgba(200, 200, 200, 180);
                border: none;
                color: #555;
                font-family: Arial;
                font-size: 16px;
                font-weight: bold;
            }
        """
        
        if btn_type == 'close':
            hover_style = """
            QPushButton:hover {
                background: rgba(255, 0, 0, 120);
                color: white;
            }
            """
            text = "✕"
            tooltip = "关闭"
        elif btn_type == 'toggle':
            hover_style = """
            QPushButton:hover {
                background: rgba(0, 255, 0, 120);
                color: white;
            }
            """
            text = "□"
            tooltip = "窗口化/全屏化"
        elif btn_type == 'minimize':
            hover_style = """
            QPushButton:hover {
                background: rgba(0, 0, 255, 120);
                color: white;
            }
            """
            text = "−"
            tooltip = "最小化"
        else:
            hover_style = ""
            text = ""
            tooltip = ""
            
        return base_style + hover_style, text, tooltip


import resource
