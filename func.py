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
import heapq
import networkx as nx

def dfs(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    open_set = list(start_nodes) # Sử dụng List như một Stack (LIFO)
    closed = set()
    previous_nodes = {node: None for node in start_nodes}
    
    best_end_node = None

    while open_set:
        # Lấy phần tử ở ĐỈNH stack (phần tử được thêm vào gần nhất)
        current_node = open_set.pop()
        
        # 1. Nếu điểm đang xét nằm trong danh sách ĐÍCH -> DỪNG NGAY!
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
            
        if current_node not in closed:
            closed.add(current_node) # Đánh dấu đã duyệt
            # Duyệt qua các hàng xóm
            for neighbor in G.neighbors(current_node):
                if neighbor not in closed:
                    previous_nodes[neighbor] = current_node
                    open_set.append(neighbor) # Đẩy vào Stack
                    
    # 2. Rút trích đường đi từ best_end_node về điểm xuất phát
    if best_end_node is None:
        return None, float('infinity') # Không tìm thấy đường nào
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current) # Chèn vào đầu mảng để ra đúng thứ tự
        current = previous_nodes.get(current)
        
    return path, len(path) - 1

def bfs(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    open_set = deque(start_nodes) # Sử dụng Deque như một Queue (FIFO)
    closed = set(start_nodes)     # BFS đánh dấu closed ngay khi cho vào queue để tránh lặp
    previous_nodes = {node: None for node in start_nodes}
    
    best_end_node = None

    while open_set:
        # Lấy phần tử ở ĐẦU hàng đợi (phần tử vào sớm nhất)
        current_node = open_set.popleft()
        
        # 1. Nếu điểm đang xét nằm trong danh sách ĐÍCH -> DỪNG NGAY!
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
            
        for neighbor in G.neighbors(current_node):
            if neighbor not in closed:
                closed.add(neighbor) # Đánh dấu duyệt ngay khi nhìn thấy
                previous_nodes[neighbor] = current_node
                open_set.append(neighbor) # Đẩy vào cuối Queue
                
    # 2. Rút trích đường đi từ best_end_node
    if best_end_node is None:
        return None, float('infinity') # Không tìm thấy đường nào
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current)
        current = previous_nodes.get(current)
        
    return path, len(path) - 1

def ucs(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}
    
    pq = [] # Priority Queue dùng heapq
    
    # 1. Ném TẤT CẢ các điểm xuất phát vào hàng đợi ưu tiên với chi phí 0
    for start_node in start_nodes:
        distances[start_node] = 0
        heapq.heappush(pq, (0, start_node))
        
    best_end_node = None

    while pq:
        # Lấy node có chi phí CỘNG DỒN nhỏ nhất hiện tại ra khỏi Priority Queue
        current_dist, current_node = heapq.heappop(pq)
        
        # 2. ĐIỀU KIỆN DỪNG: Với UCS, phải chờ khi node được POP RA khỏi hàng đợi ưu tiên 
        # mới được check đích, vì lúc này mới đảm bảo đó là đường ngắn nhất.
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
            
        # Bỏ qua nếu ta đã tìm thấy một đường ngắn hơn đến node này trước đó (tối ưu hóa Priority Queue)
        if current_dist > distances[current_node]:
            continue
            
        for neighbor in G.neighbors(current_node):
            # FIXED: Do đồ thị là MultiDiGraph, giữa 2 node có thể có NGUYÊN MỘT TẬP CÁC CẠNH.
            # Ta cần duyệt qua các cạnh này và lấy cạnh có độ dài ngắn nhất.
            min_weight = float('infinity')
            for edge_key, edge_data in G[current_node][neighbor].items():
                w = float(edge_data.get('length', 1.0))
                if w < min_weight:
                    min_weight = w
                    
            dist = current_dist + min_weight
            
            # Nếu tìm được đường đi tới neighbor ngắn hơn đường cũ
            if dist < distances[neighbor]:
                distances[neighbor] = dist
                previous_nodes[neighbor] = current_node
                # Đẩy cập nhật mới vào hàng đợi ưu tiên
                heapq.heappush(pq, (dist, neighbor))
                
    # 3. Rút trích đường đi từ best_end_node
    if best_end_node is None:
        return None, float('infinity') # Không tìm thấy đường nào
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current)
        current = previous_nodes[current] # Traceback lại đường đi
        
    return path, distances[best_end_node]
