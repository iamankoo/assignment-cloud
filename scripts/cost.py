"""Cost per 1,000 requests (Task 7). Pure arithmetic; inputs must come from a real load test.

Usage: python scripts/cost.py --rate-card data/rate_card.json --replicas 2 --cpu 1 --mem-gib 1 --rps <measured>
rate_card.json (kit) is expected to give price per vCPU-hour and per GiB-hour; key names are read from --cpu-key/--mem-key.
"""
import argparse
import json


def cost_per_1000(replicas, cpu, mem_gib, price_cpu_h, price_mem_h, rps):
    hourly = replicas * (cpu * price_cpu_h + mem_gib * price_mem_h)
    per_hour = rps * 3600
    return hourly, per_hour, hourly / per_hour * 1000


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate-card", required=True)
    ap.add_argument("--cpu-key", default="cpu_per_hour")
    ap.add_argument("--mem-key", default="memory_gib_per_hour")
    ap.add_argument("--replicas", type=int, default=2)
    ap.add_argument("--cpu", type=float, default=1.0)
    ap.add_argument("--mem-gib", type=float, default=1.0)
    ap.add_argument("--rps", type=float, required=True)
    a = ap.parse_args()
    card = json.load(open(a.rate_card))
    h, n, c = cost_per_1000(a.replicas, a.cpu, a.mem_gib, card[a.cpu_key], card[a.mem_key], a.rps)
    print(f"hourly {h:.4f}  requests/hour {n:.1f}  cost per 1000 requests {c:.4f}")
