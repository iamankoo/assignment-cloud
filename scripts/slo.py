"""Service Level Objective and error budget for one load-test run (Task 7). Pure arithmetic.

Usage: python scripts/slo.py --requests 1000 --failed 7 --target 99
error budget (requests) = (1 - target/100) * requests ; budget used = failed / budget
"""
import argparse


def error_budget(requests: int, failed: int, target_pct: float):
    budget = (1 - target_pct / 100) * requests
    used = failed / budget if budget else float("inf")
    return {
        "budget_requests": budget,
        "failed": failed,
        "budget_used_pct": used * 100,
        "success_rate_pct": (requests - failed) / requests * 100 if requests else 0.0,
        "slo_met": failed <= budget,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--requests", type=int, required=True)
    ap.add_argument("--failed", type=int, required=True)
    ap.add_argument("--target", type=float, default=99.0, help="success-rate target in percent")
    a = ap.parse_args()
    r = error_budget(a.requests, a.failed, a.target)
    print(
        f"SLO {a.target}% over {a.requests} requests: budget {r['budget_requests']:.2f} failures, observed {r['failed']}, "
        f"budget used {r['budget_used_pct']:.1f}%, success {r['success_rate_pct']:.2f}% -> {'MET' if r['slo_met'] else 'NOT MET'}"
    )
