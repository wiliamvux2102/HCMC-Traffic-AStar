# HCMC Traffic A* — phần thuật toán

Phần phụ trách: A*, Dijkstra baseline, heuristic và chứng minh/kiểm tra
admissibility, consistency theo tài liệu kỹ thuật v1.0 của nhóm.

## Module chính

```text
src/routing/
  astar.py                 A* trên snapshot cố định
  dijkstra_baseline.py     Dijkstra và ground truth trên reverse graph
  heuristic.py             Haversine / V_bound, đơn vị giây
  cost.py                  Chi phí cạnh theo snapshot
  models.py                RouteResult dùng khi ghép với nhóm
src/evaluation/
  admissibility.py         So với exact cost tới goal
  consistency.py           Kiểm tra từng cạnh có hướng
  benchmark.py             So sánh A* và Dijkstra
src/graph/loader.py         Đọc graph/POI, giữ khóa (u,v,k)
tests/test_routing.py       Kiểm thử thuật toán và heuristic
docs/ALGORITHM.md          Công thức, chứng minh và hướng tích hợp
```

Các module traffic/data có sẵn của nhóm cung cấp đầu vào cho thuật toán.
Phần LIVE/UI đã được đưa về trạng thái trước lần triển khai này.

## Chạy

Sau khi cài `pip install -r requirements.txt`, chạy từ thư mục dự án:

```powershell
python main.py --start POI0001 --goal POI0002 --timestamp 2026-10-02T17:30:00+07:00 --verify
python main.py --timestamp 2026-10-02T17:30:00+07:00 --benchmark-pairs 20
python main.py --start POI0001 --goal POI0002 --timestamp 2026-10-02T17:30:00+07:00 --mode REPLAY --snapshot data/traffic/normalized/example.csv --verify
python -m unittest discover -s tests -v
```

Mặc định CLI dùng FALLBACK theo tốc độ nền và khung giờ để kiểm chứng offline.
REPLAY dùng CSV normalized có timestamp gốc; dữ liệu thiếu cạnh được bổ sung
từ FALLBACK trước khi tính V_bound. Không có chế độ LIVE/AUTO trong CLI này.
Nếu chưa có `edges_enriched.csv`, chạy `python -m src.scripts.build_baseline`.

Hai điểm cùng road node có chi phí 0; no-path có `found=False`. ETA và distance
chỉ tính phần đường bộ, chưa tính đoạn nối POI tới road node.
