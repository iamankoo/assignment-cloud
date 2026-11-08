"""My own minimal stateless-NACL evaluator (NOT the instructor's nacl_sim.py).

Usage: python tools/nacl_eval.py network/nacl.json network/packets_own.jsonl
Packets: {"id","direction","protocol","port","address","expected"}.
Lowest rule number first; first match wins; no match -> deny.
"""
import ipaddress
import json
import sys


def decide(rules, protocol, port, address):
    ip = ipaddress.ip_address(address)
    for r in sorted(rules, key=lambda r: r["rule"]):
        if ip not in ipaddress.ip_network(r["cidr"]):
            continue
        if r["protocol"] != "all":
            if r["protocol"] != protocol or not (r["port_from"] <= port <= r["port_to"]):
                continue
        return r["action"], r["rule"]
    return "deny", None


def main(rules_path, packets_path):
    nacl = json.load(open(rules_path))
    ok = total = 0
    for line in open(packets_path):
        if not line.strip():
            continue
        p = json.loads(line)
        action, rule = decide(nacl[p["direction"]], p["protocol"], p["port"], p["address"])
        good = action == p.get("expected")
        ok += good
        total += 1
        print(f'{p["id"]} {p["direction"]:8} {p["protocol"]} {p["port"]:<6} {p["address"]:<16} -> {action} (rule {rule}) {"OK" if good else "MISMATCH"}')
    print(f"{ok}/{total} as expected")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
