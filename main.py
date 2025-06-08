from ui.界面 import Ui_MainWindow
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDialogButtonBox, QMessageBox
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

# 导入自定义模块
from trash_navigation import TrashSelectionDialog, NavToNearestBin
from trash_bin_info import TrashBinInfo

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class MyMainForm(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.start_x = None
        self.start_y = None
        self.anim=None
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)  # 设置窗口标志：隐藏窗口边框

        # 连接列表项的点击信号
        self.listWidget.itemClicked.connect(self.on_item_clicked)
        
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
    
    def displayMap(self):
        # 清除之前的图形
        self.figure.clear()
        
        # 创建子图
        ax = self.figure.add_subplot(111)
        
        # 绘制路网
        if self.roads_gdf is not None:
            self.roads_gdf.plot(ax=ax, color='gray', linewidth=1)
        
        # 绘制点位
        if self.points_gdf is not None:
            self.points_gdf.plot(ax=ax, color='red', markersize=50, marker='o')
        
        # 导航模式：绘制选择的路径（如果有）
        if self.selected_path is not None and self.enable_navigation:
            # 确保路径是有效的LineString
            if hasattr(self.selected_path, 'xy'):
                x, y = self.selected_path.xy
                ax.plot(x, y, color='blue', linewidth=3, linestyle='-', zorder=3)
        
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
            ax.plot(bin_geom.x, bin_geom.y, 'bo', markersize=15, zorder=5)
            
            # 添加垃圾桶信息标签
            bin_type_str = '、'.join(self.selected_bin['type']) if self.selected_bin['type'] else '未知类型'
            bin_size = self.selected_bin['size']
            
            label = f"{bin_type_str}\n{bin_size}"
            ax.annotate(label, 
                       xy=(bin_geom.x, bin_geom.y),
                       xytext=(10, 10),
                       textcoords="offset points",
                       bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
                       zorder=6)
        
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
        
        # 如果点击的是"垃圾识别"，打开垃圾分类窗口
        if item_text == "垃圾分类识别":
            if not self.waste_classify_window:
                self.waste_classify_window = WasteClassifyWindow()
            self.waste_classify_window.show()
        # 如果点击的是"丢垃圾"，启用导航功能
        elif item_text == "丢垃圾指路":
            # 如果导航功能已启用，则关闭它
            if self.enable_navigation:
                self.disable_navigation()
                return
                
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
                
                # 禁用垃圾桶信息查看功能
                self.enable_bin_info = False
                
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
            
            # 切换垃圾桶信息查看功能状态
            self.enable_bin_info = not self.enable_bin_info
            
            # 禁用导航功能
            self.enable_navigation = False
            
            # 更新按钮文本
            if self.enable_bin_info:
                # 设置按钮为选中状态
                self.listWidget.item(2).setSelected(True)
                # 创建并显示提示消息弹窗
                msg_box = QMessageBox()
                msg_box.setWindowTitle("操作提示")
                msg_box.setText("垃圾桶信息查看功能已启用\n请点击地图上的垃圾桶查看详细信息")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.exec_()
                print("垃圾桶信息查看功能已启用，请点击地图上的垃圾桶查看信息")
            else:
                # 清除选中状态
                self.listWidget.item(2).setSelected(False)
                # 清除选中的垃圾桶
                self.selected_bin = None
                # 重新显示地图
                self.displayMap()
                print("垃圾桶信息查看功能已禁用")
                
    def disable_navigation(self):
        """关闭导航功能"""
        # 清除选中状态
        self.listWidget.item(0).setSelected(False)
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
        
        # 导航模式
        if self.enable_navigation:
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
    
    return points_gdf, roads_gdf

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MyMainForm()
    myWin.show()
    sys.exit(app.exec_())
