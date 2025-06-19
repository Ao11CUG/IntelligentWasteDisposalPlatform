from ui.界面 import Ui_MainWindow
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QColor, QIcon
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
from flask import Flask, send_from_directory
import threading
import webbrowser
import json
import base64
import random

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

        self.setWindowIcon(QIcon('./data/icon.png'))

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

        # 新地图数据
        self.buildings_gdf = None  # 建筑物数据GeoDataFrame
        self.greenland_gdf = None  # 绿地数据GeoDataFrame
        self.ground_gdf = None  # 操场数据GeoDataFrame
        self.new_road_gdf = None  # 新道路数据GeoDataFrame
        self.outroad_gdf = None  # 外围道路数据GeoDataFrame

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

        # 人流量动画控制
        self.enable_pedestrian_flow = True  # 是否启用人流量动画

        # 图标相关
        self.icon_scale_factor = 3.0  # 图标缩放系数 - 从2.5增加到3.0，使图标在更大的地图上显示合适
        self.base_icon_sizes = {
            '垃圾站': 0.08,  # 用于设置图标的基础大小
            '大垃圾桶': 0.05,  # 用于设置图标的基础大小
            '小垃圾桶': 0.04,  # 用于设置图标的基础大小
            '垃圾车': 0.04,  # 用于设置图标的基础大小
            '行人': 0.05  # 用于设置图标的基础大小
        }
        self.bin_icons = {
            '垃圾站': self.load_icon('垃圾站.png'),
            '大垃圾桶': self.load_icon('大垃圾桶.png'),
            '小垃圾桶': self.load_icon('小垃圾桶.png'),
            '垃圾车': self.load_icon('垃圾车.png'),
            '行人': self.load_icon('行人.png')
        }

        # 加载SHP数据
        self.points_gdf, self.roads_gdf, self.buildings_gdf, self.greenland_gdf, self.ground_gdf, self.new_road_gdf, self.outroad_gdf = readSHP()

        # 构建道路网络
        self.build_road_network()

        # 初始化导航类
        self.navigator = None

        # 设置地图显示区域
        self.setupMapCanvas()

        # 显示地图
        self.displayMap()
        # 兼容UI文件中按钮命名，适配btn_close/close_btn/closeButton
        if hasattr(self, 'close_btn'):
            close_btn = self.close_btn
        elif hasattr(self, 'btn_close'):
            close_btn = self.btn_close
        elif hasattr(self, 'closeButton'):
            close_btn = self.closeButton
        else:
            close_btn = None

        # 如果有其它按钮（如minimizeButton等），隐藏它们
        if hasattr(self, 'minimizeButton'):
            self.minimizeButton.hide()
        if hasattr(self, 'maximizeButton'):
            self.maximizeButton.hide()
        if hasattr(self, 'toggle_btn'):
            self.toggle_btn.hide()  # 只用main.py的btn_toggle

        # 保证toggle按钮和minimize按钮只创建一次
        if close_btn:
            # toggle按钮
            if not hasattr(self, 'btn_toggle'):
                self.btn_toggle = QtWidgets.QPushButton("□", self)
                self.btn_toggle.setFixedSize(close_btn.width(), close_btn.height())
                # 设置样式
                self.btn_toggle.setStyleSheet("""
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
                self.btn_toggle.setToolTip("窗口化/全屏化")
                self.btn_toggle.clicked.connect(self.toggleMaximized)
                self.btn_toggle.raise_()
            # minimize按钮
            if not hasattr(self, 'btn_minimize'):
                self.btn_minimize = QtWidgets.QPushButton("−", self)
                self.btn_minimize.setFixedSize(close_btn.width(), close_btn.height())
                # 设置样式
                self.btn_minimize.setStyleSheet("""
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
                self.btn_minimize.setToolTip("最小化")
                self.btn_minimize.clicked.connect(self.showMinimized)
                self.btn_minimize.raise_()
        # 按钮自适应窗口大小
        self._update_close_and_toggle_btn_pos()
        # 添加界面淡入动画
        self._fade_anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(400)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.setWindowOpacity(0.0)
        self._fade_anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_close_and_toggle_btn_pos()

        # 添加重绘地图的逻辑，使用防抖机制
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        else:
            self._resize_timer = QtCore.QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self.displayMap)

        # 设置300ms的防抖延迟
        self._resize_timer.start(300)

    def _update_close_and_toggle_btn_pos(self):
        # 让关闭按钮、toggle按钮、minimize按钮随窗口缩放自适应
        if hasattr(self, 'close_btn'):
            close_btn = self.close_btn
        elif hasattr(self, 'btn_close'):
            close_btn = self.btn_close
        elif hasattr(self, 'closeButton'):
            close_btn = self.closeButton
        else:
            close_btn = None

        # 关闭按钮自适应
        if close_btn:
            btn_size = max(30, int(self.width() * 0.035))
            close_btn.setFixedSize(btn_size, btn_size)
            margin_top = 18
            margin_right = 18

            # 如果close_btn没有文本，设置为"✕"
            if not close_btn.text():
                close_btn.setText("✕")
                close_btn.setStyleSheet("""
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

            close_btn.move(self.width() - btn_size - margin_right, margin_top)

        # toggle按钮自适应
        if close_btn and hasattr(self, 'btn_toggle'):
            self.btn_toggle.setFixedSize(close_btn.width(), close_btn.height())
            self.btn_toggle.move(close_btn.x() - close_btn.width() - 10, close_btn.y())

        # minimize按钮自适应
        if close_btn and hasattr(self, 'btn_minimize'):
            self.btn_minimize.setFixedSize(close_btn.width(), close_btn.height())
            self.btn_minimize.move(self.btn_toggle.x() - close_btn.width() - 10, close_btn.y())

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
        # 创建Figure对象 - 进一步增加图形大小
        self.figure = Figure(figsize=(14, 11), dpi=100)  # 从(12,9)改为(14,11)，进一步增大地图显示区域
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent")  # Qt层面canvas背景透明
        # 将canvas添加到widget中
        layout = QtWidgets.QVBoxLayout(self.widget)
        layout.setContentsMargins(20, 0, 0, 0)  # 左边距由0改为20
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

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 停止所有动画
        if self.animation_running:
            self.stop_animations()
        # 添加界面淡出动画
        fade = QtCore.QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(400)
        fade.setStartValue(self.windowOpacity())
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.InOutQuad)
        fade.finished.connect(self._final_close)
        fade.start()
        self._fade_anim = fade
        event.ignore()

    def displayMap(self):
        # 清除之前的图形
        self.figure.clear()

        # 创建子图
        ax = self.figure.add_subplot(111)
        # 设置背景为透明
        ax.set_facecolor((1, 1, 1, 0))  # 轴背景透明
        self.figure.patch.set_alpha(0)  # 整个figure背景透明

        # 绘制新的地图数据
        # 1. 绘制外围道路 - 使用灰色
        if hasattr(self, 'outroad_gdf') and self.outroad_gdf is not None:
            self.outroad_gdf.plot(ax=ax, color="grey", linewidth=3, zorder=1)

        # 2. 绘制道路 - 使用浅灰色
        if hasattr(self, 'new_road_gdf') and self.new_road_gdf is not None:
            self.new_road_gdf.plot(ax=ax, color="#FFFFFF", linewidth=2, zorder=2)

        # 3. 绘制操场 - 使用更深的灰色
        if hasattr(self, 'ground_gdf') and self.ground_gdf is not None:
            self.ground_gdf.plot(ax=ax, color="#736161", alpha=0.8, zorder=3)  # 从#B0B0B0改为#909090，更深的灰色

        # 4. 绘制绿地 - 使用草地的样式（绿色+纹理）
        if hasattr(self, 'greenland_gdf') and self.greenland_gdf is not None:
            self.greenland_gdf.plot(ax=ax, color='#8FBC8F', alpha=0.7, zorder=3)
            # 添加一些随机点模拟草地纹理
            for _, geom in self.greenland_gdf.geometry.items():
                if not geom.is_empty:
                    # 获取多边形的边界框
                    minx, miny, maxx, maxy = geom.bounds
                    # 生成随机点
                    num_points = int(geom.area * 10000)  # 根据面积确定点的数量
                    num_points = min(num_points, 100)  # 限制最大点数

                    for _ in range(num_points):
                        # 生成边界框内的随机点
                        p_x = np.random.uniform(minx, maxx)
                        p_y = np.random.uniform(miny, maxy)
                        point = Point(p_x, p_y)

                        # 检查点是否在多边形内
                        if point.within(geom):
                            ax.plot(p_x, p_y, 'o', color='#006400', markersize=0.3, alpha=0.5, zorder=3)

        # 5. 绘制建筑物 - 根据type字段区分建筑物和水域
        if hasattr(self, 'buildings_gdf') and self.buildings_gdf is not None:
            # 创建两个子集：建筑物和水域
            buildings = self.buildings_gdf[self.buildings_gdf['type'] == 'building']
            water = self.buildings_gdf[self.buildings_gdf['type'] == 'water']

            # 绘制建筑物 - 使用深灰色（原来是暗红色）
            if not buildings.empty:
                buildings.plot(ax=ax, color='#404040', edgecolor='#505050', linewidth=0.5, alpha=0.9, zorder=4)

            # 绘制水域 - 使用蓝色和纹理
            if not water.empty:
                water.plot(ax=ax, color='#4F94CD', alpha=0.6, zorder=3)
                # 添加一些线条模拟水纹
                for _, geom in water.geometry.items():
                    if not geom.is_empty:
                        # 获取多边形的边界框
                        minx, miny, maxx, maxy = geom.bounds
                        # 计算水平线的数量（基于高度）
                        height = maxy - miny
                        num_lines = int(height * 500)
                        num_lines = min(num_lines, 20)  # 增加最大线条数

                        for i in range(num_lines):
                            # 在多边形内部画水平线，使用正弦波形以模拟波纹
                            y_base = miny + (i + 0.5) * (height / (num_lines + 1))

                            # 创建多段波浪线
                            wave_points = []
                            segments = 50  # 波浪线的段数

                            for s in range(segments + 1):
                                x = minx + s * (maxx - minx) / segments
                                # 使用正弦函数创建波浪效果，幅度很小
                                wave_height = 0.00002 * np.sin(s * np.pi / 2.5)
                                y = y_base + wave_height
                                wave_points.append((x, y))

                            wave_line = LineString(wave_points)
                            clipped_line = wave_line.intersection(geom)

                            if not clipped_line.is_empty:
                                if isinstance(clipped_line, LineString):
                                    x, y = clipped_line.xy
                                    ax.plot(x, y, color='#B0E0E6', linewidth=0.5, alpha=0.4, zorder=3)
                                elif isinstance(clipped_line, MultiLineString):
                                    for line_part in clipped_line.geoms:
                                        x, y = line_part.xy
                                        ax.plot(x, y, color='#B0E0E6', linewidth=0.5, alpha=0.4, zorder=3)

        # 绘制原始道路数据但设置为不可见（透明度为0），以保持导航和路径规划功能
        if self.roads_gdf is not None:
            self.roads_gdf.plot(ax=ax, color='black', linewidth=1, alpha=0, zorder=1)

        # 绘制垃圾桶和垃圾站图标（始终显示）
        if self.points_gdf is not None:
            for idx, bin_point in self.points_gdf.iterrows():
                # 判断是否需要高亮显示（被选中的垃圾桶）
                highlight = (self.selecting_bins and idx in self.selected_truck_bins)
                # 设置合适的zorder（图层顺序），高亮显示的在上层
                zorder = 15 if highlight else 12

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
                                zorder=16)

        # 下面是功能性元素，始终显示
        # 导航模式：绘制选择的路径（如果有）
        if self.selected_path is not None and self.enable_navigation:
            # 确保路径是有效的LineString
            if hasattr(self.selected_path, 'xy'):
                x, y = self.selected_path.xy
                ax.plot(x, y, color='blue', linewidth=3, linestyle='-', zorder=10)

        # 垃圾车导航模式：绘制多条路径
        if self.truck_routes is not None and self.enable_truck_navigation:
            # 这里不再停止人流量动画，让人流量和垃圾车同时显示
            # 如果是单车模式
            if not isinstance(self.truck_routes, list):
                route = self.truck_routes
                # 绘制路径
                for path in route['route_paths']:
                    if hasattr(path, 'xy'):
                        x, y = path.xy
                        ax.plot(x, y, color='blue', linewidth=3, linestyle='-', zorder=10)

                # 绘制点
                for j, point in enumerate(route['route_points']):
                    if j == 0 or j == len(route['route_points']) - 1:
                        # 起点和终点用星星标记，不使用垃圾车图标
                        ax.plot(point.x, point.y, marker='*', markersize=15,
                                color='blue', markeredgecolor='black', zorder=11)

                        # 添加垃圾车编号标签
                        ax.annotate(f"车1",
                                    xy=(point.x, point.y),
                                    xytext=(10, 10),
                                    textcoords="offset points",
                                    bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
                                    zorder=12)
                    else:
                        # 中间点用圆形标记
                        ax.plot(point.x, point.y, marker='o', markersize=10,
                                color='blue', markeredgecolor='black', zorder=11)
            else:
                # 多车模式
                for i, route in enumerate(self.truck_routes):
                    # 获取颜色
                    color = self.route_colors[i % len(self.route_colors)]

                    # 绘制路径
                    for path in route['route_paths']:
                        if hasattr(path, 'xy'):
                            x, y = path.xy
                            ax.plot(x, y, color=color, linewidth=3, linestyle='-', zorder=10)

                    # 绘制点
                    for j, point in enumerate(route['route_points']):
                        if j == 0 or j == len(route['route_points']) - 1:
                            # 起点和终点用星星标记，不使用垃圾车图标
                            ax.plot(point.x, point.y, marker='*', markersize=15,
                                    color=color, markeredgecolor='black', zorder=11)

                            # 添加垃圾车编号标签
                            ax.annotate(f"车{route['truck_id']}",
                                        xy=(point.x, point.y),
                                        xytext=(10, 10),
                                        textcoords="offset points",
                                        bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
                                        zorder=12)
                        else:
                            # 中间点用圆形标记
                            ax.plot(point.x, point.y, marker='o', markersize=10,
                                    color=color, markeredgecolor='black', zorder=11)

        # 单独绘制点击点（如果有）
        if self.click_point is not None:
            ax.plot(self.click_point.x, self.click_point.y, 'mo', markersize=10, zorder=15)

        # 绘制最近道路点（如果有）
        if self.nearest_road_point is not None and self.enable_navigation:
            ax.plot(self.nearest_road_point.x, self.nearest_road_point.y, 'go', markersize=8, zorder=14)

        # 绘制最近垃圾桶点（如果有）
        if self.nearest_bin_point is not None and self.enable_navigation:
            ax.plot(self.nearest_bin_point.x, self.nearest_bin_point.y, 'yo', markersize=12, zorder=14)

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
                                    zorder=15)
                ax.add_artist(ab)
            else:
                ax.plot(bin_geom.x, bin_geom.y, 'bo', markersize=15, zorder=15)

            # 添加垃圾桶信息标签
            label = f"{bin_type_str}\n{bin_size}"
            ax.annotate(label,
                        xy=(bin_geom.x, bin_geom.y),
                        xytext=(10, 10),
                        textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
                        zorder=16)

        # 如果正在选择垃圾桶模式，添加规划按钮
        if self.selecting_bins:
            # 添加"开始规划"按钮
            self.add_plan_button()

        # 隐藏坐标轴
        ax.set_axis_off()

        # 调整地图视图，确保所有内容都能显示出来
        # 确定显示范围 - 优先使用新地图数据的范围
        if hasattr(self, 'new_road_gdf') and self.new_road_gdf is not None and not self.new_road_gdf.empty:
            bounds = self.new_road_gdf.total_bounds
            # 扩大边界以确保所有内容都能显示
            x_margin = (bounds[2] - bounds[0]) * 0.12  # 水平方向增加12%的边距
            y_margin = (bounds[3] - bounds[1]) * 0.12  # 垂直方向增加12%的边距

            # 设置地图显示范围
            ax.set_xlim([bounds[0] - x_margin, bounds[2] + x_margin])
            ax.set_ylim([bounds[1] - y_margin, bounds[3] + y_margin])

        # 使用tight_layout，减少空白边距
        self.figure.tight_layout(pad=0)

        # 刷新canvas
        self.canvas.draw()

        # 在地图生成时立即模拟道路人流量动画，只有当启用人流量动画时才显示
        if self.enable_pedestrian_flow:
            self.animate_pedestrian_flow(ax)

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

            # 禁用人流量动画
            self.enable_pedestrian_flow = False

            # 设置按钮为选中状态
            self.listWidget.item(2).setSelected(True)
            # 创建并显示提示消息弹窗
            msg_box = QMessageBox()
            msg_box.setWindowTitle("操作提示")
            msg_box.setText("垃圾桶信息查看功能已启用\n请点击地图上的垃圾桶查看详细信息")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.exec_()
            print("垃圾桶信息查看功能已启用，请点击地图上的垃圾桶查看信息")
        # 如果点击的是"网页端"
        elif item_text == "网页端":
            html_path = os.path.abspath("web/垃圾桶.html")
            html_dir = os.path.dirname(html_path)
            html_file = os.path.basename(html_path)
            # Cesium静态资源目录（如Cesium-1.128）应与html同级
            cesium_dir = os.path.join(html_dir, "Cesium-1.128")

            def run_flask():
                flask_app = Flask(__name__, static_folder=html_dir)

                @flask_app.route('/')
                def index():
                    return send_from_directory(html_dir, html_file)

                # 静态资源路由
                @flask_app.route('/Cesium-1.128/<path:filename>')
                def cesium_static(filename):
                    return send_from_directory(cesium_dir, filename)

                # 兼容favicon
                @flask_app.route('/favicon.ico')
                def favicon():
                    return send_from_directory(html_dir, 'favicon.ico') if os.path.exists(
                        os.path.join(html_dir, 'favicon.ico')) else ('', 204)

                # 新增：垃圾分类最新结果接口
                @flask_app.route('/api/classify/latest')
                def classify_latest():
                    json_path = os.path.join(os.path.dirname(__file__), 'latest_classify.json')
                    img_path = os.path.join(os.path.dirname(__file__), 'latest_classify.jpg')
                    if not os.path.exists(json_path) or not os.path.exists(img_path):
                        return {"result": "", "image": ""}
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        with open(img_path, 'rb') as f:
                            img_b64 = base64.b64encode(f.read()).decode('utf-8')
                        return {
                            "result": data.get("result", ""),
                            "image": "data:image/jpeg;base64," + img_b64
                        }
                    except Exception as e:
                        return {"result": "读取失败", "image": ""}

                # web目录下所有静态资源（如js/css/image等）
                @flask_app.route('/web/<path:filename>')
                def web_static(filename):
                    return send_from_directory(html_dir, filename)

                # web下js、image、css等静态资源支持
                @flask_app.route('/js/<path:filename>')
                def js_static(filename):
                    return send_from_directory(os.path.join(html_dir, 'js'), filename)

                @flask_app.route('/image/<path:filename>')
                def image_static(filename):
                    return send_from_directory(os.path.join(html_dir, 'image'), filename)

                @flask_app.route('/data/<path:filename>')
                def css_static(filename):
                    return send_from_directory(os.path.join(html_dir, 'data'), filename)

                flask_app.run(port=5678, debug=False, use_reloader=False)

            if os.path.exists(html_path):
                if not hasattr(self, "_flask_thread") or not self._flask_thread.is_alive():
                    self._flask_thread = threading.Thread(target=run_flask, daemon=True)
                    self._flask_thread.start()
                webbrowser.open('http://127.0.0.1:5678/')
            else:
                QMessageBox.warning(self, "提示", f"未找到本地HTML文件: {html_path}")
        # 如果点击的是"垃圾车最优遍历"，启用垃圾车导航功能
        elif item_text == "垃圾车最优遍历":
            # 初始化垃圾车导航类
            if not self.truck_navigator:
                self.truck_navigator = GarbageTruckNavigation(self.roads_gdf, self.points_gdf)

            # 禁用人流量动画
            self.enable_pedestrian_flow = False

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
        # 不再停止人流量动画，允许垃圾车和人流量同时显示
        self.stop_pedestrian_animation()

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
                    prev_point = all_points[i - 1]
                    curr_point = all_points[i]
                    dist = np.sqrt((curr_point[0] - prev_point[0]) ** 2 + (curr_point[1] - prev_point[1]) ** 2)
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
                prev_point = all_points[i - 1]
                curr_point = all_points[i]
                dist = np.sqrt((curr_point[0] - prev_point[0]) ** 2 + (curr_point[1] - prev_point[1]) ** 2)
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
            if self.pedestrian_animation and hasattr(self.pedestrian_animation,
                                                     'event_source') and self.pedestrian_animation.event_source:
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

        print("道路网络构建完成，节点数:", len(self.road_network.nodes), "边数:", len(self.road_network.edges))

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
                # 停止模拟人流量动画和行人点
                self.stop_pedestrian_flow_animation()
                self.stop_pedestrian_animation()
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

        # 停止人流量动画
        self.stop_pedestrian_flow_animation()

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

        # 重新启用人流量动画
        self.enable_pedestrian_flow = True

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
            if self.pedestrian_animation and hasattr(self.pedestrian_animation,
                                                     'event_source') and self.pedestrian_animation.event_source:
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
                prev_point = all_points[i - 1]
                curr_point = all_points[i]
                dist = np.sqrt((curr_point[0] - prev_point[0]) ** 2 + (curr_point[1] - prev_point[1]) ** 2)
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

    def animate_pedestrian_flow(self, ax):
        """
        在道路矢量上根据人流量随机生成点，并让这些点在道路上做动画移动
        """
        # 检查必要的对象是否存在
        if not hasattr(self, "roads_gdf") or self.roads_gdf is None:
            return

        # 检查figure和axes是否有效
        if not hasattr(self, "figure") or self.figure is None:
            print("警告: figure对象不存在，无法创建人流量动画")
            return

        if not hasattr(self.figure, "axes") or len(self.figure.axes) == 0:
            print("警告: axes对象不存在，无法创建人流量动画")
            return

        if ax is None:
            print("警告: 传入的ax对象为None，无法创建人流量动画")
            return

        # 全图行人总数限制
        max_total_people = 80
        pedestrian_color = "#3abcbc"
        pedestrian_size = 7

        self.road_pedestrian_artists = []
        self.road_pedestrian_data = []

        # 只在主显示时生成一次人流点
        if not hasattr(self, "_road_pedestrian_cache") or not self._road_pedestrian_cache:
            self._road_pedestrian_cache = []
            road_geoms = [road.geometry for idx, road in self.roads_gdf.iterrows() if
                          isinstance(road.geometry, LineString)]
            # 建立道路连接关系（端点相同即为相连）
            road_endpoints = []
            for geom in road_geoms:
                coords = list(geom.coords)
                road_endpoints.append((coords[0], coords[-1]))
            # 记录每条道路的相连道路索引
            road_connections = {}
            for i, (start1, end1) in enumerate(road_endpoints):
                connections = []
                for j, (start2, end2) in enumerate(road_endpoints):
                    if i == j:
                        continue
                    if start1 == start2 or start1 == end2 or end1 == start2 or end1 == end2:
                        connections.append(j)
                road_connections[i] = connections
            # 保存到self，供update闭包使用，避免闭包变量问题
            self._road_connections = road_connections
            self._road_geoms = road_geoms
            total_people = 0
            while total_people < max_total_people and road_geoms:
                road_idx = random.randrange(len(road_geoms))
                random_geom = road_geoms[road_idx]
                start_pos = random.uniform(0, 1)
                direction = random.choice([1, -1])
                speed = random.uniform(0.005, 0.03)
                self._road_pedestrian_cache.append({
                    "geom": random_geom,
                    "road_idx": road_idx,
                    "pos": start_pos,
                    "direction": direction,
                    "speed": speed,
                    "color": pedestrian_color,
                    "size": pedestrian_size
                })
                total_people += 1

        # 绘制初始点（不透明 alpha=1.0）
        try:
            for ped in self._road_pedestrian_cache:
                point = ped["geom"].interpolate(ped["pos"], normalized=True)
                artist, = ax.plot([point.x], [point.y], 'o', color=ped["color"], markersize=ped["size"], alpha=1.0,
                                  zorder=20)
                self.road_pedestrian_artists.append(artist)
                self.road_pedestrian_data.append(ped)
        except Exception as e:
            print(f"创建人流量点时出错: {e}")
            return

        # 检查是否成功创建了人流量点
        if not self.road_pedestrian_artists:
            print("警告: 未能创建人流量点，无法创建动画")
            return

        # self.add_stop_pedestrian_flow_btn(ax)

        def update(frame):
            try:
                # 使用self._road_connections和self._road_geoms，避免闭包变量问题
                road_connections = getattr(self, "_road_connections", {})
                road_geoms = getattr(self, "_road_geoms", [])

                # 检查必要的数据是否存在
                if not hasattr(self, "road_pedestrian_data") or not self.road_pedestrian_data:
                    return []

                if not hasattr(self, "road_pedestrian_artists") or not self.road_pedestrian_artists:
                    return []

                for i, ped in enumerate(self.road_pedestrian_data):
                    if i >= len(self.road_pedestrian_artists):
                        continue  # 防止索引越界

                    ped["pos"] += ped["direction"] * ped["speed"]
                    # 到达道路端点时，尝试切换到相连道路
                    if ped["pos"] > 1 or ped["pos"] < 0:
                        cur_idx = ped.get("road_idx", None)
                        if cur_idx is not None and "road_idx" in ped:
                            connections = road_connections.get(cur_idx, [])
                            if connections:
                                # 随机选择一条相连道路
                                next_idx = random.choice(connections)
                                ped["geom"] = road_geoms[next_idx]
                                ped["road_idx"] = next_idx
                                # 随机选择方向和端点
                                if random.random() < 0.5:
                                    ped["pos"] = 0
                                    ped["direction"] = 1
                                else:
                                    ped["pos"] = 1
                                    ped["direction"] = -1
                            else:
                                # 没有相连道路则原路返回
                                if ped["pos"] > 1:
                                    ped["pos"] = 1
                                    ped["direction"] = -1
                                else:
                                    ped["pos"] = 0
                                    ped["direction"] = 1
                        else:
                            # 没有road_idx信息则原路返回
                            if ped["pos"] > 1:
                                ped["pos"] = 1
                                ped["direction"] = -1
                            else:
                                ped["pos"] = 0
                                ped["direction"] = 1

                    # 安全地更新点位置
                    try:
                        point = ped["geom"].interpolate(ped["pos"], normalized=True)
                        self.road_pedestrian_artists[i].set_data([point.x], [point.y])
                    except Exception as e:
                        print(f"更新人流量点位置时出错: {e}")
                        continue

                return self.road_pedestrian_artists
            except Exception as e:
                print(f"人流量动画更新函数出错: {e}")
                return []

        # 停止现有动画
        if hasattr(self, "road_pedestrian_anim") and self.road_pedestrian_anim:
            try:
                self.road_pedestrian_anim.event_source.stop()
            except Exception as e:
                print(f"停止现有人流量动画时出错: {e}")

        try:
            # 创建新动画
            self.road_pedestrian_anim = animation.FuncAnimation(
                self.figure,
                update,
                frames=200,
                interval=60,
                blit=True,
                repeat=True
            )

            # 刷新画布
            if hasattr(self, "canvas") and self.canvas:
                self.canvas.draw()
        except Exception as e:
            print(f"创建人流量动画时出错: {e}")
            self.road_pedestrian_anim = None

    def stop_pedestrian_flow_animation(self):
        """关闭人流量动画并隐藏按钮"""
        try:
            # 停止动画
            if hasattr(self, "road_pedestrian_anim") and self.road_pedestrian_anim:
                try:
                    self.road_pedestrian_anim.event_source.stop()
                except Exception as e:
                    print(f"停止人流量动画时出错: {e}")
                finally:
                    self.road_pedestrian_anim = None

            # 清除艺术家对象
            if hasattr(self, "road_pedestrian_artists") and self.road_pedestrian_artists:
                for artist in self.road_pedestrian_artists:
                    try:
                        if artist in self.figure.axes[0].artists or artist in self.figure.axes[0].lines:
                            artist.remove()
                    except Exception as e:
                        print(f"移除人流量点时出错: {e}")
                self.road_pedestrian_artists = []

            # 清除数据
            if hasattr(self, "road_pedestrian_data"):
                self.road_pedestrian_data = []

            # 隐藏按钮
            if hasattr(self, "_stop_pedestrian_flow_btn") and self._stop_pedestrian_flow_btn:
                self._stop_pedestrian_flow_btn.hide()

            # 刷新canvas
            if hasattr(self, "canvas") and self.canvas:
                self.canvas.draw()
        except Exception as e:
            print(f"停止人流量动画过程中出错: {e}")
            # 重置关键状态，确保不会影响后续操作
            self.road_pedestrian_anim = None
            self.road_pedestrian_artists = []
            self.road_pedestrian_data = []


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

    # 加载新的地图数据
    # 建筑物
    building_file_path = './data/map/ex_building.shp'
    buildings_gdf = gpd.read_file(building_file_path)
    print("ex_building.shp 字段列表:", buildings_gdf.columns.tolist())

    # 绿地
    greenland_file_path = './data/map/ex_greenland.shp'
    greenland_gdf = gpd.read_file(greenland_file_path)
    print("ex_greenland.shp 字段列表:", greenland_gdf.columns.tolist())

    # 操场
    ground_file_path = './data/map/ex_ground.shp'

    ground_gdf = gpd.read_file(ground_file_path)
    print("ex_ground.shp 字段列表:", ground_gdf.columns.tolist())

    # 道路
    new_road_file_path = './data/map/ex_road.shp'
    new_road_gdf = gpd.read_file(new_road_file_path)
    print("ex_road.shp 字段列表:", new_road_gdf.columns.tolist())

    # 外围道路
    outroad_file_path = './data/map/outroad1.shp'
    outroad_gdf = gpd.read_file(outroad_file_path)
    print("outroad1.shp 字段列表:", outroad_gdf.columns.tolist())

    return points_gdf, roads_gdf, buildings_gdf, greenland_gdf, ground_gdf, new_road_gdf, outroad_gdf


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MyMainForm()
    myWin.show()
    sys.exit(app.exec_())
