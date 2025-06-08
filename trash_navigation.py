from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDialogButtonBox, QWidget, QPushButton
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QColor
import networkx as nx
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
import matplotlib.pyplot as plt

class TrashSelectionDialog(QDialog):
    """垃圾类型和大小选择对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trash_type = None
        self.trash_size = None
        self.initUI()
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('丢垃圾指路')
        self.resize(550, 350)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: rgb(245, 245, 248);
                border-radius: 20px;
            }
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: rgb(80, 100, 100);
                padding: 5px;
            }
            QComboBox {
                border: 1px solid rgb(200, 200, 200);
                border-radius: 10px;
                padding: 10px;
                background-color: rgb(250, 250, 252);
                min-width: 220px;
                font-size: 20px;
                selection-background-color: rgb(90, 216, 212);
            }
            QComboBox:hover {
                border: 1px solid rgb(90, 216, 212);
                background-color: rgb(252, 252, 255);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
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
        """)
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(25)
        
        # 创建标题标签
        title_label = QLabel('请选择垃圾类型和大小')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 36px; font-weight: bold; margin-bottom: 20px; color: rgb(60, 90, 90);')
        layout.addWidget(title_label)
        
        # 创建垃圾类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel('垃圾类型:')
        self.type_combo = QComboBox()
        self.type_combo.addItems(['厨余垃圾', '可回收垃圾', '其他垃圾', '有害垃圾'])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # 创建垃圾大小选择
        size_layout = QHBoxLayout()
        size_label = QLabel('垃圾大小:')
        self.size_combo = QComboBox()
        self.size_combo.addItems(['小垃圾', '大垃圾'])
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo)
        layout.addLayout(size_layout)
        
        # 创建按钮
        button_box = QDialogButtonBox()
        ok_button = QPushButton('确定')
        cancel_button = QPushButton('取消')
        cancel_button.setStyleSheet("""
            background-color: rgb(210, 210, 215);
            color: rgb(40, 40, 40);
            font-weight: bold;
            border: 2px solid rgb(180, 180, 185);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        """)
        
        button_box.addButton(ok_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)

        tip_label = QLabel('[点击确定后，请在地图上点击选择起点]')
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet('font-size: 20px; color: rgb(100, 120, 120); margin-top: 20px;')
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)
        
        # 设置对话框布局
        self.setLayout(layout)
    
    def get_selection(self):
        """获取用户选择的垃圾类型和大小"""
        return self.type_combo.currentText(), self.size_combo.currentText()

class NavToNearestBin:
    """封装寻找最近垃圾桶的导航功能"""
    
    def __init__(self, roads_gdf, points_gdf, road_network):
        """初始化导航类
        
        Args:
            roads_gdf: 道路GeoDataFrame
            points_gdf: 垃圾桶点GeoDataFrame
            road_network: 道路网络图
        """
        self.roads_gdf = roads_gdf
        self.points_gdf = points_gdf
        self.road_network = road_network
    
    def find_nearest_road_point(self, click_point):
        """查找离点击位置最近的道路点"""
        if self.roads_gdf is None:
            return None
            
        min_distance = float('inf')
        nearest_point = None
        nearest_road_geom = None
        
        # 遍历每条道路
        for idx, road in self.roads_gdf.iterrows():
            geom = road.geometry
            
            # 计算点到线的最短距离
            dist = geom.distance(click_point)
            
            if dist < min_distance:
                min_distance = dist
                nearest_road_geom = geom
        
        if nearest_road_geom:
            # 使用nearest_points找到最近点
            nearest_point_on_line = nearest_points(click_point, nearest_road_geom)[1]
            return nearest_point_on_line
        
        return None
    
    def find_suitable_trash_bin(self, start_point, trash_type, trash_size):
        """查找适合特定垃圾类型和大小的最近垃圾桶
        
        Args:
            start_point: 起始点
            trash_type: 垃圾类型 (厨余垃圾/可回收垃圾/其他垃圾/有害垃圾)
            trash_size: 垃圾大小 (小垃圾/大垃圾)
            
        Returns:
            tuple: (bin_geom, bin_node) 或 None
        """
        if self.points_gdf is None or self.road_network is None:
            return None
            
        # 首先找到网络中最近的节点作为起点
        min_dist = float('inf')
        start_node = None
        
        for node in self.road_network.nodes():
            dist = Point(node).distance(Point(start_point.x, start_point.y))
            if dist < min_dist:
                min_dist = dist
                start_node = node
        
        if not start_node:
            return None
        
        # 找到合适的垃圾桶
        suitable_bins = []
        
        for idx, bin_point in self.points_gdf.iterrows():
            bin_geom = bin_point.geometry
            
            # 解析垃圾桶类型和大小
            remark = bin_point.get('Remark', '')
            name = bin_point.get('Name', '')
            
            # 判断垃圾桶是否适合当前垃圾类型
            bin_type = self._parse_remark(remark)
            bin_size = self._parse_name(name)
            
            # 检查垃圾桶是否适合所选垃圾类型
            is_suitable_type = False
            if trash_type == '厨余垃圾' and '厨余垃圾' in bin_type:
                is_suitable_type = True
            elif trash_type == '可回收垃圾' and '可回收垃圾' in bin_type:
                is_suitable_type = True
            elif trash_type == '其他垃圾' and '其他垃圾' in bin_type:
                is_suitable_type = True
            elif trash_type == '有害垃圾' and '有害垃圾' in bin_type:
                is_suitable_type = True
            elif '垃圾站' in bin_type:  # 垃圾站可以接收所有类型的垃圾
                is_suitable_type = True
                
            # 检查垃圾桶是否适合所选垃圾大小
            is_suitable_size = False
            if trash_size == '小垃圾':
                # 小垃圾可以放入任何大小的垃圾桶
                is_suitable_size = True
            elif trash_size == '大垃圾' and (bin_size == '大垃圾桶' or bin_size == '垃圾站'):
                # 大垃圾只能放入大垃圾桶或垃圾站
                is_suitable_size = True
                
            # 如果类型和大小都适合，则计算网络距离
            if is_suitable_type and is_suitable_size:
                # 找到网络中最近的节点
                min_node_dist = float('inf')
                closest_node = None
                
                for node in self.road_network.nodes():
                    dist = Point(node).distance(bin_geom)
                    if dist < min_node_dist:
                        min_node_dist = dist
                        closest_node = node
                
                if closest_node:
                    # 计算网络距离
                    try:
                        path_length = nx.shortest_path_length(
                            self.road_network, 
                            start_node, 
                            closest_node, 
                            weight='weight'
                        )
                        
                        suitable_bins.append((bin_geom, closest_node, path_length))
                    except nx.NetworkXNoPath:
                        # 如果没有路径，继续检查下一个垃圾桶
                        continue
        
        # 如果找到了合适的垃圾桶，返回距离最近的一个
        if suitable_bins:
            # 按照路径长度排序
            suitable_bins.sort(key=lambda x: x[2])
            return suitable_bins[0][0], suitable_bins[0][1]
        
        # 如果没有找到完全匹配的垃圾桶，退回到查找任何最近的垃圾桶
        print("未找到完全匹配的垃圾桶，将导航到最近的任意垃圾桶")
        return self.find_nearest_trash_bin(start_point)
    
    def _parse_remark(self, remark):
        """解析Remark字段，获取垃圾桶类型
        
        Args:
            remark: Remark字段值
            
        Returns:
            list: 垃圾桶类型列表
        """
        if not remark:
            return []
            
        # 如果是Dumpster，表示垃圾站
        if remark.lower() == 'dumpster':
            return ['垃圾站']
            
        # 解析垃圾桶类型
        bin_types = []
        
        # 查找类型代码
        if 'C' in remark:
            bin_types.append('厨余垃圾')
        if 'K' in remark:
            bin_types.append('可回收垃圾')
        if 'Q' in remark:
            bin_types.append('其他垃圾')
        if 'Y' in remark:
            bin_types.append('有害垃圾')
        
        return bin_types
    
    def _parse_name(self, name):
        """解析Name字段，获取垃圾桶大小
        
        Args:
            name: Name字段值
            
        Returns:
            str: 垃圾桶大小描述
        """
        if not name:
            return '未知大小'
            
        name_lower = name.lower()
        
        if name_lower.startswith('td'):
            return '垃圾站'
        elif name_lower.startswith('d'):
            return '大垃圾桶'
        elif name_lower.startswith('x'):
            return '小垃圾桶'
        else:
            return '未知大小'
    
    def find_nearest_trash_bin(self, start_point):
        """查找最近的垃圾桶"""
        if self.points_gdf is None or self.road_network is None:
            return None
            
        # 首先找到网络中最近的节点作为起点
        min_dist = float('inf')
        start_node = None
        
        for node in self.road_network.nodes():
            dist = Point(node).distance(Point(start_point.x, start_point.y))
            if dist < min_dist:
                min_dist = dist
                start_node = node
        
        if not start_node:
            return None
        
        # 找到最近的垃圾桶
        min_bin_dist = float('inf')
        nearest_bin = None
        nearest_bin_node = None
        
        for idx, bin_point in self.points_gdf.iterrows():
            bin_geom = bin_point.geometry
            
            # 找到网络中最近的节点
            min_node_dist = float('inf')
            closest_node = None
            
            for node in self.road_network.nodes():
                dist = Point(node).distance(bin_geom)
                if dist < min_node_dist:
                    min_node_dist = dist
                    closest_node = node
            
            if closest_node:
                # 计算网络距离
                try:
                    path_length = nx.shortest_path_length(
                        self.road_network, 
                        start_node, 
                        closest_node, 
                        weight='weight'
                    )
                    
                    if path_length < min_bin_dist:
                        min_bin_dist = path_length
                        nearest_bin = bin_geom
                        nearest_bin_node = closest_node
                except nx.NetworkXNoPath:
                    # 如果没有路径，继续检查下一个垃圾桶
                    continue
        
        return nearest_bin, nearest_bin_node
    
    def calculate_path(self, start_point, end_node):
        """计算从起点到终点的路径"""
        if self.road_network is None:
            return None
            
        # 找到网络中最近的节点作为起点
        min_dist = float('inf')
        start_node = None
        
        for node in self.road_network.nodes():
            dist = Point(node).distance(Point(start_point.x, start_point.y))
            if dist < min_dist:
                min_dist = dist
                start_node = node
        
        if not start_node or not end_node:
            return None
        
        # 使用NetworkX计算最短路径
        try:
            path_nodes = nx.shortest_path(
                self.road_network, 
                start_node, 
                end_node, 
                weight='weight'
            )
            
            # 检查路径节点数量
            if len(path_nodes) <= 1:
                # 处理只有一个节点的情况
                # 如果只有一个节点，创建一个包含该节点重复两次的LineString
                # 这样可以形成一条很短的线段，避免LineString创建失败
                node = path_nodes[0]
                # 创建一个微小偏移，确保两点不完全重合
                offset = 0.0000001
                path = LineString([(node[0], node[1]), (node[0] + offset, node[1] + offset)])
                print("注意: 路径只包含一个节点，已创建微小线段")
                return path
                
            # 将路径节点转换为LineString
            path = LineString(path_nodes)
            return path
        except nx.NetworkXNoPath:
            return None 