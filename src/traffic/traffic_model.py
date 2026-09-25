import pandas as pd
import os

class TrafficModel:
    """Base traffic model container."""

    # Classification by threshold
    TRAFFIC_LEVELS = {
        'LOW':       (40, float('inf')),   # ≥ 40 km/h
        'MEDIUM':    (25, 40),             # 25–40 km/h
        'HIGH':      (15, 25),             # 15–25 km/h
        'VERY_HIGH': (0, 15),              # < 15 km/h
    }

    # Factor α(t) for heuristic — the more congested, the smaller α(t) gets
    TRAFFIC_FACTORS = {
        'LOW':       1.0,
        'MEDIUM':    0.8,
        'HIGH':      0.6,
        'VERY_HIGH': 0.4,
    }

    def __init__(self, traffic_csv_path: str):
        if not os.path.exists(traffic_csv_path):
            raise FileNotFoundError(f"File cannot be found: {traffic_csv_path}")

        self.df = pd.read_csv(traffic_csv_path)

        # Casting
        self.df['speed_kph'] = self.df['speed_kph'].astype(float)
        self.df['time'] = self.df['time'].astype(str)

        # Build lookup dict: {(segment_id, time): speed}
        # → Query O(1) instead of filter DataFrame each time
        self._speed_index = {
            (row['segment_id'], row['time']): row['speed_kph']
            for _, row in self.df.iterrows()
        }

        # Build list for available schedule
        self.available_times = sorted(self.df['time'].unique().tolist())

        # Cache traffic level by each time slot (caculate once, use many times)
        self._level_cache = {}


    def get_speed(self, segment_id: str, time: str, default: float = 30.0) -> float:
        """
        Args:
            segment_id: ex: '1_2'
            time: ex: '17:30'
            default: fallback if no available data

        Returns:
            speed_kph (float)
        """
        return self._speed_index.get((segment_id, time), default)

    def get_traffic_level(self, time: str) -> str:
        """
        Return to the overall traffic level at that time slot.
        """
        if time in self._level_cache:
            return self._level_cache[time]

        records = self.df[self.df['time'] == time]

        if len(records) == 0:
            return 'UNKNOWN'

        avg_speed = records['speed_kph'].mean()

        for level, (low, high) in self.TRAFFIC_LEVELS.items():
            if low <= avg_speed < high:
                self._level_cache[time] = level
                return level

        return 'UNKNOWN'

    def get_traffic_factor(self, time: str) -> float:
        level = self.get_traffic_level(time)
        return self.TRAFFIC_FACTORS.get(level, 0.8)

    def summary(self) -> pd.DataFrame:
        """Summary for each time slot"""
        summary = self.df.groupby('time').agg(
            avg_speed=('speed_kph', 'mean'),
            min_speed=('speed_kph', 'min'),
            max_speed=('speed_kph', 'max'),
            n_segments=('segment_id', 'count')
        ).reset_index()
        summary['level'] = summary['time'].apply(self.get_traffic_level)
        summary['alpha'] = summary['time'].apply(self.get_traffic_factor)
        return summary


if __name__ == "__main__":
    model = TrafficModel('data/processed/traffic.csv')

    print("\n=== Test get_speed ===")
    for t in model.available_times:
        s = model.get_speed('1_2', t)
        print(f"  Segment 1_2 @ {t}: {s} km/h")

    print("\n=== Test get_traffic_level ===")
    for t in model.available_times:
        level = model.get_traffic_level(t)
        alpha = model.get_traffic_factor(t)
        print(f"  {t} → {level:10s} (α = {alpha})")

    print("\n=== Summary ===")
    print(model.summary().to_string(index=False))
