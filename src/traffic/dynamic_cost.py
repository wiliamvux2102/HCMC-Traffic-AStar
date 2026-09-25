from src.traffic.traffic_model import TrafficModel


class DynamicCost:
    """
    Bộ tính cost động cho A*.
    
    Sử dụng:
        traffic = TrafficModel('data/processed/traffic.csv')
        cost_model = DynamicCost(traffic)
        
        # Tính cost của edge (u=1, v=2) lúc 17:30
        c = cost_model.edge_cost({'distance': 140, 'speed': 35}, '17:30')
    
    Đặc điểm:
        - cost = distance / actual_speed(t)  → time-dependent
        - Cùng 1 edge nhưng cost khác nhau ở các giờ khác nhau
    """

    # Vận tốc tối đa giả định trên toàn mạng (km/h)
    # → Dùng cho heuristic: h ≤ d / V_MAX
    V_MAX = 60.0

    def __init__(self, traffic_model: TrafficModel):
        """
        Args:
            traffic_model: instance TrafficModel đã load sẵn
        """
        if traffic_model is None:
            raise ValueError("traffic_model cannot be None")

        self.traffic = traffic_model
        

    # ------------------------------------------------------------------
    # API chính — dùng bởi A*
    # ------------------------------------------------------------------

    def edge_cost(self, edge: dict, time: str) -> float:
        """
        Tính chi phí đi hết 1 edge tại thời điểm `time`.
        
        Công thức:
            cost (phút) = distance_m / (speed_kph × 1000 / 60)
                        = distance_m × 60 / (speed_kph × 1000)
        
        Args:
            edge: dict có 'distance' (mét) và optional 'speed' (baseline)
            time: ví dụ '17:30'
        
        Returns:
            cost (phút)
        """
        distance_m = edge['distance']

        # Ưu tiên lấy speed động từ traffic model
        segment_id = edge.get('segment_id')
        if segment_id is None:
            # Fallback nếu edge không có segment_id
            speed_kph = edge.get('speed', 30.0)
        else:
            speed_kph = self.traffic.get_speed(segment_id, time)

        # Chống chia cho 0
        if speed_kph <= 0:
            speed_kph = 5.0  # coi như tắc cứng

        # Đổi m/s
        cost_min = (distance_m / 1000.0) / speed_kph * 60.0
        return cost_min

    def heuristic_factor(self, time: str) -> float:
        """
        Trả về α(t) — hệ số nhân cho heuristic.
        Delegate cho TrafficModel.
        """
        return self.traffic.get_traffic_factor(time)

    def heuristic(self, geo_distance_km: float, time: str) -> float:
        """
        Heuristic h(n, t) — lower bound thời gian còn lại tới goal.
        
        Công thức:
            h = (d_geo / V_MAX) × 60 × α(t)
        
        Trong đó:
            d_geo: khoảng cách đường chim bay (km)
            V_MAX: vận tốc tối đa giả định
            α(t): hệ số traffic ∈ (0, 1]
        
        Lý do admissible:
            - d_geo / V_MAX là lower bound thời gian (vì không xe nào
              nhanh hơn V_MAX).
            - α(t) ≤ 1 → h càng nhỏ, càng chắc chắn không overestimate.
        
        Args:
            geo_distance_km: khoảng cách haversine từ node hiện tại đến goal
            time: khung giờ
        
        Returns:
            h (phút)
        """
        alpha = self.heuristic_factor(time)
        h_minutes = (geo_distance_km / self.V_MAX) * 60.0 * alpha
        return h_minutes


if __name__ == "__main__":
    from src.traffic.traffic_model import TrafficModel

    # 1. Load traffic model
    traffic = TrafficModel('data/processed/traffic.csv')

    # 2. Khởi tạo cost model
    cost_model = DynamicCost(traffic)

    # 3. Test edge_cost với cùng 1 edge ở 4 khung giờ
    edge_sample = {
        'segment_id': '1_2',
        'distance': 140,       # mét
        'speed': 35,           # baseline (không dùng khi có segment_id)
    }

    print("\n=== Test edge_cost cho segment 1_2 (140m) ===")
    for t in traffic.available_times:
        c = cost_model.edge_cost(edge_sample, t)
        speed = traffic.get_speed('1_2', t)
        print(f"  {t}: speed = {speed:5.1f} km/h → cost = {c:.2f} phút")

    # 4. Test heuristic cho khoảng cách 5km
    print("\n=== Test heuristic cho d_geo = 5km ===")
    for t in traffic.available_times:
        h = cost_model.heuristic(5.0, t)
        alpha = cost_model.heuristic_factor(t)
        print(f"  {t}: α = {alpha} → h = {h:.2f} phút")