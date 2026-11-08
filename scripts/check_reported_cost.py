"""Arithmetic consistency check of the cost figures reported in the handwritten reflection.

This is NOT a measurement. It only checks whether three reported numbers agree with each other:
  hourly cost (INR/h), throughput (requests/h), cost per 1,000 requests (INR).
cost_per_1000 = hourly / requests_per_hour * 1000
"""
import sys

REPORTED = {"hourly_inr": 7.90, "requests_per_hour": 2052.0, "cost_per_1000_inr": 3.95}


def check(hourly, rph, reported):
    calc = hourly / rph * 1000
    implied_rph = hourly / reported * 1000
    return {
        "calculated_cost_per_1000": calc,
        "reported_cost_per_1000": reported,
        "difference": reported - calc,
        "difference_pct": (reported - calc) / calc * 100,
        "requests_per_hour_implied_by_reported_cost": implied_rph,
        "hourly_cost_per_replica_if_2_replicas": hourly / 2,
        "rps_from_requests_per_hour": rph / 3600,
        "agrees_within_0.5pct": abs(reported - calc) / calc < 0.005,
    }


def main():
    r = check(REPORTED["hourly_inr"], REPORTED["requests_per_hour"], REPORTED["cost_per_1000_inr"])
    print("Inputs (as reported in the reflection, unverified):", REPORTED)
    for k, v in r.items():
        print(f"{k}: {round(v, 4) if isinstance(v, float) else v}")
    print("RESULT:", "consistent" if r["agrees_within_0.5pct"] else "DISCREPANCY: reported cost per 1000 does not follow from the reported hourly cost and throughput")
    return 0


if __name__ == "__main__":
    sys.exit(main())
