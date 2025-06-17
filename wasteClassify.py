import sys
# 现在导入zhipuai
import functools
import base64
import threading
from zhipuai import ZhipuAI
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, QHBoxLayout, QMainWindow, QApplication
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import os

# 设置智谱AI API密钥的默认值
DEFAULT_API_KEY = "be0ffc24eaaa41629f2c6a47af6c956e.U2s3r6ojZgi3dOiv"  # 默认API密钥

# 创建信号类，用于线程间通信
class SignalEmitter(QObject):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    enable_button_signal = pyqtSignal()
    
class WasteClassifyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = DEFAULT_API_KEY  # 直接使用默认API密钥
        self.rubbish_type = None
        
        # 创建信号对象
        self.classify_signals = SignalEmitter()
        self.classify_signals.result_signal.connect(self.update_classify_result)
        self.classify_signals.error_signal.connect(self.show_error)
        self.classify_signals.enable_button_signal.connect(self.enable_classify_button)
        
        self.initUI()
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('垃圾分类识别')
        self.resize(850, 750)
        self.setWindowIcon(QIcon('./data/icon.png'))
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: rgb(245, 245, 248);
                border-radius: 20px;
            }
            QLabel {
                color: rgb(80, 100, 100);
                font-size: 18px;
            }
            QPushButton {
                font-size: 18px;
                padding: 12px 24px;
                border-radius: 15px;
                background-color: rgb(60, 180, 180);
                color: white;
                font-weight: bold;
                border: 2px solid rgb(50, 160, 160);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: rgb(50, 170, 170);
                border: 2px solid rgb(40, 150, 150);
            }
            QPushButton:pressed {
                background-color: rgb(40, 150, 150);
                border: 2px solid rgb(30, 140, 140);
            }
            QWidget {
                font-size: 16px;
            }
        """)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: rgb(245, 245, 248);")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(25)
        
        # 创建标题标签
        title_label = QLabel('垃圾分类识别系统')
        title_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet('font-size: 36px; color: rgb(60, 90, 90); margin: 15px;')
        layout.addWidget(title_label)
        
        # 创建说明标签
        desc_label = QLabel('请选择一张图片，系统将识别图片中的垃圾类型')
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet('font-size: 18px; margin: 15px; color: rgb(80, 100, 100);')
        layout.addWidget(desc_label)
        
        # 创建选择图片按钮
        self.select_btn = QPushButton('选择图片')
        self.select_btn.setFixedHeight(55)
        self.select_btn.clicked.connect(self.select_image)
        self.select_btn.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            font-weight: bold;
            border: 2px solid #1976D2;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            font-size: 18px;
            padding: 12px 24px;
        """)
        layout.addWidget(self.select_btn)
        
        # 创建图片显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(320)
        self.image_label.setStyleSheet('border: 2px solid rgb(200, 200, 200); border-radius: 15px; margin: 15px; background-color: rgb(250, 250, 252);')
        layout.addWidget(self.image_label)
        
        # 创建识别结果标签
        self.result_label = QLabel('识别结果')
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet('font-size: 20px; font-weight: bold; margin: 20px; padding: 18px; border: 2px solid rgb(100, 100, 100); border-radius: 15px; background-color: rgb(240, 240, 245);')
        layout.addWidget(self.result_label)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # 创建识别按钮
        self.classify_btn = QPushButton('开始识别')
        self.classify_btn.setFixedHeight(55)
        self.classify_btn.clicked.connect(self.classify_waste)
        self.classify_btn.setEnabled(False)  # 初始禁用，直到选择了图片
        self.classify_btn.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            font-weight: bold;
            border: 2px solid #1976D2;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            font-size: 18px;
            padding: 12px 24px;
        """)
        button_layout.addWidget(self.classify_btn)
        
        # 创建返回按钮
        self.back_btn = QPushButton('返回主界面')
        self.back_btn.setFixedHeight(55)
        self.back_btn.setStyleSheet("""
            background-color: rgb(210, 210, 215);
            color: rgb(40, 40, 40);
            font-weight: bold;
            border: 2px solid rgb(180, 180, 185);
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        """)
        self.back_btn.clicked.connect(self.close)
        button_layout.addWidget(self.back_btn)
        
        layout.addLayout(button_layout)
        
        # 设置中央部件
        self.setCentralWidget(central_widget)
        
        self.image_path = None
        
    def select_image(self):
        # 打开文件对话框选择图片
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, '选择图片', '', 'Image Files (*.png *.jpg *.jpeg)')
        
        if file_path:
            self.image_path = file_path
            # 显示选择的图片
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(450, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(pixmap)
                self.classify_btn.setEnabled(True)  # 启用识别按钮
                # 重置结果标签样式为默认样式
                self.result_label.setStyleSheet('font-size: 20px; font-weight: bold; margin: 20px; padding: 18px; border: 2px solid rgb(100, 100, 100); border-radius: 15px; background-color: rgb(240, 240, 245); color: rgb(60, 60, 60);')
                self.result_label.setText('图片已加载，点击"开始识别"按钮进行识别')
            else:
                QMessageBox.warning(self, '错误', '无法加载所选图片')
    
    def classify_waste(self):
        if not self.image_path:
            QMessageBox.warning(self, '提示', '请先选择一张图片')
            return
        
        # 检查图片大小
        file_size = os.path.getsize(self.image_path)
        if file_size > 500 * 1024 * 1024:  # 500MB
            QMessageBox.warning(self, '警告', '图片大小超过500MB')
            return
            
        # 显示正在处理的消息
        self.result_label.setStyleSheet('font-size: 20px; font-weight: bold; margin: 20px; padding: 18px; border: 2px solid rgb(100, 100, 100); border-radius: 15px; background-color: #FFC107; color: black;')
        self.result_label.setText('正在识别中，请稍候...')
        self.classify_btn.setEnabled(False)
        
        # 创建线程执行AI请求
        threading.Thread(target=self._classify_thread, daemon=True).start()
    
    def _classify_thread(self):
        try:
            # 将图片转换为base64编码
            with open(self.image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 创建ZhipuAI客户端
            client = ZhipuAI(api_key=self.api_key)
            
            # 调用智谱AI进行图像识别
            response = client.chat.completions.create(
                model="glm-4v-flash",  # 使用更快的模型
                messages=[
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        {"type": "text", "text": "直接输出这个图片中的东西应该分类在哪种垃圾，不要输出其他内容。格式：厨余垃圾/其他垃圾/可回收垃圾/有害垃圾"}
                    ]}
                ]
            )
            
            # 处理响应结果
            if response and hasattr(response, 'choices') and len(response.choices) > 0:
                result = response.choices[0].message.content
                self.classify_signals.result_signal.emit(result)
            else:
                self.classify_signals.error_signal.emit('识别失败，请重试')
                
        except Exception as e:
            self.classify_signals.error_signal.emit(str(e))
        finally:
            self.classify_signals.enable_button_signal.emit()
    
    # 信号处理函数
    def update_classify_result(self, result):
        self.rubbish_type = result
        
        # 根据不同垃圾类型设置不同的背景色
        background_color = "rgb(240, 240, 245)"  # 默认背景色
        if "厨余垃圾" in result:
            background_color = "#8BC34A"  # 绿色
        elif "其他垃圾" in result:
            background_color = "#9E9E9E"  # 灰色
        elif "可回收垃圾" in result:
            background_color = "#2196F3"  # 蓝色
        elif "有害垃圾" in result:
            background_color = "#F44336"  # 红色
        
        # 设置结果标签的样式，包括背景色
        self.result_label.setStyleSheet(f'font-size: 20px; font-weight: bold; margin: 20px; padding: 18px; border: 2px solid rgb(80, 80, 80); border-radius: 15px; background-color: {background_color}; color: white; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);')
        self.result_label.setText(f"识别结果: {result}")
    
    def show_error(self, error_msg):
        # 错误信息使用红色背景
        self.result_label.setStyleSheet('font-size: 20px; font-weight: bold; margin: 20px; padding: 18px; border: 2px solid rgb(80, 80, 80); border-radius: 15px; background-color: #F44336; color: white; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);')
        self.result_label.setText(f"错误: {error_msg}")
        QMessageBox.warning(self, '错误', error_msg)
    
    def enable_classify_button(self):
        self.classify_btn.setEnabled(True)