from shapely.geometry import Point

class TrashBinInfo:
    """封装垃圾桶信息查看功能"""
    
    def __init__(self, points_gdf):
        """初始化垃圾桶信息类
        
        Args:
            points_gdf: 垃圾桶点GeoDataFrame
        """
        self.points_gdf = points_gdf
        # 存储解析后的垃圾桶信息
        self.bins_info = {}
        # 解析所有垃圾桶信息
        if points_gdf is not None:
            self.parse_bins_info()
    
    def parse_bins_info(self):
        """解析所有垃圾桶信息"""
        if self.points_gdf is None:
            return
            
        for idx, bin_point in self.points_gdf.iterrows():
            bin_id = idx
            bin_geom = bin_point.geometry
            
            # 获取Remark和Name字段值
            remark = bin_point.get('Remark', '')
            name = bin_point.get('Name', '')
            
            # 解析垃圾桶类型
            bin_type = self.parse_remark(remark)
            
            # 解析垃圾桶大小
            bin_size = self.parse_name(name)
            
            # 存储解析结果
            self.bins_info[bin_id] = {
                'geometry': bin_geom,
                'type': bin_type,
                'size': bin_size,
                'remark': remark,
                'name': name
            }
    
    def parse_remark(self, remark):
        """解析Remark字段，获取垃圾桶类型
        
        Args:
            remark: Remark字段值
            
        Returns:
            list: 垃圾桶类型列表
        
        说明:
            - 如果remark为'Dumpster'，则返回['垃圾站']
            - 否则检查remark中是否包含以下字母，包含则添加对应垃圾桶类型:
              - 'C': 厨余垃圾
              - 'K': 可回收垃圾
              - 'Q': 其他垃圾
              - 'Y': 有害垃圾
            - 例如，如果remark='KQ'，则返回['可回收垃圾', '其他垃圾']
        """
        if not remark:
            return []
            
        # 如果是Dumpster，表示垃圾站
        if remark.lower() == 'dumpster':
            return ['垃圾站']
            
        # 解析垃圾桶类型
        bin_types = []
        
        # 查找类型代码: 检查remark中包含的字母，添加对应的垃圾桶类型
        if 'C' in remark:
            bin_types.append('厨余垃圾')
        if 'K' in remark:
            bin_types.append('可回收垃圾')
        if 'Q' in remark:
            bin_types.append('其他垃圾')
        if 'Y' in remark:
            bin_types.append('有害垃圾')
        
        return bin_types
    
    def parse_name(self, name):
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
    
    def find_nearest_bin(self, click_point, max_distance=0.001):
        """查找离点击位置最近的垃圾桶
        
        Args:
            click_point: 点击位置的Point对象
            max_distance: 最大搜索距离
            
        Returns:
            tuple: (bin_id, bin_info) 或 None
        """
        if not self.bins_info:
            return None
            
        min_distance = float('inf')
        nearest_bin_id = None
        
        for bin_id, bin_info in self.bins_info.items():
            bin_geom = bin_info['geometry']
            
            # 计算点到垃圾桶的距离
            dist = bin_geom.distance(click_point)
            
            if dist < min_distance and dist < max_distance:
                min_distance = dist
                nearest_bin_id = bin_id
        
        if nearest_bin_id is not None:
            return nearest_bin_id, self.bins_info[nearest_bin_id]
        
        return None
    
    def show_bin_info(self, bin_info):
        """显示垃圾桶信息
        
        Args:
            bin_info: 垃圾桶信息字典
            
        Returns:
            str: 格式化的垃圾桶信息字符串
        """
        if not bin_info:
            return "未找到垃圾桶信息"
            
        bin_type_str = '、'.join(bin_info['type']) if bin_info['type'] else '未知类型'
        
        info = f"垃圾桶信息:\n"
        info += f"类型: {bin_type_str}\n"
        info += f"大小: {bin_info['size']}"
        
        print(info)
        return info 