# Task 5: Subnets and NACL (10.20.0.0/16)

Method: largest requirement first, contiguous from 10.20.0.0, smallest prefix with 2^(32-p)-2 >= hosts.

| Subnet | Hosts | Prefix | Network | Usable range | Broadcast | Usable |
|---|---:|---|---|---|---|---:|
| app | 1,000 | /22 | 10.20.0.0 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1,022 |
| public | 250 | /24 | 10.20.4.0 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 100 | /25 | 10.20.5.0 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 20 | /27 | 10.20.5.128 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

Why: /23 gives 510 (<1000), /25 gives 126 (<250), /26 gives 62 (<100), /28 gives 14 (<20).

## NACL for `public` (see `nacl.json`)
Inbound: 100 deny all from 198.51.100.0/24; 110 allow tcp 80; 120 allow tcp 443; 130 allow tcp 22 from 10.20.5.128/27;
140 allow tcp 1024-65535 from 10.20.0.0/22 (replies from app). Default deny.
Outbound: 100 allow tcp 8000 to 10.20.0.0/22; 110 allow tcp 1024-65535 to 0.0.0.0/0 (replies to clients). Default deny.

A NACL is stateless, so a reply is a new packet judged on its own and needs its own rule (ephemeral ports 1024-65535).
Rules run lowest number first and the first match wins, so the 198.51.100.0/24 deny is rule 100, below the web allows
at 110/120; otherwise that range would still reach ports 80/443.
Side effect of the required reply rule: outbound TCP 8000 to any address is also allowed by rule 110 (8000 is in 1024-65535).

Checked with my own `tools/nacl_eval.py` (not the instructor's `nacl_sim.py`, which I do not have here).
