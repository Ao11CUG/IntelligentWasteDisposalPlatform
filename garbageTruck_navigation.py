from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDialogButtonBox, QWidget, QPushButton, QListWidget, QListWidgetItem, QCheckBox, QGroupBox, QGridLayout, QMessageBox, QSpinBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import networkx as nx
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import nearest_points
import numpy as np
import matplotlib.pyplot as plt
from itertools import permutations
import time

class TruckCountDialog(QDialog):
    """垃圾车数量选择对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.truck_count = 1  # 默认垃圾车数量
        self.initUI()
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('垃圾车最优遍历')
        self.resize(400, 250)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: rgb(245, 245, 248);
                border-radius: 20px;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: rgb(80, 100, 100);
                padding: 5px;
            }
            QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 15px;
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
            QSpinBox {
                font-size: 14px;
                padding: 5px;
                border: 1px solid rgb(200, 200, 200);
                border-radius: 5px;
            }
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # 创建标题标签
        title_label = QLabel('垃圾车最优遍历设置')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 24px; font-weight: bold; margin-bottom: 15px; color: rgb(60, 90, 90);')
        main_layout.addWidget(title_label)
        
        # 创建垃圾车数量选择区域
        truck_layout = QHBoxLayout()
        truck_label = QLabel('垃圾车数量:')
        self.truck_spin = QSpinBox()
        self.truck_spin.setMinimum(1)
        self.truck_spin.setMaximum(5)  # 最多5辆垃圾车
        self.truck_spin.setValue(1)
        self.truck_spin.valueChanged.connect(self.on_truck_count_changed)
        truck_layout.addWidget(truck_label)
        truck_layout.addWidget(self.truck_spin)
        truck_layout.addStretch()
        main_layout.addLayout(truck_layout)
        
        # 添加说明标签
        tip_label = QLabel('请点击确定后，在地图上点击选择需要回收的垃圾桶。\n完成选择后，点击"开始规划"按钮进行路径规划。')
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet('font-size: 14px; color: rgb(100, 120, 120); margin-top: 20px;')
        tip_label.setWordWrap(True)
        main_layout.addWidget(tip_label)
        
        # 创建按钮
        button_box = QDialogButtonBox()
        self.ok_button = QPushButton('确定')
        self.cancel_button = QPushButton('取消')
        self.cancel_button.setStyleSheet("""
            background-color: rgb(210, 210, 215);
            color: rgb(40, 40, 40);
            font-weight: bold;
            border: 2px solid rgb(180, 180, 185);
        """)
        
        button_box.addButton(self.ok_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(self.cancel_button, QDialogButtonBox.RejectRole)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(button_box)
        
        # 设置对话框布局
        self.setLayout(main_layout)
    
    def on_truck_count_changed(self, value):
        """垃圾车数量变化处理"""
        self.truck_count = value
    
    def get_truck_count(self):
        """获取用户选择的垃圾车数量"""
        return self.truck_count

class GarbageTruckNavigation:
    """垃圾车导航类，用于垃圾车路径规划和最优遍历"""
    
    def __init__(self, roads_gdf, points_gdf):
        """初始化垃圾车导航类
        
        Args:
            roads_gdf: 道路GeoDataFrame
            points_gdf: 垃圾桶点GeoDataFrame
        """
        self.roads_gdf = roads_gdf
        self.points_gdf = points_gdf
        self.vehicle_road_network = None  # 车辆道路网络（大路）
        self.pedestrian_road_network = None  # 行人道路网络（包含所有道路）
        
        # 构建道路网络
        self.build_road_networks()
    
    def build_road_networks(self):
        """构建两种道路网络：车辆道路网络和行人道路网络"""
        # 创建两个新的网络图
        self.vehicle_road_network = nx.Graph()
        self.pedestrian_road_network = nx.Graph()
        
        if self.roads_gdf is None:
            return
            
        # 遍历每条道路线
        for idx, road in self.roads_gdf.iterrows():
            geom = road.geometry
            
            # 获取roadType字段值，判断道路类型
            # roadType=0 表示大路，可以让车通行
            # roadType=1 表示小路，只能让人通行
            road_type = road.get('roadType', 1)  # 默认为小路
            
            # 处理LineString
            if isinstance(geom, LineString):
                coords = list(geom.coords)
                # 添加节点和边
                for i in range(len(coords) - 1):
                    start_node = coords[i]
                    end_node = coords[i + 1]
                    # 计算两点之间的距离作为边的权重
                    distance = Point(start_node).distance(Point(end_node))
                    
                    # 所有道路都添加到行人道路网络
                    self.pedestrian_road_network.add_edge(start_node, end_node, weight=distance)
                    
                    # 只有大路才添加到车辆道路网络
                    if road_type == 0:
                        self.vehicle_road_network.add_edge(start_node, end_node, weight=distance)
            
            # 处理MultiLineString
            elif isinstance(geom, MultiLineString):
                for line in geom.geoms:
                    coords = list(line.coords)
                    for i in range(len(coords) - 1):
                        start_node = coords[i]
                        end_node = coords[i + 1]
                        distance = Point(start_node).distance(Point(end_node))
                        
                        # 所有道路都添加到行人道路网络
                        self.pedestrian_road_network.add_edge(start_node, end_node, weight=distance)
                        
                        # 只有大路才添加到车辆道路网络
                        if road_type == 0:
                            self.vehicle_road_network.add_edge(start_node, end_node, weight=distance)
    
    def find_td1_station(self):
        """查找名为td1的垃圾站"""
        if self.points_gdf is None:
            return None
            
        for idx, bin_point in self.points_gdf.iterrows():
            name = bin_point.get('Name', '')
            if name.lower() == 'td1':
                return idx, bin_point
                
        return None
    
    def find_nearest_road_node(self, point, vehicle_only=False):
        """查找离点最近的道路节点
        
        Args:
            point: 几何点
            vehicle_only: 是否只查找车辆可通行的道路节点
            
        Returns:
            最近的道路节点
        """
        if vehicle_only and self.vehicle_road_network is None:
            return None
        if not vehicle_only and self.pedestrian_road_network is None:
            return None
            
        # 选择使用的道路网络
        road_network = self.vehicle_road_network if vehicle_only else self.pedestrian_road_network
        
        # 找到最近的节点
        min_dist = float('inf')
        nearest_node = None
        
        for node in road_network.nodes():
            dist = Point(node).distance(point)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
        
        return nearest_node
    
    def calculate_distance_matrix(self, bin_ids):
        """计算垃圾桶之间的距离矩阵
        
        Args:
            bin_ids: 垃圾桶ID列表
            
        Returns:
            距离矩阵，bin_nodes列表
        """
        if self.points_gdf is None or self.vehicle_road_network is None:
            return None, None, None
            
        n = len(bin_ids)
        distance_matrix = np.zeros((n, n))
        bin_nodes = []
        bin_points = []
        
        # 为每个垃圾桶找到最近的道路节点
        for idx in bin_ids:
            bin_point = self.points_gdf.loc[idx].geometry
            bin_points.append(bin_point)
            node = self.find_nearest_road_node(bin_point, vehicle_only=True)
            bin_nodes.append(node)
        
        # 计算每对垃圾桶之间的最短路径距离
        for i in range(n):
            for j in range(n):
                if i == j:
                    distance_matrix[i][j] = 0
                    continue
                    
                try:
                    # 计算网络距离
                    path_length = nx.shortest_path_length(
                        self.vehicle_road_network,
                        bin_nodes[i],
                        bin_nodes[j],
                        weight='weight'
                    )
                    distance_matrix[i][j] = path_length
                except nx.NetworkXNoPath:
                    # 如果没有路径，设置一个很大的值
                    distance_matrix[i][j] = float('inf')
        
        return distance_matrix, bin_nodes, bin_points
    
    def plan_optimal_route(self, selected_bin_ids, truck_count=1):
        """规划最优垃圾回收路径
        
        Args:
            selected_bin_ids: 选择的垃圾桶ID列表
            truck_count: 垃圾车数量
            
        Returns:
            最优路径列表，每辆车负责的垃圾桶ID和路径
        """
        # 查找td1垃圾站
        td1_result = self.find_td1_station()
        if td1_result is None:
            print("未找到td1垃圾站！")
            return None
            
        td1_id, td1_point = td1_result
        
        # 如果只有一辆垃圾车，使用TSP求解
        if truck_count == 1:
            return self._plan_single_truck_route(selected_bin_ids, td1_id)
        else:
            # 多辆垃圾车，使用聚类+TSP求解
            return self._plan_multi_truck_route(selected_bin_ids, td1_id, truck_count)
    
    def _plan_single_truck_route(self, selected_bin_ids, td1_id):
        """规划单辆垃圾车的最优路径（TSP问题）
        
        Args:
            selected_bin_ids: 选择的垃圾桶ID列表
            td1_id: td1垃圾站ID
            
        Returns:
            最优路径
        """
        # 构建包含起点/终点和所有选定垃圾桶的ID列表
        bin_ids = [td1_id] + selected_bin_ids
        
        # 计算距离矩阵
        distance_matrix, bin_nodes, bin_points = self.calculate_distance_matrix(bin_ids)
        
        if distance_matrix is None:
            return None
        
        # TSP问题求解
        n = len(bin_ids)
        
        # 如果垃圾桶数量较少，使用暴力法求解
        if n <= 10:
            best_path, min_dist = self._solve_tsp_brute_force(distance_matrix)
        else:
            # 垃圾桶数量较多，使用贪心算法
            best_path, min_dist = self._solve_tsp_nearest_neighbor(distance_matrix)
        
        # 确保路径起点和终点都是td1垃圾站（索引0）
        if best_path[0] != 0:
            # 找到起点在路径中的位置，并旋转路径
            start_pos = best_path.index(0)
            best_path = best_path[start_pos:] + best_path[:start_pos]
        
        # 添加终点（回到起点）
        if best_path[-1] != 0:
            best_path.append(0)
        
        # 将索引转换回垃圾桶ID
        route_bin_ids = [bin_ids[i] for i in best_path]
        
        # 为路径中的每一段计算实际路径
        route_paths = []
        route_points = []
        
        for i in range(len(best_path) - 1):
            start_idx = best_path[i]
            end_idx = best_path[i + 1]
            
            start_node = bin_nodes[start_idx]
            end_node = bin_nodes[end_idx]
            
            # 计算两点间的最短路径
            try:
                path_nodes = nx.shortest_path(
                    self.vehicle_road_network,
                    start_node,
                    end_node,
                    weight='weight'
                )
                
                # 将路径节点转换为LineString
                if len(path_nodes) > 1:
                    path = LineString(path_nodes)
                    route_paths.append(path)
                    route_points.append(bin_points[start_idx])
            except nx.NetworkXNoPath:
                print(f"警告：从垃圾桶{bin_ids[start_idx]}到垃圾桶{bin_ids[end_idx]}没有可行路径！")
        
        # 添加最后一个点
        route_points.append(bin_points[best_path[-1]])
        
        return {
            'truck_id': 1,
            'bin_ids': route_bin_ids,
            'route_paths': route_paths,
            'route_points': route_points,
            'total_distance': min_dist
        }
    
    def _plan_multi_truck_route(self, selected_bin_ids, td1_id, truck_count):
        """规划多辆垃圾车的最优路径
        
        Args:
            selected_bin_ids: 选择的垃圾桶ID列表
            td1_id: td1垃圾站ID
            truck_count: 垃圾车数量
            
        Returns:
            每辆车的最优路径
        """
        # 如果垃圾车数量大于垃圾桶数量，调整垃圾车数量
        actual_truck_count = min(truck_count, len(selected_bin_ids))
        
        # 构建所有垃圾桶的距离矩阵
        all_bin_ids = [td1_id] + selected_bin_ids
        distance_matrix, bin_nodes, bin_points = self.calculate_distance_matrix(all_bin_ids)
        
        if distance_matrix is None:
            return None
        
        # 将垃圾桶分配给不同的垃圾车（简单策略：按照与td1的距离进行分组）
        td1_idx = 0  # td1在距离矩阵中的索引为0
        
        # 计算每个垃圾桶到td1的距离
        distances_to_td1 = [(i, distance_matrix[td1_idx][i]) for i in range(1, len(all_bin_ids))]
        
        # 按照距离排序
        distances_to_td1.sort(key=lambda x: x[1])
        
        # 将垃圾桶分配给垃圾车
        truck_bins = [[] for _ in range(actual_truck_count)]
        
        for i, (bin_idx, _) in enumerate(distances_to_td1):
            truck_idx = i % actual_truck_count
            truck_bins[truck_idx].append(bin_idx)
        
        # 为每辆垃圾车规划路径
        truck_routes = []
        
        for truck_idx, truck_bin_indices in enumerate(truck_bins):
            # 如果这辆车没有分配垃圾桶，跳过
            if not truck_bin_indices:
                continue
                
            # 提取该垃圾车负责的垃圾桶
            truck_bin_indices = [td1_idx] + truck_bin_indices  # 添加起点
            
            # 创建子距离矩阵
            sub_distance_matrix = np.zeros((len(truck_bin_indices), len(truck_bin_indices)))
            
            for i in range(len(truck_bin_indices)):
                for j in range(len(truck_bin_indices)):
                    orig_i = truck_bin_indices[i]
                    orig_j = truck_bin_indices[j]
                    sub_distance_matrix[i][j] = distance_matrix[orig_i][orig_j]
            
            # 解决TSP问题
            if len(truck_bin_indices) <= 10:
                best_path, min_dist = self._solve_tsp_brute_force(sub_distance_matrix)
            else:
                best_path, min_dist = self._solve_tsp_nearest_neighbor(sub_distance_matrix)
            
            # 确保路径起点和终点都是td1垃圾站（索引0）
            if best_path[0] != 0:
                start_pos = best_path.index(0)
                best_path = best_path[start_pos:] + best_path[:start_pos]
            
            # 添加终点（回到起点）
            if best_path[-1] != 0:
                best_path.append(0)
            
            # 将索引转换回全局索引
            global_path = [truck_bin_indices[i] for i in best_path]
            
            # 将索引转换回垃圾桶ID
            route_bin_ids = [all_bin_ids[i] for i in global_path]
            
            # 为路径中的每一段计算实际路径
            route_paths = []
            route_points = []
            
            for i in range(len(global_path) - 1):
                start_idx = global_path[i]
                end_idx = global_path[i + 1]
                
                start_node = bin_nodes[start_idx]
                end_node = bin_nodes[end_idx]
                
                # 计算两点间的最短路径
                try:
                    path_nodes = nx.shortest_path(
                        self.vehicle_road_network,
                        start_node,
                        end_node,
                        weight='weight'
                    )
                    
                    # 将路径节点转换为LineString
                    if len(path_nodes) > 1:
                        path = LineString(path_nodes)
                        route_paths.append(path)
                        route_points.append(bin_points[start_idx])
                except nx.NetworkXNoPath:
                    print(f"警告：从垃圾桶{all_bin_ids[start_idx]}到垃圾桶{all_bin_ids[end_idx]}没有可行路径！")
            
            # 添加最后一个点
            route_points.append(bin_points[global_path[-1]])
            
            truck_routes.append({
                'truck_id': truck_idx + 1,
                'bin_ids': route_bin_ids,
                'route_paths': route_paths,
                'route_points': route_points,
                'total_distance': min_dist
            })
        
        return truck_routes
    
    def _solve_tsp_brute_force(self, distance_matrix):
        """使用暴力法解决TSP问题
        
        Args:
            distance_matrix: 距离矩阵
            
        Returns:
            最优路径，最短距离
        """
        n = distance_matrix.shape[0]
        
        # 如果只有起点，直接返回
        if n <= 1:
            return [0], 0
        
        # 固定起点为0（td1垃圾站）
        best_path = None
        min_dist = float('inf')
        
        # 生成所有可能的路径（不包括起点）
        for path in permutations(range(1, n)):
            path = (0,) + path  # 添加起点
            
            # 计算路径总长度
            total_dist = 0
            for i in range(len(path) - 1):
                total_dist += distance_matrix[path[i]][path[i + 1]]
            
            # 加上从最后一个点回到起点的距离
            total_dist += distance_matrix[path[-1]][0]
            
            # 更新最短路径
            if total_dist < min_dist:
                min_dist = total_dist
                best_path = list(path)
        
        return best_path, min_dist
    
    def _solve_tsp_nearest_neighbor(self, distance_matrix):
        """使用最近邻算法解决TSP问题
        
        Args:
            distance_matrix: 距离矩阵
            
        Returns:
            路径，距离
        """
        n = distance_matrix.shape[0]
        
        # 如果只有起点，直接返回
        if n <= 1:
            return [0], 0
        
        # 从起点0开始
        current = 0
        path = [current]
        unvisited = set(range(1, n))  # 不包括起点
        total_dist = 0
        
        # 依次访问最近的未访问点
        while unvisited:
            # 查找距离当前点最近的未访问点
            min_dist = float('inf')
            nearest = None
            
            for next_point in unvisited:
                dist = distance_matrix[current][next_point]
                if dist < min_dist:
                    min_dist = dist
                    nearest = next_point
            
            # 如果找不到可达的点，跳出循环
            if nearest is None:
                break
                
            # 移动到最近的点
            current = nearest
            path.append(current)
            unvisited.remove(current)
            total_dist += min_dist
        
        # 添加回到起点的距离
        if path[-1] != 0:  # 如果最后一个点不是起点
            total_dist += distance_matrix[path[-1]][0]
        
        return path, total_dist
