import pandas as pd
import random
import os

def generate_traffic_data(edges_path, output_path):
    edges_df = pd.read_csv(edges_path)

    time_factors = {
        '07:30': 0.5,   # rush 
        '12:00': 0.8,   # stable
        '17:30': 0.3,   # rush (worst)
        '21:00': 1.0,   # night
    }

    rows = []
    for _, edge in edges_df.iterrows():
        u = int(edge['u'])
        v = int(edge['v'])
        seg_id = f"{u}_{v}"
        base_speed = edge['speed_kph']
        
        for time_str, factor in time_factors.items():
            # Add ±20% to be more natural
            noise = random.uniform(0.8, 1.2)
            actual_speed = max(5, base_speed * factor * noise)
            density = int(100 - actual_speed)  # opposite to speed
            flow = int(actual_speed * density * 0.5)
            
            rows.append({
                'segment_id': seg_id,
                'time': time_str,
                'speed_kph': round(actual_speed, 1),
                'density': density,
                'flow': flow
            })

            traffic_df = pd.DataFrame(rows)
            traffic_df.to_csv(output_path, index=False)

if __name__ == "__main__":
    generate_traffic_data(
        edges_path='data/processed/edges.csv',
        output_path='data/processed/traffic.csv'
    )