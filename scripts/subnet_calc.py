"""Allocate subnets from a /16, largest requirement first, contiguous, smallest fitting prefix."""
import ipaddress
import math


def allocate(base, reqs):
    cur = int(ipaddress.ip_network(base).network_address)
    out = []
    for name, hosts in sorted(reqs, key=lambda x: -x[1]):
        prefix = 32 - math.ceil(math.log2(hosts + 2))
        net = ipaddress.ip_network((cur, prefix))
        out.append((name, hosts, net))
        cur = int(net.broadcast_address) + 1
    return out


if __name__ == "__main__":
    for name, hosts, n in allocate("10.20.0.0/16", [("app", 1000), ("public", 250), ("data", 100), ("management", 20)]):
        print(f"{name:11} need {hosts:5} {str(n):16} usable {n.num_addresses - 2:5} {n[1]} - {n[-2]} broadcast {n.broadcast_address}")
