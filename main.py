from ui.界面 import Ui_MainWindow
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QPushButton, QDialog, QVBoxLayout, QHBoxLayout, \
    QLabel, QComboBox, QDialogButtonBox, QMessageBox, QWidget
import sys
from wasteClassify import WasteClassifyWindow
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import nearest_points
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import matplotlib.animation as animation
from numpy import linspace, array
import os
import time

# 导入自定义模块
from trash_navigation import TrashSelectionDialog, NavToNearestBin
from trash_bin_info import TrashBinInfo
from garbageTruck_navigation import TruckCountDialog, GarbageTruckNavigation

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class MyMainForm(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.start_x = None
        self.start_y = None
        self.anim = None
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)  # 设置窗口标志：隐藏窗口边框

        # 连接列表项的点击信号
        self.listWidget.itemClicked.connect(self.on_item_clicked)
        
        # 连接清除按钮到清除方法
        self.clearButton.clicked.connect(self.clear_display)
        
        # 垃圾分类窗口实例
        self.waste_classify_window = None

        # 数据存储
        self.points_gdf = None  # 点数据GeoDataFrame
        self.roads_gdf = None  # 路网数据GeoDataFrame
        self.graph = nx.Graph()  # 路网图结构
        
        # 路径规划相关
        self.selected_path = None  # 当前选择的路径
        self.road_network = None  # 道路网络
        self.nearest_road_point = None  # 最近的道路点
        self.nearest_bin_point = None  # 最近的垃圾桶点
        
        # 新增属性
        self.enable_navigation = False  # 是否启用导航功能
        self.click_point = None  # 点击点坐标
        self.click_to_road_path = None  # 点击点到道路的路径
        self.road_to_bin_path = None  # 道路到垃圾桶的路径
        
        # 垃圾桶信息查看相关
        self.enable_bin_info = False  # 是否启用垃圾桶信息查看
        self.bin_info_instance = None  # TrashBinInfo实例
        self.selected_bin = None  # 当前选中的垃圾桶
        
        # 垃圾类型和大小选择相关
        self.selected_trash_type = None  # 用户选择的垃圾类型
        self.selected_trash_size = None  # 用户选择的垃圾大小
        self.trash_selection_dialog = None  # 垃圾选择对话框
        
        # 垃圾车导航相关
        self.truck_navigator = None  # 垃圾车导航类
        self.truck_count_dialog = None  # 垃圾车数量选择对话框
        self.enable_truck_navigation = False  # 是否启用垃圾车导航功能
        self.truck_routes = None  # 垃圾车路径
        self.selected_truck_bins = []  # 用户选择的垃圾桶
        self.truck_count = 1  # 垃圾车数量
        self.route_colors = ['blue', 'red', 'green', 'purple', 'orange']  # 路径颜色
        self.selecting_bins = False  # 是否正在选择垃圾桶
        self.plan_btn = None  # 开始规划按钮
        
        # 动画相关
        self.truck_animations = []  # 垃圾车动画列表
        self.truck_artists = []  # 垃圾车图像对象列表
        self.animation_speed = 33  # 动画速度（帧间隔，单位：毫秒，值越大动画越慢）
        self.animation_running = False  # 动画是否正在运行
        
        # 行人动画相关
        self.pedestrian_animation = None  # 行人动画对象
        self.pedestrian_artist = None  # 行人图像对象
        self.pedestrian_animation_running = False  # 行人动画是否正在运行
        
        # 图标相关
        self.icon_scale_factor = 2.5  # 图标缩放系数 - 可以在这里直接调整所有图标大小
        self.base_icon_sizes = {
            '垃圾站': 0.07,
            '大垃圾桶': 0.04,
            '小垃圾桶': 0.03,
            '垃圾车': 0.03,
            '行人': 0.04
        }
        self.bin_icons = {
            '垃圾站': self.load_icon('垃圾站.png'),
            '大垃圾桶': self.load_icon('大垃圾桶.png'),
            '小垃圾桶': self.load_icon('小垃圾桶.png'),
            '垃圾车': self.load_icon('垃圾车.png'),
            '行人': self.load_icon('行人.png')
        }
        
        # 加载SHP数据
        self.points_gdf, self.roads_gdf = readSHP()
        
        # 构建道路网络
        self.build_road_network()
        
        # 初始化导航类
        self.navigator = None
        
        # 设置地图显示区域
        self.setupMapCanvas()
        
        # 显示地图
        self.displayMap()

    def load_icon(self, icon_name):
        """加载图标文件
        
        Args:
            icon_name: 图标文件名
            
        Returns:
            加载的图片对象，如果加载失败则返回None
        """
        icon_path = os.path.join('./data', icon_name)
        try:
            return mpimg.imread(icon_path)
        except Exception as e:
            print(f"加载图标 {icon_name} 失败: {e}")
            return None

    def setupMapCanvas(self):
        # 创建Figure对象
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # 将canvas添加到widget中
        layout = QtWidgets.QVBoxLayout(self.widget)
        layout.addWidget(self.canvas)
        self.widget.setLayout(layout)
        
        # 连接点击事件
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
    
    def get_bin_icon(self, bin_point):
        """根据垃圾桶类型和大小获取对应的图标
        
        Args:
            bin_point: 垃圾桶点数据
            
        Returns:
            图标对象和图标大小
        """
        # 获取垃圾桶名称和备注
        name = bin_point.get('Name', '')
        remark = bin_point.get('Remark', '')
        
        # 判断垃圾桶类型
        if remark.lower() == 'dumpster' or name.lower().startswith('td'):
            return self.bin_icons['垃圾站'], self.base_icon_sizes['垃圾站'] * self.icon_scale_factor
        elif name.lower().startswith('d'):
            return self.bin_icons['大垃圾桶'], self.base_icon_sizes['大垃圾桶'] * self.icon_scale_factor
        elif name.lower().startswith('x'):
            return self.bin_icons['小垃圾桶'], self.base_icon_sizes['小垃圾桶'] * self.icon_scale_factor
        else:
            return self.bin_icons['小垃圾桶'], self.base_icon_sizes['小垃圾桶'] * self.icon_scale_factor
    
    def add_bin_icon(self, ax, bin_point, highlight=False, zorder=2):
        """向地图添加垃圾桶图标
        
        Args:
            ax: matplotlib轴对象
            bin_point: 垃圾桶点数据
            highlight: 是否高亮显示
            zorder: 图层顺序
            
        Returns:
            添加的AnnotationBbox对象
        """
        bin_geom = bin_point.geometry
        icon, icon_size = self.get_bin_icon(bin_point)
        
        if icon is None:
            # 如果图标加载失败，使用默认标记
            return ax.plot(bin_geom.x, bin_geom.y, 'ro', markersize=8, zorder=zorder)
        
        # 创建OffsetImage
        img_box = OffsetImage(icon, zoom=icon_size)
        
        # 创建AnnotationBbox
        ab = AnnotationBbox(img_box, (bin_geom.x, bin_geom.y), 
                           frameon=highlight,  # 高亮时显示边框
                           bboxprops=dict(edgecolor='green' if highlight else 'none', 
                                         linewidth=2),
                           pad=0.0,
                           zorder=zorder)
        
        # 添加到图中
        ax.add_artist(ab)
        return ab
    
    def displayMap(self):
        # 清除之前的图形
        self.figure.clear()
        
        # 创建子图
        ax = self.figure.add_subplot(111)
        
        # 绘制路网
        if self.roads_gdf is not None:
            self.roads_gdf.plot(ax=ax, color='gray', linewidth=1)
        
        # 绘制垃圾桶点位（使用图标）
        if self.points_gdf is not None:
            for idx, bin_point in self.points_gdf.iterrows():
                # 判断是否需要高亮显示（被选中的垃圾桶）
                highlight = (self.selecting_bins and idx in self.selected_truck_bins)
                # 如果是垃圾站td1，使用垃圾站图标
                bin_name = bin_point.get('Name', '')
                
                # 设置合适的zorder（图层顺序），高亮显示的在上层
                zorder = 5 if highlight else 2
                
                # 添加图标
                self.add_bin_icon(ax, bin_point, highlight, zorder)
                
                # 如果是选中的垃圾桶，添加序号标签
                if highlight:
                    bin_idx = self.selected_truck_bins.index(idx) + 1
                    ax.annotate(f"{bin_idx}", 
                               xy=(bin_point.geometry.x, bin_point.geometry.y),
                               xytext=(0, 0),
                               textcoords="offset points",
                               ha='center', va='center',
                               bbox=dict(boxstyle="circle,pad=0.3", fc="white", ec="green", alpha=0.8),
                               zorder=6)
        
        # 导航模式：绘制选择的路径（如果有）
        if self.selected_path is not None and self.enable_navigation:
            # 确保路径是有效的LineString
            if hasattr(self.selected_path, 'xy'):
                x, y = self.selected_path.xy
                ax.plot(x, y, color='blue', linewidth=3, linestyle='-', zorder=3)
        
        # 垃圾车导航模式：绘制多条路径
        if self.truck_routes is not None and self.enable_truck_navigation:
            # 如果是单车模式
            if not isinstance(self.truck_routes, list):
                route = self.truck_routes
                # 绘制路径
                for path in route['route_paths']:
                    if hasattr(path, 'xy'):
                        x, y = path.xy
                        ax.plot(x, y, color='blue', linewidth=3, linestyle='-', zorder=3)
                
                # 绘制点
                for j, point in enumerate(route['route_points']):
                    if j == 0 or j == len(route['route_points']) - 1:
                        # 起点和终点用星星标记，不使用垃圾车图标
                        ax.plot(point.x, point.y, marker='*', markersize=15, 
                                color='blue', markeredgecolor='black', zorder=4)
                        
                        # 添加垃圾车编号标签
                        ax.annotate(f"车1", 
                                  xy=(point.x, point.y),
                                  xytext=(10, 10),
                                  textcoords="offset points",
                                  bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
                                  zorder=6)
                    else:
                        # 中间点用圆形标记
                        ax.plot(point.x, point.y, marker='o', markersize=10, 
                                color='blue', markeredgecolor='black', zorder=4)
            else:
                # 多车模式
                for i, route in enumerate(self.truck_routes):
                    # 获取颜色
                    color = self.route_colors[i % len(self.route_colors)]
                    
                    # 绘制路径
                    for path in route['route_paths']:
                        if hasattr(path, 'xy'):
                            x, y = path.xy
                            ax.plot(x, y, color=color, linewidth=3, linestyle='-', zorder=3)
                    
                    # 绘制点
                    for j, point in enumerate(route['route_points']):
                        if j == 0 or j == len(route['route_points']) - 1:
                            # 起点和终点用星星标记，不使用垃圾车图标
                            ax.plot(point.x, point.y, marker='*', markersize=15, 
                                    color=color, markeredgecolor='black', zorder=4)
                            
                            # 添加垃圾车编号标签
                            ax.annotate(f"车{route['truck_id']}", 
                                      xy=(point.x, point.y),
                                      xytext=(10, 10),
                                      textcoords="offset points",
                                      bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
                                      zorder=6)
                        else:
                            # 中间点用圆形标记
                            ax.plot(point.x, point.y, marker='o', markersize=10, 
                                    color=color, markeredgecolor='black', zorder=4)
        
        # 单独绘制点击点（如果有）
        if self.click_point is not None:
            ax.plot(self.click_point.x, self.click_point.y, 'mo', markersize=10, zorder=5)
            
        # 绘制最近道路点（如果有）
        if self.nearest_road_point is not None and self.enable_navigation:
            ax.plot(self.nearest_road_point.x, self.nearest_road_point.y, 'go', markersize=8, zorder=4)
        
        # 绘制最近垃圾桶点（如果有）
        if self.nearest_bin_point is not None and self.enable_navigation:
            ax.plot(self.nearest_bin_point.x, self.nearest_bin_point.y, 'yo', markersize=12, zorder=4)
        
        # 垃圾桶信息模式：高亮显示选中的垃圾桶
        if self.selected_bin is not None and self.enable_bin_info:
            bin_geom = self.selected_bin['geometry']
            
            # 获取垃圾桶类型和大小信息
            bin_type_str = '、'.join(self.selected_bin['type']) if self.selected_bin['type'] else '未知类型'
            bin_size = self.selected_bin['size']
            
            # 使用图标绘制
            if bin_size == '垃圾站':
                icon = self.bin_icons['垃圾站']
                icon_size = self.base_icon_sizes['垃圾站'] * self.icon_scale_factor
            elif bin_size == '大垃圾桶':
                icon = self.bin_icons['大垃圾桶']
                icon_size = self.base_icon_sizes['大垃圾桶'] * self.icon_scale_factor
            else:
                icon = self.bin_icons['小垃圾桶']
                icon_size = self.base_icon_sizes['小垃圾桶'] * self.icon_scale_factor
            
            if icon is not None:
                img_box = OffsetImage(icon, zoom=icon_size)
                ab = AnnotationBbox(img_box, (bin_geom.x, bin_geom.y), 
                                 frameon=True,
                                 bboxprops=dict(edgecolor='blue', linewidth=2),
                                 pad=0.0,
                                 zorder=5)
                ax.add_artist(ab)
            else:
                ax.plot(bin_geom.x, bin_geom.y, 'bo', markersize=15, zorder=5)
            
            # 添加垃圾桶信息标签
            label = f"{bin_type_str}\n{bin_size}"
            ax.annotate(label, 
                       xy=(bin_geom.x, bin_geom.y),
                       xytext=(10, 10),
                       textcoords="offset points",
                       bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
                       zorder=6)
        
        # 如果正在选择垃圾桶模式，添加规划按钮
        if self.selecting_bins:
            # 添加"开始规划"按钮
            self.add_plan_button()
        
        # 隐藏坐标轴
        ax.set_axis_off()
        
        # 刷新canvas
        self.canvas.draw()

    def toggleMaximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            super(MyMainForm, self).mousePressEvent(event)
            self.start_x = event.x()
            self.start_y = event.y()

    def mouseReleaseEvent(self, event):
        self.start_x = None
        self.start_y = None

    def mouseMoveEvent(self, event):
        try:
            super(MyMainForm, self).mouseMoveEvent(event)
            dis_x = event.x() - self.start_x
            dis_y = event.y() - self.start_y
            self.move(self.x() + dis_x, self.y() + dis_y)
        except:
            pass

    def effect_shadow_style(self, widget):
        effect_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        effect_shadow.setOffset(12, 12)  # 偏移
        effect_shadow.setBlurRadius(128)  # 阴影半径
        effect_shadow.setColor(QColor(155, 230, 237, 150))  # 阴影颜色
        widget.setGraphicsEffect(effect_shadow)
    
    def on_item_clicked(self, item):
        # 获取点击的项目文本
        item_text = item.text()
        
        # 清除当前的绘图内容
        self.clear_display()
        
        # 如果点击的是"垃圾识别"，打开垃圾分类窗口
        if item_text == "垃圾分类识别":
            if not self.waste_classify_window:
                self.waste_classify_window = WasteClassifyWindow()
            self.waste_classify_window.show()
        # 如果点击的是"丢垃圾"，启用导航功能
        elif item_text == "丢垃圾指路":
            # 初始化导航类
            if not self.navigator:
                self.navigator = NavToNearestBin(self.roads_gdf, self.points_gdf, self.road_network)
            
            # 显示垃圾类型和大小选择对话框
            self.trash_selection_dialog = TrashSelectionDialog(self)
            if self.trash_selection_dialog.exec_() == QDialog.Accepted:
                # 获取用户选择的垃圾类型和大小
                self.selected_trash_type, self.selected_trash_size = self.trash_selection_dialog.get_selection()
                
                # 启用导航功能
                self.enable_navigation = True
                
                # 设置按钮为选中状态
                self.listWidget.item(0).setSelected(True)
                print(f"导航功能已启用，将为您导航到适合{self.selected_trash_type}的{self.selected_trash_size}垃圾桶")
                print("请点击地图任意位置开始导航")
            else:
                # 用户取消了选择，不启用导航功能
                return
        # 如果点击的是"垃圾桶信息"，启用垃圾桶信息查看功能
        elif item_text == "垃圾桶信息查询":
            # 初始化垃圾桶信息类
            if not self.bin_info_instance:
                self.bin_info_instance = TrashBinInfo(self.points_gdf)
            
            # 启用垃圾桶信息查看功能
            self.enable_bin_info = True
            
            # 设置按钮为选中状态
            self.listWidget.item(2).setSelected(True)
            # 创建并显示提示消息弹窗
            msg_box = QMessageBox()
            msg_box.setWindowTitle("操作提示")
            msg_box.setText("垃圾桶信息查看功能已启用\n请点击地图上的垃圾桶查看详细信息")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.exec_()
            print("垃圾桶信息查看功能已启用，请点击地图上的垃圾桶查看信息")
        # 如果点击的是"垃圾车最优遍历"，启用垃圾车导航功能
        elif item_text == "垃圾车最优遍历":
            # 初始化垃圾车导航类
            if not self.truck_navigator:
                self.truck_navigator = GarbageTruckNavigation(self.roads_gdf, self.points_gdf)
            
            # 显示垃圾车数量选择对话框
            self.truck_count_dialog = TruckCountDialog(self)
            if self.truck_count_dialog.exec_() == QDialog.Accepted:
                # 获取用户选择的垃圾车数量
                self.truck_count = self.truck_count_dialog.get_truck_count()
                
                # 清空已选择的垃圾桶
                self.selected_truck_bins = []
                
                # 启用垃圾桶选择模式
                self.selecting_bins = True
                
                # 设置按钮为选中状态
                self.listWidget.item(3).setSelected(True)
                
                # 显示提示消息
                QMessageBox.information(self, "操作提示", 
                                       f"请在地图上点击选择需要回收的垃圾桶。\n"
                                       f"垃圾车数量: {self.truck_count}\n"
                                       f"选择完成后，点击'开始规划'按钮进行路径规划。")
                
                # 重新显示地图
                self.displayMap()
            else:
                # 用户取消了选择，不启用垃圾车导航功能
                return
                
    def disable_navigation(self):
        """关闭导航功能"""
        # 清除选中状态
        self.listWidget.item(0).setSelected(False)
        # 停止行人动画
        if self.pedestrian_animation_running:
            self.stop_pedestrian_animation()
        # 清除路径
        self.selected_path = None
        self.click_point = None
        self.click_to_road_path = None
        self.road_to_bin_path = None
        self.nearest_road_point = None
        self.nearest_bin_point = None
        # 清除选择的垃圾类型和大小
        self.selected_trash_type = None
        self.selected_trash_size = None
        # 禁用导航功能
        self.enable_navigation = False
        # 重新显示地图
        self.displayMap()
        print("导航功能已禁用")
        
    def disable_truck_navigation(self):
        """关闭垃圾车导航功能"""
        # 清除选中状态
        self.listWidget.item(3).setSelected(False)
        # 停止动画
        self.stop_animations()
        # 清除路径
        self.truck_routes = None
        self.selected_truck_bins = []
        # 禁用垃圾车导航功能
        self.enable_truck_navigation = False
        self.selecting_bins = False
        # 移除规划按钮（如果存在）
        if self.plan_btn:
            self.plan_btn.setParent(None)
            self.plan_btn = None
        # 重新显示地图
        self.displayMap()
        print("垃圾车最优遍历功能已禁用")
    
    def add_plan_button(self):
        """添加开始规划按钮"""
        if not self.plan_btn:
            self.plan_btn = QPushButton("开始规划", self)
            self.plan_btn.setGeometry(QtCore.QRect(self.width() - 150, 100, 120, 40))
            self.plan_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    padding: 8px 16px;
                    border-radius: 10px;
                    background-color: rgb(60, 180, 180);
                    color: white;
                    font-weight: bold;
                    border: 2px solid rgb(50, 160, 160);
                }
                QPushButton:hover {
                    background-color: rgb(50, 170, 170);
                    border: 2px solid rgb(40, 150, 150);
                }
                QPushButton:pressed {
                    background-color: rgb(40, 150, 150);
                    border: 2px solid rgb(30, 140, 140);
                }
            """)
            self.plan_btn.clicked.connect(self.on_plan_button_clicked)
            self.plan_btn.show()
    
    def on_plan_button_clicked(self):
        """规划按钮点击处理"""
        # 检查是否有选中的垃圾桶
        if not self.selected_truck_bins:
            QMessageBox.warning(self, "提示", "请至少选择一个垃圾桶！")
            return
        
        # 规划最优路径
        self.truck_routes = self.truck_navigator.plan_optimal_route(
            self.selected_truck_bins, 
            self.truck_count
        )
        
        if not self.truck_routes:
            QMessageBox.warning(self, "警告", "无法规划路径，请检查选择的垃圾桶是否可达！")
            return
        
        # 启用垃圾车导航功能
        self.enable_truck_navigation = True
        self.selecting_bins = False
        
        # 移除规划按钮
        if self.plan_btn:
            self.plan_btn.setParent(None)
            self.plan_btn = None
        
        # 显示路径信息
        if isinstance(self.truck_routes, list):
            # 多辆垃圾车
            routes_info = "垃圾车最优遍历路径规划完成:\n"
            for route in self.truck_routes:
                routes_info += f"垃圾车{route['truck_id']}: 经过垃圾桶 {len(route['bin_ids']) - 2} 个\n"
        else:
            # 单辆垃圾车
            route = self.truck_routes
            routes_info = "垃圾车最优遍历路径规划完成:\n"
            routes_info += f"经过垃圾桶: {len(route['bin_ids']) - 2} 个\n"
        
        # 显示路径信息
        QMessageBox.information(self, "路径规划结果", routes_info)
        
        # 绘制路径并启动动画
        self.displayMap()
        self.animate_truck_route()

    def animate_truck_route(self, speed=None):
        """创建并启动垃圾车路径动画
        
        Args:
            speed: 动画速度（帧间隔，单位：毫秒），如果为None则使用默认速度
        """
        # 停止现有动画
        self.stop_animations()
        
        # 更新动画速度（如果指定）
        if speed is not None:
            self.animation_speed = max(1, min(speed, 200))  # 限制在1-200ms之间
        
        # 清空动画列表
        self.truck_animations = []
        self.truck_artists = []
        
        # 创建新的动画
        if isinstance(self.truck_routes, list) and len(self.truck_routes) > 1:
            # 多辆垃圾车 - 使用单一动画来避免闪烁
            self.create_multi_truck_animation(self.truck_routes)
        else:
            # 单辆垃圾车
            route = self.truck_routes if not isinstance(self.truck_routes, list) else self.truck_routes[0]
            anim = self.create_truck_animation(route, 'blue', 1)
            if anim:
                self.truck_animations.append(anim)
        
        # 设置动画状态
        self.animation_running = True
        
        # 提示动画已启动
        if self.truck_animations:
            print("垃圾车动画已启动")
    
    def create_multi_truck_animation(self, routes):
        """为多辆垃圾车创建单一动画对象以避免闪烁
        
        Args:
            routes: 垃圾车路径数据列表
        """
        try:
            # 准备所有路径和艺术家对象
            all_trucks_data = []
            
            for i, route in enumerate(routes):
                color = self.route_colors[i % len(self.route_colors)]
                truck_id = route['truck_id']
                
                # 检查路径是否有效
                if not route['route_paths'] or len(route['route_paths']) == 0:
                    print(f"垃圾车{truck_id}的路径无效")
                    continue
                
                # 准备路径点
                all_points = []
                for path in route['route_paths']:
                    if hasattr(path, 'xy'):
                        x, y = path.xy
                        points = np.array(list(zip(x, y)))
                        all_points.extend(points)
                
                if not all_points or len(all_points) < 2:
                    print(f"垃圾车{truck_id}的路径点不足")
                    continue
                
                all_points = np.array(all_points)
                
                # 计算路径点之间的累积距离
                distances = [0]
                for i in range(1, len(all_points)):
                    prev_point = all_points[i-1]
                    curr_point = all_points[i]
                    dist = np.sqrt((curr_point[0] - prev_point[0])**2 + (curr_point[1] - prev_point[1])**2)
                    distances.append(distances[-1] + dist)
                
                total_distance = distances[-1]
                if total_distance <= 0:
                    print(f"垃圾车{truck_id}的路径长度为0")
                    continue
                
                # 创建垃圾车图标
                truck_icon = self.bin_icons['垃圾车']
                if truck_icon is None:
                    print("垃圾车图标加载失败")
                    continue
                
                # 垃圾车图标缩放比例
                zoom = 0.05 * self.icon_scale_factor
                imagebox = OffsetImage(truck_icon, zoom=zoom)
                
                # 创建AnnotationBbox
                truck_artist = AnnotationBbox(
                    imagebox, 
                    (all_points[0][0], all_points[0][1]),  # 起始位置
                    xycoords='data',
                    boxcoords='data',
                    frameon=False,
                    pad=0.0,
                    zorder=10 + truck_id  # 确保不同车辆在不同层级
                )
                
                # 添加到图中
                self.figure.axes[0].add_artist(truck_artist)
                self.truck_artists.append(truck_artist)
                
                # 保存车辆数据
                all_trucks_data.append({
                    'truck_id': truck_id,
                    'points': all_points,
                    'distances': distances,
                    'total_distance': total_distance,
                    'artist': truck_artist
                })
            
            if not all_trucks_data:
                return
            
            # 确定帧数 - 根据所有路径中最长的一个
            max_points = max([len(data['points']) for data in all_trucks_data])
            num_frames = min(300, max(150, int(max_points * 2)))
            
            # 定义多车动画更新函数
            def update_multi_truck(frame):
                artists = []
                for truck_data in all_trucks_data:
                    try:
                        all_points = truck_data['points']
                        distances = truck_data['distances']
                        total_distance = truck_data['total_distance']
                        truck_artist = truck_data['artist']
                        
                        # 计算当前位置
                        if frame == 0:
                            pos = all_points[0]
                        else:
                            # 计算目标距离
                            target_distance = frame / (num_frames - 1) * total_distance
                            
                            # 找到最近的路径段
                            idx = np.searchsorted(distances, target_distance) - 1
                            idx = max(0, min(idx, len(all_points) - 2))  # 确保索引有效
                            
                            # 计算插值点
                            p1 = all_points[idx]
                            p2 = all_points[idx + 1]
                            segment_length = distances[idx + 1] - distances[idx]
                            
                            if segment_length > 0:
                                alpha = (target_distance - distances[idx]) / segment_length
                            else:
                                alpha = 0
                            
                            # 线性插值计算当前位置
                            pos = p1 + alpha * (p2 - p1)
                        
                        # 更新垃圾车位置
                        truck_artist.xybox = pos
                        artists.append(truck_artist)
                    except Exception as e:
                        print(f"垃圾车动画更新错误: {e}")
                
                return artists
            
            # 创建动画
            anim = animation.FuncAnimation(
                self.figure, 
                update_multi_truck, 
                frames=num_frames,
                interval=self.animation_speed,
                blit=True,
                repeat=True
            )
            
            # 添加到动画列表
            self.truck_animations.append(anim)
            
            # 刷新画布
            self.canvas.draw()
            
        except Exception as e:
            print(f"创建多车动画错误: {e}")
    
    def create_truck_animation(self, route, color, truck_id):
        """为单个垃圾车创建动画
        
        Args:
            route: 垃圾车路径数据
            color: 路径颜色
            truck_id: 垃圾车编号
            
        Returns:
            animation对象
        """
        try:
            # 检查路径是否有效
            if not route['route_paths'] or len(route['route_paths']) == 0:
                print(f"垃圾车{truck_id}的路径无效")
                return None
            
            # 准备路径点
            all_points = []
            for path in route['route_paths']:
                if hasattr(path, 'xy'):
                    x, y = path.xy
                    points = np.array(list(zip(x, y)))
                    all_points.extend(points)
            
            if not all_points or len(all_points) < 2:
                print(f"垃圾车{truck_id}的路径点不足")
                return None
            
            all_points = np.array(all_points)
            
            # 计算路径点之间的累积距离
            distances = [0]
            for i in range(1, len(all_points)):
                prev_point = all_points[i-1]
                curr_point = all_points[i]
                dist = np.sqrt((curr_point[0] - prev_point[0])**2 + (curr_point[1] - prev_point[1])**2)
                distances.append(distances[-1] + dist)
            
            total_distance = distances[-1]
            if total_distance <= 0:
                print(f"垃圾车{truck_id}的路径长度为0")
                return None
            
            # 创建垃圾车图标
            truck_icon = self.bin_icons['垃圾车']
            if truck_icon is None:
                print("垃圾车图标加载失败")
                return None
            
            # 垃圾车图标缩放比例，可以根据路径长度调整
            zoom = 0.05 * self.icon_scale_factor
            imagebox = OffsetImage(truck_icon, zoom=zoom)
            
            # 创建AnnotationBbox
            truck_artist = AnnotationBbox(
                imagebox, 
                (all_points[0][0], all_points[0][1]),  # 起始位置
                xycoords='data',
                boxcoords='data',
                frameon=False,
                pad=0.0,
                zorder=10  # 确保在其他元素上方显示
            )
            
            # 添加到图中
            self.figure.axes[0].add_artist(truck_artist)
            self.truck_artists.append(truck_artist)
            
            # 确定帧数（根据路径长度和复杂度自动调整）
            num_frames = min(200, max(100, int(len(all_points) * 2)))
            
            # 定义动画更新函数
            def update(frame):
                try:
                    # 计算当前位置
                    if frame == 0:
                        pos = all_points[0]
                    else:
                        # 计算目标距离
                        target_distance = frame / (num_frames - 1) * total_distance
                        
                        # 找到最近的路径段
                        idx = np.searchsorted(distances, target_distance) - 1
                        idx = max(0, min(idx, len(all_points) - 2))  # 确保索引有效
                        
                        # 计算插值点
                        p1 = all_points[idx]
                        p2 = all_points[idx + 1]
                        segment_length = distances[idx + 1] - distances[idx]
                        
                        if segment_length > 0:
                            alpha = (target_distance - distances[idx]) / segment_length
                        else:
                            alpha = 0
                        
                        # 线性插值计算当前位置
                        pos = p1 + alpha * (p2 - p1)
                    
                    # 更新垃圾车位置
                    truck_artist.xybox = pos
                    
                    return [truck_artist]
                except Exception as e:
                    print(f"动画更新错误: {e}")
                    return []
            
            # 创建动画
            anim = animation.FuncAnimation(
                self.figure, 
                update, 
                frames=num_frames,
                interval=self.animation_speed,
                blit=True,
                repeat=True
            )
            
            # 刷新画布
            self.canvas.draw()
            
            return anim
        except Exception as e:
            print(f"创建垃圾车动画错误: {e}")
            return None
    
    def stop_animations(self):
        """停止所有动画"""
        try:
            # 停止垃圾车动画
            for anim in self.truck_animations:
                try:
                    if hasattr(anim, 'event_source') and anim.event_source:
                        anim.event_source.stop()
                except Exception as e:
                    print(f"停止动画错误: {e}")
            
            # 停止行人动画
            if self.pedestrian_animation and hasattr(self.pedestrian_animation, 'event_source') and self.pedestrian_animation.event_source:
                self.pedestrian_animation.event_source.stop()
            
            # 从图中移除所有垃圾车图标和文本
            if hasattr(self, 'figure') and self.figure and hasattr(self.figure, 'axes') and self.figure.axes:
                ax = self.figure.axes[0]
                
                # 移除所有AnnotationBbox对象（垃圾车图标和行人图标）
                for artist in list(ax.artists):
                    if isinstance(artist, AnnotationBbox):
                        artist.remove()
                
                # 移除所有文本注释
                for text in list(ax.texts):
                    if hasattr(text, 'get_text') and '车' in text.get_text():
                        text.remove()
            
            # 清空列表
            self.truck_animations = []
            self.truck_artists = []
            self.animation_running = False
            
            # 清空行人动画相关属性
            self.pedestrian_animation = None
            self.pedestrian_artist = None
            self.pedestrian_animation_running = False
            
            # 刷新画布
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.draw()
        except Exception as e:
            print(f"停止动画时发生错误: {e}")
            # 如果出错，尝试重置状态
            self.truck_animations = []
            self.truck_artists = []
            self.animation_running = False
            self.pedestrian_animation = None
            self.pedestrian_artist = None
            self.pedestrian_animation_running = False
    
    def build_road_network(self):
        """构建道路网络图结构"""
        # 创建一个新的网络图
        self.road_network = nx.Graph()
        
        if self.roads_gdf is None:
            return
            
        # 遍历每条道路线
        for idx, road in self.roads_gdf.iterrows():
            geom = road.geometry
            
            # 处理LineString
            if isinstance(geom, LineString):
                coords = list(geom.coords)
                # 添加节点和边
                for i in range(len(coords) - 1):
                    start_node = coords[i]
                    end_node = coords[i + 1]
                    # 计算两点之间的距离作为边的权重
                    distance = Point(start_node).distance(Point(end_node))
                    self.road_network.add_edge(start_node, end_node, weight=distance)
            
            # 处理MultiLineString
            elif isinstance(geom, MultiLineString):
                for line in geom.geoms:
                    coords = list(line.coords)
                    for i in range(len(coords) - 1):
                        start_node = coords[i]
                        end_node = coords[i + 1]
                        distance = Point(start_node).distance(Point(end_node))
                        self.road_network.add_edge(start_node, end_node, weight=distance)
    
    def on_map_click(self, event):
        """处理地图点击事件"""
        if event.inaxes is None:
            return
            
        # 获取点击位置的坐标
        x, y = event.xdata, event.ydata
        click_point = Point(x, y)
        self.click_point = click_point
        
        # 垃圾桶选择模式
        if self.selecting_bins:
            # 查找最近的垃圾桶
            nearest_bin_id = self.find_nearest_bin(click_point)
            if nearest_bin_id is None:
                return
                
            # 获取垃圾桶名称
            bin_name = self.points_gdf.loc[nearest_bin_id].get('Name', '')
            
            # 排除td1垃圾站（它是起点和终点）
            if bin_name.lower() == 'td1':
                QMessageBox.information(self, "提示", "td1垃圾站是起点和终点，不能选择！")
                return
                
            # 检查是否已经选择了该垃圾桶
            if nearest_bin_id in self.selected_truck_bins:
                # 如果已选择，则移除
                self.selected_truck_bins.remove(nearest_bin_id)
                print(f"取消选择垃圾桶: {bin_name}")
            else:
                # 如果未选择，则添加
                self.selected_truck_bins.append(nearest_bin_id)
                print(f"选择垃圾桶: {bin_name}")
            
            # 更新地图显示
            self.displayMap()
            return
        
        # 导航模式
        elif self.enable_navigation:
            # 确保导航器已初始化
            if not self.navigator:
                self.navigator = NavToNearestBin(self.roads_gdf, self.points_gdf, self.road_network)
            
            # 查找最近的道路点
            nearest_road_point = self.navigator.find_nearest_road_point(click_point)
            if nearest_road_point is None:
                return
                
            self.nearest_road_point = nearest_road_point
            
            # 创建从点击点到最近道路点的直线路径
            self.click_to_road_path = LineString([(click_point.x, click_point.y), 
                                                (nearest_road_point.x, nearest_road_point.y)])
            
            # 查找适合所选垃圾类型和大小的垃圾桶
            if self.selected_trash_type and self.selected_trash_size:
                nearest_bin_result = self.navigator.find_suitable_trash_bin(
                    nearest_road_point, 
                    self.selected_trash_type, 
                    self.selected_trash_size
                )
            else:
                # 如果没有选择垃圾类型和大小，则查找最近的垃圾桶
                nearest_bin_result = self.navigator.find_nearest_trash_bin(nearest_road_point)
                
            if nearest_bin_result is None:
                return
                
            nearest_bin, nearest_bin_node = nearest_bin_result
            self.nearest_bin_point = nearest_bin
            
            # 计算从最近道路点到最近垃圾桶的路径
            road_to_bin_path = self.navigator.calculate_path(nearest_road_point, nearest_bin_node)
            if road_to_bin_path is None:
                return
                
            self.road_to_bin_path = road_to_bin_path
            
            # 合并路径段
            if self.click_to_road_path and self.road_to_bin_path:
                # 完整路径是两段路径的组合
                self.selected_path = LineString(list(self.click_to_road_path.coords) + 
                                            list(self.road_to_bin_path.coords)[1:])
            else:
                self.selected_path = None
            
            # 重新显示地图
            self.displayMap()
            
            # 启动行人动画
            if self.selected_path is not None:
                self.animate_pedestrian_route()
        
        # 垃圾桶信息查看模式
        elif self.enable_bin_info:
            # 确保垃圾桶信息实例已初始化
            if not self.bin_info_instance:
                self.bin_info_instance = TrashBinInfo(self.points_gdf)
            
            # 查找最近的垃圾桶
            result = self.bin_info_instance.find_nearest_bin(click_point, max_distance=0.0005)
            if result is None:
                print("附近没有垃圾桶")
                return
                
            bin_id, bin_info = result
            self.selected_bin = bin_info
            
            # 显示垃圾桶信息
            info_text = self.bin_info_instance.show_bin_info(bin_info)
            
            # 创建一个简单的信息窗口
            msg_box = QMessageBox()
            msg_box.setWindowTitle("垃圾桶信息")
            msg_box.setText(info_text)
            msg_box.exec_()
            
            # 重新显示地图，高亮选中的垃圾桶
            self.displayMap()
    
    def find_nearest_bin(self, click_point, max_distance=0.0005):
        """查找离点击位置最近的垃圾桶
        
        Args:
            click_point: 点击位置的Point对象
            max_distance: 最大搜索距离
            
        Returns:
            bin_id 或 None
        """
        if self.points_gdf is None:
            return None
            
        min_distance = float('inf')
        nearest_bin_id = None
        
        for idx, bin_point in self.points_gdf.iterrows():
            bin_geom = bin_point.geometry
            
            # 计算点到垃圾桶的距离
            dist = bin_geom.distance(click_point)
            
            if dist < min_distance and dist < max_distance:
                min_distance = dist
                nearest_bin_id = idx
        
        return nearest_bin_id

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 停止所有动画
        if self.animation_running:
            self.stop_animations()
        
        # 接受关闭事件
        event.accept()

    def clear_display(self):
        """清除地图上的所有绘制内容"""
        # 停止动画
        if self.animation_running:
            self.stop_animations()
        
        # 停止行人动画
        if self.pedestrian_animation_running:
            self.stop_pedestrian_animation()
            
        # 清除导航相关的路径
        self.selected_path = None
        self.click_point = None
        self.click_to_road_path = None
        self.road_to_bin_path = None
        self.nearest_road_point = None
        self.nearest_bin_point = None
        self.selected_trash_type = None
        self.selected_trash_size = None
        
        # 禁用所有功能
        self.enable_navigation = False
        self.enable_bin_info = False
        self.enable_truck_navigation = False
        
        # 清除垃圾车导航相关的内容
        self.truck_routes = None
        
        # 清除垃圾桶选择
        self.selected_truck_bins = []
        self.selecting_bins = False
        
        # 移除规划按钮（如果存在）
        if self.plan_btn:
            self.plan_btn.setParent(None)
            self.plan_btn = None
        
        # 清除垃圾桶信息查看相关的内容
        self.selected_bin = None
        
        # 重新显示地图
        self.displayMap()
        
        # 取消所有功能选择状态
        for i in range(self.listWidget.count()):
            self.listWidget.item(i).setSelected(False)
            
        # 提示用户
        print("已清除所有绘图内容")

    def animate_pedestrian_route(self, speed=None):
        """创建并启动行人路径动画
        
        Args:
            speed: 动画速度（帧间隔，单位：毫秒），如果为None则使用默认速度
        """
        # 停止现有动画
        self.stop_pedestrian_animation()
        
        # 更新动画速度（如果指定）
        pedestrian_speed = 27  # 行人默认动画速度，比垃圾车快
        if speed is not None:
            pedestrian_speed = max(1, min(speed, 200))  # 限制在1-200ms之间
        
        # 创建新的动画
        if self.selected_path is not None and self.enable_navigation:
            anim = self.create_pedestrian_animation(self.selected_path, 'blue', pedestrian_speed)
            if anim:
                self.pedestrian_animation = anim
                self.pedestrian_animation_running = True
                print("行人动画已启动")
    
    def stop_pedestrian_animation(self):
        """停止行人动画"""
        try:
            # 停止动画
            if self.pedestrian_animation and hasattr(self.pedestrian_animation, 'event_source') and self.pedestrian_animation.event_source:
                self.pedestrian_animation.event_source.stop()
            
            # 从图中移除行人图标
            if hasattr(self, 'figure') and self.figure and hasattr(self.figure, 'axes') and self.figure.axes:
                ax = self.figure.axes[0]
                
                # 移除行人AnnotationBbox对象
                if self.pedestrian_artist and self.pedestrian_artist in ax.artists:
                    self.pedestrian_artist.remove()
            
            # 清空属性
            self.pedestrian_animation = None
            self.pedestrian_artist = None
            self.pedestrian_animation_running = False
            
            # 刷新画布
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.draw()
        except Exception as e:
            print(f"停止行人动画时发生错误: {e}")
            # 如果出错，尝试重置状态
            self.pedestrian_animation = None
            self.pedestrian_artist = None
            self.pedestrian_animation_running = False

    def create_pedestrian_animation(self, path, color, speed):
        """为行人创建动画
        
        Args:
            path: 行人路径数据（LineString）
            color: 路径颜色
            speed: 动画速度（帧间隔，单位：毫秒）
            
        Returns:
            animation对象
        """
        try:
            # 检查路径是否有效
            if not hasattr(path, 'xy'):
                print("行人路径无效")
                return None
            
            # 获取路径点
            x, y = path.xy
            all_points = np.array(list(zip(x, y)))
            
            if len(all_points) < 2:
                print("行人路径点不足")
                return None
            
            # 计算路径点之间的累积距离
            distances = [0]
            for i in range(1, len(all_points)):
                prev_point = all_points[i-1]
                curr_point = all_points[i]
                dist = np.sqrt((curr_point[0] - prev_point[0])**2 + (curr_point[1] - prev_point[1])**2)
                distances.append(distances[-1] + dist)
            
            total_distance = distances[-1]
            if total_distance <= 0:
                print("行人路径长度为0")
                return None
            
            # 创建行人图标
            pedestrian_icon = self.bin_icons['行人']
            if pedestrian_icon is None:
                print("行人图标加载失败")
                return None
            
            # 行人图标缩放比例
            zoom = self.base_icon_sizes['行人'] * self.icon_scale_factor
            imagebox = OffsetImage(pedestrian_icon, zoom=zoom)
            
            # 创建AnnotationBbox
            pedestrian_artist = AnnotationBbox(
                imagebox, 
                (all_points[0][0], all_points[0][1]),  # 起始位置
                xycoords='data',
                boxcoords='data',
                frameon=False,
                pad=0.0,
                zorder=15  # 确保行人显示在最上层
            )
            
            # 添加到图中
            self.figure.axes[0].add_artist(pedestrian_artist)
            self.pedestrian_artist = pedestrian_artist
            
            # 确定帧数（根据路径长度和复杂度自动调整）
            num_frames = min(200, max(100, int(len(all_points) * 2)))
            
            # 定义动画更新函数
            def update(frame):
                try:
                    # 计算当前位置
                    if frame == 0:
                        pos = all_points[0]
                    else:
                        # 计算目标距离
                        target_distance = frame / (num_frames - 1) * total_distance
                        
                        # 找到最近的路径段
                        idx = np.searchsorted(distances, target_distance) - 1
                        idx = max(0, min(idx, len(all_points) - 2))  # 确保索引有效
                        
                        # 计算插值点
                        p1 = all_points[idx]
                        p2 = all_points[idx + 1]
                        segment_length = distances[idx + 1] - distances[idx]
                        
                        if segment_length > 0:
                            alpha = (target_distance - distances[idx]) / segment_length
                        else:
                            alpha = 0
                        
                        # 线性插值计算当前位置
                        pos = p1 + alpha * (p2 - p1)
                    
                    # 更新行人位置
                    pedestrian_artist.xybox = pos
                    
                    return [pedestrian_artist]
                except Exception as e:
                    print(f"行人动画更新错误: {e}")
                    return []
            
            # 创建动画
            anim = animation.FuncAnimation(
                self.figure, 
                update, 
                frames=num_frames,
                interval=speed,
                blit=True,
                repeat=True
            )
            
            # 刷新画布
            self.canvas.draw()
            
            return anim
        except Exception as e:
            print(f"创建行人动画错误: {e}")
            return None

def readSHP():
    # 加载点矢量文件（垃圾桶）
    point_file_path = './data/垃圾桶.shp'
    points_gdf = gpd.read_file(point_file_path)
    
    # 打印字段信息
    print("垃圾桶.shp 字段列表:", points_gdf.columns.tolist())
    print("垃圾桶.shp 前3行数据:")
    print(points_gdf.head(3))
    
    # 加载线矢量文件（道路）
    line_file_path = './data/R.shp'
    roads_gdf = gpd.read_file(line_file_path)
    
    # 打印道路字段信息
    print("R.shp 字段列表:", roads_gdf.columns.tolist())
    print("R.shp 前3行数据:")
    print(roads_gdf.head(3))
    
    return points_gdf, roads_gdf

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MyMainForm()
    myWin.show()
    sys.exit(app.exec_())
