# Thuật toán và chứng minh heuristic

Tài liệu tham chiếu: mục 7, 8, 9, 11 và contract RouteResult trong tài liệu
kỹ thuật v1.0 của nhóm. Scope của module này là routing và evaluation; nhóm
traffic chuẩn bị snapshot, nhóm UI sử dụng RouteResult.

## Đầu vào và đơn vị

Graph có hướng, giữ từng cạnh song song bằng `(u,v,k)`. Chiều dài `L_e` tính
bằng mét; tốc độ `v_e` tính bằng km/h; cost, g, h và total_time_s tính bằng giây.
Một lần tìm đường dùng cùng một snapshot bất biến, đủ tốc độ dương hữu hạn
cho mọi cạnh. `V_bound = max_e v_e` được tính sau khi fill missing speed.

```text
c(e) = 3.6 * L_e / v_e
h(n) = 3.6 * d_Haversine(n, goal) / V_bound
f(n) = g(n) + h(n)
```

Không nhân alpha riêng của mỗi cạnh vào heuristic. Traffic khác nhau trên
từng cạnh đã được thể hiện qua `v_e` và cost. Heuristic dùng một V_bound chung.
A* dùng heap priority queue, bỏ entry lỗi thời và lưu predecessor edge để
reconstruct đúng khóa cạnh. Không thay graph weight thành thời gian ở giữa
lần chạy. Dijkstra baseline dùng h=0; reverse Dijkstra là ground truth độc lập.

## Admissibility

Với mọi cạnh, `v_e <= V_bound`, suy ra
`c(e) >= 3.6 * L_e / V_bound`. Với mọi đường đi P từ n tới goal,
`sum(L_e) >= d_Haversine(n,goal)` nếu chiều dài cạnh không nhỏ hơn khoảng cách
chim bay giữa hai đầu cạnh. Vì vậy:

```text
cost(P) >= 3.6 * sum(L_e) / V_bound >= h(n)
```

Điều này đúng với mọi P nên cũng đúng với đường tối ưu: `h(n) <= h*(n)`.
Tại goal, h=0; node không tới được goal có h*=infinity.

## Consistency

Với cạnh u→v, bất đẳng thức tam giác cho
`d(u,goal) <= d(u,v) + d(v,goal) <= L_(u,v,k) + d(v,goal)`. Suy ra:

```text
h(u) <= 3.6 * L_(u,v,k) / V_bound + h(v)
     <= c(u,v,k) + h(v)
```

A* kiểm tra giả thiết về chiều dài cạnh lúc khởi tạo (tolerance 1e-6 m).
Snapshot từ chối tốc độ không dương, NaN/inf; lần tìm đường từ chối missing
speed. Kiểm tra thực nghiệm dùng epsilon giây cho sai số floating-point.
Chứng minh không áp dụng cho snapshot bị thay đổi giữa chừng hoặc cost có
penalty âm. Nếu thêm penalty không âm, lower bound vẫn hợp lệ.

## Tích hợp với thành viên khác

```python
from src.routing.astar import AStar

# graph do loader hoặc thành viên dữ liệu xây dựng.
# snapshot do thành viên traffic chuẩn hóa và fill đầy đủ.
result = AStar(graph).search(start_node, goal_node, snapshot)
# result.path_edges: [(u,v,k), ...]
# result.total_time_s, result.total_distance_m, result.expanded_nodes
# result.runtime_ms, result.snapshot_timestamp, result.traffic_mode
```

Tham số thuật toán là road node ID. Có thể lấy node từ
`graph.poi_to_node[poi_id]`. Không có đường đi: `found=False`, path rỗng,
các tổng bằng 0 để JSON hợp lệ; chỉ đọc ETA khi found=True.

## Kiểm tra

`check_admissibility(graph, snapshot, goal)` dùng exact cost tới goal từ
Dijkstra trên reverse graph. `check_consistency(graph, snapshot, goal)` kiểm
tra tất cả cạnh, kể cả cạnh song song. `compare_routes` kiểm tra A* và Dijkstra
cùng cost/reachability; không bắt buộc cùng path khi có nhiều route đồng hạng.
Reports gồm số phần tử đã kiểm tra và chi tiết vi phạm, không trả True giả.

CLI `--verify` và `--benchmark-pairs 20` dùng cùng snapshot cho mọi thuật toán.
Các test bao gồm graph nhỏ có thể tính tay, chọn cạnh song song, snapshot đổi
route, no-path, start=goal, dữ liệu sai và heuristic admissible nhưng không
consistent. Kết quả thực nghiệm là bằng chứng cho dataset/snapshot đã chạy;
chứng minh toán học ở trên là cơ sở tổng quát.
