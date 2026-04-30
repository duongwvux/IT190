import osmnx as ox
import networkx as nx
import heapq
import math

def get_node_id_from_station(G, station_name):
    query = f"{station_name}, Berlin, Germany"
    try: 
        lat, lng = ox.geocode(query)
        nearest_node_id = ox.distance.nearest_nodes(G, X= lng, Y= lat)
        return nearest_node_id
    except Exception as e:
        print(f"❌ Không tìm thấy tọa độ cho ga: {station_name}")
        return None
    
def haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách (mét) giữa 2 tọa độ GPS"""
    R = 6371000  # Bán kính Trái Đất (mét)
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
        
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
    
def get_all_candidate_nodes(G, station_name, radius_meters=150):
    """
    Trả về DANH SÁCH tất cả các Node ID nằm trong bán kính của nhà ga.
    """
    query = f"{station_name}, Berlin, Germany"
    
    try:
        lat_center, lng_center = ox.geocode(query)
        lat_center, lng_center = float(lat_center), float(lng_center)
        
        candidates = []
        
        # Quét và gom tất cả các Node hợp lệ
        for node_id, data in G.nodes(data=True):
            node_lat = data['y']
            node_lng = data['x']
            
            dist = haversine_distance(lat_center, lng_center, node_lat, node_lng)
            
            if dist <= radius_meters:
                candidates.append(node_id)
                
        # Nếu không có Node nào trong bán kính, dùng hàm nearest_nodes làm phương án dự phòng
        if not candidates:
            fallback_node = int(ox.distance.nearest_nodes(G, X=[lng_center], Y=[lat_center])[0])
            return [fallback_node]
            
        return candidates
        
    except Exception as e:
        print(f"❌ Không thể định vị ga '{station_name}': {e}")
        return []

def dijkstra(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}
    
    pq = []
    
    # 1. Ném TẤT CẢ các điểm xuất phát vào hàng đợi với khoảng cách 0
    for start_node in start_nodes:
        distances[start_node] = 0
        heapq.heappush(pq, (0, start_node))
        
    best_end_node = None
    
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        # 2. Nếu điểm đang xét nằm trong danh sách ĐÍCH -> DỪNG NGAY!
        # Nhờ hàng đợi ưu tiên, điểm đích đầu tiên chạm tới chính là khoảng cách ngắn nhất.
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
            
        if current_dist > distances[current_node]:
            continue
            
        for neighbor in G.neighbors(current_node):
            edge_data = G[current_node][neighbor][0]
            
            # SỬA LỖI 2: Thêm giá trị mặc định 1.0 mét nếu không có length
            weight = float(edge_data.get('length', 1.0))
            dist = current_dist + weight

            if dist < distances[neighbor]:
                distances[neighbor] = dist
                previous_nodes[neighbor] = current_node 
                heapq.heappush(pq, (dist, neighbor))
                
    # 3. Rút trích đường đi từ best_end_node (Điểm đích tốt nhất vừa tìm được)
    if best_end_node is None:
        return None, float('infinity') # Không tìm thấy đường nào
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current)
        current = previous_nodes[current]    
        
    return path, distances[best_end_node]
    from collections import deque

def dfs(G: nx.MultiDiGraph, start_node, goal_node):
    """Thuật toán Tìm kiếm theo chiều sâu (DFS)"""
    open_set = [start_node] 
    closed = set()
    came_from = {}
    came_from[start_node] = None
    count_node = 0

    while open_set:
        count_node += 1
        current = open_set.pop()
        
        if current == goal_node:
            # Rút trích đường đi trực tiếp tại đây
            path = []
            curr = goal_node
            while curr is not None:
                path.insert(0, curr)
                curr = came_from.get(curr)
            return count_node, path
            
        if current not in closed:
            closed.add(current)
            for neighbor in G.neighbors(current):
                if neighbor not in closed:
                    came_from[neighbor] = current
                    open_set.append(neighbor)
                    
    return count_node, None

def bfs(G: nx.MultiDiGraph, start_node, goal_node):
    """Thuật toán Tìm kiếm theo chiều rộng (BFS)"""
    open_set = deque([start_node]) 
    closed = set([start_node])
    came_from = {}
    came_from[start_node] = None
    count_node = 0

    while open_set:
        count_node += 1
        current = open_set.popleft()
        
        if current == goal_node:
            # Rút trích đường đi trực tiếp tại đây
            path = []
            curr = goal_node
            while curr is not None:
                path.insert(0, curr)
                curr = came_from.get(curr)
            return count_node, path
            
        for neighbor in G.neighbors(current):
            if neighbor not in closed:
                closed.add(neighbor)
                came_from[neighbor] = current
                open_set.append(neighbor)
                
    return count_node, None

def ucs(G: nx.MultiDiGraph, start_node, goal_node):
    """Thuật toán Uniform Cost Search (UCS)"""
    open_queue = []
    heapq.heappush(open_queue, (0, start_node))
    open_set = {start_node}
    
    came_from = {}
    came_from[start_node] = None
    
    g_score = {node: float('inf') for node in G.nodes}
    g_score[start_node] = 0
    count_node = 0

    while open_queue:
        current_dist, current = heapq.heappop(open_queue)
        count_node += 1
        
        if current in open_set:
            open_set.remove(current)
            
        if current == goal_node:
            # Rút trích đường đi trực tiếp tại đây
            path = []
            curr = goal_node
            while curr is not None:
                path.insert(0, curr)
                curr = came_from.get(curr)
            return count_node, path
            
        for neighbor in G.neighbors(current):
            edge_data = G[current][neighbor][0]
            weight = float(edge_data.get('length', 1.0))
            tentative_g_score = g_score[current] + weight
            
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                
                if neighbor not in open_set:
                    heapq.heappush(open_queue, (tentative_g_score, neighbor))
                    open_set.add(neighbor)
                    
    return count_node, None
