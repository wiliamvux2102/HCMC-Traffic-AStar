# README_MEM_2.md

# Member 2 — Traffic & Dynamic Cost

## Mục đích

Member 2 chịu trách nhiệm lấy tình trạng giao thông và biến nó thành **speed/cost cho từng OSM edge** để Member 3 dùng trong A*.

Flow tổng quát:

```text
OSM edges
   ↓
HERE realtime traffic
   ↓
normalize
   ↓
map HERE segment → OSM edge
   ↓
resolve conflict
   ↓
LIVE speed nếu có
   ↓
FALLBACK speed nếu không có live
   ↓
TrafficSnapshot
   ↓
A*
```

---

## Các file chính

```text
src/traffic/
├── baseline.py
├── speed_parser.py
├── normalizer.py
├── grid_fetcher.py
├── edge_mapper.py
├── mapping_resolver.py
├── fallback_provider.py
├── snapshot_builder.py
├── models.py
├── snapshot.py
├── provider.py
├── live_provider.py
├── replay_provider.py
├── service.py
└── cost.py
```

Ý nghĩa ngắn gọn:

```text
baseline.py
→ tạo free-flow speed từ OSM

grid_fetcher.py
→ lấy HERE realtime theo grid 4×4

normalizer.py
→ HERE JSON → bảng traffic sạch

edge_mapper.py
→ map geometry HERE sang OSM (u,v,k)

mapping_resolver.py
→ nếu nhiều HERE segment cùng map 1 OSM edge thì chọn match tốt nhất

fallback_provider.py
→ tạo speed dự phòng cho edge không có realtime

snapshot_builder.py
→ merge LIVE + FALLBACK

models.py / snapshot.py
→ tạo TrafficSnapshot

live_provider.py
→ chạy toàn bộ realtime pipeline

replay_provider.py
→ load snapshot cũ nếu LIVE lỗi

service.py
→ LIVE → REPLAY → FALLBACK

cost.py
→ tính thời gian đi qua edge
```

---

# Cách sử dụng

Member 3 chỉ cần dùng `TrafficService`.

```python
from datetime import datetime

from src.traffic.service import TrafficService
from src.traffic.cost import travel_time_seconds


service = TrafficService(
    edges_path="data/processed/edges_enriched.csv",
    cache_ttl_minutes=10
)

snapshot = service.get_snapshot(
    datetime.now()
)
```

Lấy speed của edge:

```python
speed = snapshot.speed(
    u,
    v,
    edge_key
)
```

Tính cost:

```python
cost = travel_time_seconds(
    distance_m,
    speed
)
```

Công thức:

```text
cost_seconds
=
3.6 * distance_m / speed_kph
```

Lấy speed bound cho heuristic:

```python
v_bound = snapshot.v_bound
```

Heuristic:

```text
h(n)
=
3.6 * straight_line_distance_m / v_bound
```

---

# Traffic source priority

```text
LIVE
 ↓ nếu lỗi
REPLAY
 ↓ nếu lỗi
FALLBACK
```

- **LIVE**: lấy HERE realtime tại thời điểm hiện tại.
- **REPLAY**: dùng complete snapshot gần nhất đã lưu.
- **FALLBACK**: dùng free-flow speed × time-of-day factor.

A* luôn nhận được một complete snapshot cho toàn graph.

---

# Khi present

Chỉ cần:

```python
snapshot = service.get_snapshot(
    datetime.now()
)
```

Nếu chưa có cache:

```text
→ fetch HERE realtime
→ build snapshot
```

Trong 10 phút tiếp theo:

```text
→ dùng lại cached snapshot
→ không gọi HERE lại
```

Nếu muốn ép refresh traffic:

```python
snapshot = service.refresh_snapshot(
    datetime.now()
)
```

---

# Artifact được lưu

Một lần LIVE fetch sẽ tạo:

```text
data/traffic/
├── raw_grid/      # raw HERE JSON
├── normalized/    # normalized HERE segments
├── mapping/       # HERE → OSM mapping
├── resolved/      # unique live OSM edge speeds
└── snapshots/     # complete snapshot
```

---

# Kết quả hiện tại

```text
Total OSM edges: 200540
Live edges:      25400
Overall live:    ~12.67%
```

Coverage đường chính:

```text
primary      ~91.5%
trunk        ~83.5%
secondary    ~79.2%
tertiary     ~40.3%
```

Các edge không có HERE realtime sẽ dùng FALLBACK.

---

# Rule quan trọng

```text
1. Luôn dùng edge key: (source, target, edge_key)

2. Không gọi HERE API bên trong A*

3. Một A* run dùng một TrafficSnapshot cố định

4. LIVE speed ưu tiên hơn FALLBACK

5. Nếu HERE lỗi:
   LIVE → REPLAY → FALLBACK

6. Không fetch lại traffic cho mỗi route query
   → dùng cache TTL
```

---

# Mental model

```text
Member 1:
"Đường nào tồn tại?"

Member 2:
"Hiện tại đi qua từng đường mất bao lâu?"

Member 3:
"Dùng các cost đó để A* chọn route."
```
