"""Local-only mixed authenticated HTTP load, no live database writes."""
import argparse
import asyncio
from collections import Counter
import json
import time
from contextlib import AsyncExitStack
from math import ceil
from pathlib import Path
from urllib.parse import urlsplit
import httpx


async def main(args):
    if urlsplit(args.url).hostname not in {"localhost", "127.0.0.1"}:
        raise SystemExit("This harness is restricted to localhost; use a reviewed staging load plan for remote tests")
    tokens = json.loads(Path("tmp/load-users.json").read_text())
    if args.users > len(tokens):
        raise SystemExit("Not enough synthetic identities")
    latencies, codes = [], Counter()
    active = peak = 0
    paths = ["/api/v1/auth/me", "/api/v1/opportunities?limit=20", "/api/v1/students/me/skills", "/api/v1/recommendations/opportunities"]
    started = time.perf_counter()
    # Shard the generator's connection pools to avoid quadratic pool scans at
    # 1000 connections. This changes generator overhead, not server limits.
    async with AsyncExitStack() as stack:
        shards = min(16, args.users)
        clients = [await stack.enter_async_context(httpx.AsyncClient(base_url=args.url, timeout=60,
            limits=httpx.Limits(max_connections=ceil(args.users/shards), max_keepalive_connections=ceil(args.users/shards)))) for _ in range(shards)]
        async def user(index):
            nonlocal active, peak
            if args.ramp:
                await asyncio.sleep(args.ramp * index / args.users)
            for turn in range(args.rounds):
                active += 1
                peak = max(peak, active)
                before = time.perf_counter()
                try:
                    response = await clients[index % shards].get(paths[(index + turn) % len(paths)], headers={"Authorization": "Bearer " + tokens[index]})
                    codes[str(response.status_code)] += 1
                except httpx.HTTPError as exc:
                    codes[type(exc).__name__] += 1
                finally:
                    latencies.append((time.perf_counter()-before)*1000)
                    active -= 1
                if args.think:
                    await asyncio.sleep(args.think)
        await asyncio.gather(*(user(i) for i in range(args.users)))
    elapsed = time.perf_counter() - started
    ordered = sorted(latencies)
    def percentile(p):
        return round(ordered[min(len(ordered)-1, int(len(ordered)*p))], 2)
    result = {"users": args.users, "rounds": args.rounds, "ramp_seconds": args.ramp,
        "think_seconds": args.think, "peak_in_flight": peak, "requests": len(latencies),
        "duration_seconds": round(elapsed, 2), "requests_per_second": round(len(latencies)/elapsed, 2),
        "p50_ms": percentile(.5), "p95_ms": percentile(.95), "p99_ms": percentile(.99),
        "statuses": dict(codes), "workload": paths,
        "scope": "Local synthetic authenticated read workload; excludes login bursts, uploads, WebSockets, Redis and WAN latency."}
    Path(args.output).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if codes.get("200", 0) != len(latencies):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8011")
    parser.add_argument("--users", type=int, default=1000)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--ramp", type=float, default=10)
    parser.add_argument("--think", type=float, default=1)
    parser.add_argument("--output", default="tmp/load-result.json")
    asyncio.run(main(parser.parse_args()))
