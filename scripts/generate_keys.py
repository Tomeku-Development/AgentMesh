#!/usr/bin/env python3
"""Generate Ed25519 keypairs for MESH agents.

Usage:
    python scripts/generate_keys.py               # Generate 1 keypair
    python scripts/generate_keys.py --count 6     # Generate 6 keypairs
    python scripts/generate_keys.py --seed myseed # Deterministic from seed
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mesh.core.identity import AgentIdentity


def main():
    parser = argparse.ArgumentParser(description="Generate Ed25519 keypairs for MESH agents")
    parser.add_argument("--count", type=int, default=1, help="Number of keypairs to generate")
    parser.add_argument("--seed", type=str, default="", help="Deterministic seed (for reproducible keys)")
    parser.add_argument("--output", type=str, default="", help="Output file (JSON). Prints to stdout if empty")
    args = parser.parse_args()

    keys = []
    for i in range(args.count):
        if args.seed:
            seed_str = f"{args.seed}_{i}" if args.count > 1 else args.seed
            import hashlib
            seed_bytes = hashlib.sha256(seed_str.encode()).digest()
            identity = AgentIdentity.from_seed(seed_bytes)
        else:
            identity = AgentIdentity.generate()

        entry = {
            "agent_id": identity.agent_id,
            "public_key_hex": identity.public_key_hex,
            "seed_hex": identity.seed_hex(),
        }
        keys.append(entry)

    output = json.dumps(keys, indent=2) if args.count > 1 else json.dumps(keys[0], indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output + "\n")
        print(f"Written {args.count} keypair(s) to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
