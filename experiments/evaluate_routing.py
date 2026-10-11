"""Evaluate routing and heuristic correctness using fixed traffic snapshots."""
import csv
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.graph.loader import load_graph
from src.routing.astar import AStar
from src.routing.dijkstra_baseline import Dijkstra
from src.routing.heuristic import haversine_distance
from src.evaluation.admissibility import check_admissibility
from src.evaluation.consistency import check_consistency
from src.traffic.fallback_provider import FallbackProvider
from src.traffic.models import TrafficSnapshot
from src.traffic.snapshot import load_snapshot_csv

OUT = Path(os.environ.get('ROUTING_EVALUATION_OUTPUT', str(ROOT / 'experiments/results/evaluation')))
OUT.mkdir(parents=True, exist_ok=True)

class BoundView:
    """Cache one immutable snapshot's maximum for whole-graph checking only."""
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.v_bound = snapshot.v_bound
    def __getattr__(self, name):
        return getattr(self.snapshot, name)

def compact_result(value):
    """Keep measurements without repeating complete route geometry in the output."""
    if isinstance(value, dict):
        return {key: compact_result(item) for key, item in value.items()
                if key not in {'path_nodes', 'path_edges'}}
    if isinstance(value, (list, tuple)):
        return [compact_result(item) for item in value]
    return value


def save(name, value):
    (OUT / name).write_text(json.dumps(compact_result(value), indent=2, ensure_ascii=False,
                                     allow_nan=False), encoding='utf-8')

def main():
    graph = load_graph()
    astar, dijkstra = AStar(graph), Dijkstra(graph)
    data = ROOT / 'data/processed'
    hashes = {n: hashlib.sha256((data / n).read_bytes()).hexdigest() for n in
              ['nodes.csv','edges.csv','edges_enriched.csv','poi_final.csv','poi_node_mapping.csv']}
    gaps = [e['meta']['distance_m'] - haversine_distance(graph.nodes[k[0]].lat,graph.nodes[k[0]].lon,
            graph.nodes[k[1]].lat,graph.nodes[k[1]].lon) for k,e in graph.edge_index.items()]
    rng = random.Random(3061)
    ids = list(graph.poi_to_node)
    pairs = []
    while len(pairs) < 20:
        a,b = rng.sample(ids,2)
        if graph.poi_to_node[a] != graph.poi_to_node[b]:
            pairs.append((a,b))
    with (data/'edges.csv').open(encoding='utf-8-sig',newline='') as stream:
        raw=list(csv.DictReader(stream))
    raw_keys=[(int(x['source']),int(x['target']),int(x['edge_key'])) for x in raw]
    raw_mismatch=sum(k not in graph.edge_index or not math.isclose(float(x['distance_m']),graph.edge_index[k]['meta']['distance_m'],rel_tol=1e-9,abs_tol=1e-6) for k,x in zip(raw_keys,raw))
    data_validation={'raw_edges':len(raw),'raw_duplicate_edges':len(raw_keys)-len(set(raw_keys)),
        'raw_only_edges':len(set(raw_keys)-graph.edge_index.keys()),'enriched_only_edges':len(graph.edge_index.keys()-set(raw_keys)),
        'length_mismatches':raw_mismatch}
    del raw,raw_keys
    metadata = {'run_at_utc':datetime.now(timezone.utc).isoformat(),'data_validation':data_validation,
        'python':sys.version,'platform':platform.platform(),'processor':platform.processor(),
        'nodes':len(graph.nodes),'edges':len(graph.edge_index),'pois':len(graph.pois),
        'seed':3061,'repeats':3,'pairs':pairs,'sha256':hashes,
        'minimum_length_minus_haversine_m':min(gaps),'negative_geometry_gaps':sum(x<0 for x in gaps),
        'heuristic_check_method':'Project validators with the fixed snapshot maximum cached once.',
        'runtime_method':'Median of 3 searches per pair and algorithm; alternating which algorithm runs first. Constructors and loading excluded; per-query bound scan included.'}
    save('metadata.json',metadata)
    print('GRAPH',metadata['nodes'],metadata['edges'],metadata['pois'],flush=True)
    fallback=FallbackProvider(str(data/'edges_enriched.csv'))
    snapshots=[('12:00 FALLBACK',fallback.get_snapshot(datetime.fromisoformat('2026-10-11T12:00:00+07:00'))),
               ('17:30 FALLBACK',fallback.get_snapshot(datetime.fromisoformat('2026-10-11T17:30:00+07:00')))]
    path=sorted((ROOT/'data/traffic/snapshots').glob('**/*-complete.csv'))[-1]
    captured=path.parent.name+'T'+path.name[:8].replace('-',':')+'+07:00'
    replay=load_snapshot_csv(str(path),captured)
    replay=TrafficSnapshot(replay.timestamp,replay.edge_speed,replay.provenance,mode='REPLAY')
    metadata['replay_source']=path.relative_to(ROOT).as_posix(); save('metadata.json',metadata)
    snapshots.append(('Recorded REPLAY',replay))
    records=[]
    for label,snapshot in snapshots:
        view=BoundView(snapshot)
        checks=[]
        for poi in ['POI0001','POI0002']:
            goal=graph.poi_to_node[poi]
            a=check_admissibility(graph,view,goal); c=check_consistency(graph,view,goal)
            checks.append({'poi':poi,'admissibility':a,'consistency':c})
            print('HEURISTIC',label,poi,a['passed'],c['passed'],flush=True)
        rows=[]
        for i,(sp,gp) in enumerate(pairs):
            start,goal=graph.poi_to_node[sp],graph.poi_to_node[gp]
            runs={'astar':[],'dijkstra':[]}
            for repeat in range(3):
                order=['astar','dijkstra'] if (i+repeat)%2==0 else ['dijkstra','astar']
                for algo in order:
                    solver=astar if algo=='astar' else dijkstra
                    runs[algo].append(asdict(solver.search(start,goal,snapshot)))
            a,d=dict(runs['astar'][0]),dict(runs['dijkstra'][0])
            matched=all(x['found']==a['found'] and (not a['found'] or math.isclose(x['total_time_s'],a['total_time_s'],rel_tol=1e-9,abs_tol=1e-7)) for rr in runs.values() for x in rr)
            row={'start_poi':sp,'goal_poi':gp,'start':start,'goal':goal,'optimality_passed':matched,
                 'astar':a,'dijkstra':d,'runs':runs}
            for algo in runs:
                row[algo]['runtime_ms']=statistics.median(x['runtime_ms'] for x in runs[algo])
            rows.append(row)
            print('BENCHMARK',label,i+1,'/20',matched,flush=True)
        summary={algo:{k:statistics.mean(x[algo][k] for x in rows) for k in ['total_time_s','expanded_nodes','runtime_ms']} for algo in ['astar','dijkstra']}
        summary['expanded_reduction_percent']=100*(1-summary['astar']['expanded_nodes']/summary['dijkstra']['expanded_nodes'])
        summary['reachable_cases']=sum(x['astar']['found'] for x in rows)
        summary['fewer_expansions_cases']=sum(x['astar']['expanded_nodes']<x['dijkstra']['expanded_nodes'] for x in rows)
        result={'label':label,'timestamp':snapshot.timestamp,'mode':snapshot.mode,'v_bound_kph':snapshot.v_bound,
                'provenance':dict(Counter(snapshot.provenance.values())), 'heuristic_checks':checks,'case_count':len(rows),
                'passed':all(x['optimality_passed'] for x in rows),'cases':rows,'summary':summary,
                'example':asdict(astar.search(graph.poi_to_node['POI0001'],graph.poi_to_node['POI0002'],snapshot))}
        records.append(result); save('routing-results.json',records)
        print('SUMMARY',label,json.dumps(summary),flush=True)
    speeds={k:float(e['meta']['free_flow_speed_kph']) for k,e in graph.edge_index.items()}
    free=TrafficSnapshot(replay.timestamp,speeds,{k:'fallback' for k in speeds},mode='FALLBACK')
    comparisons=[]
    for i,(sp,gp) in enumerate(pairs):
        base=astar.search(graph.poi_to_node[sp],graph.poi_to_node[gp],free)
        traffic=records[-1]['cases'][i]['astar']
        comparisons.append({'start_poi':sp,'goal_poi':gp,'free_flow':asdict(base),
            'recorded_traffic_time_s':traffic['total_time_s'],
            'path_changed':base.path_edges!=[tuple(k) for k in traffic['path_edges']]})
    save('freeflow-comparison.json',{'description':'Same A* and graph; free-flow speeds versus recorded replay speeds. Free flow is a baseline, not a captured traffic snapshot.',
        'cases':comparisons,'changed_route_cases':sum(x['path_changed'] for x in comparisons),
        'mean_freeflow_time_s':statistics.mean(x['free_flow']['total_time_s'] for x in comparisons),
        'mean_recorded_time_s':statistics.mean(x['recorded_traffic_time_s'] for x in comparisons)})
    print('EVALUATION COMPLETE',flush=True)

if __name__=='__main__':
    main()
