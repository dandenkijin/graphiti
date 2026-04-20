#!/usr/bin/env python3
"""
Simple healthcheck performance benchmark.
Run this script to measure the time penalty of the healthcheck endpoint.
"""

import asyncio
import time
import statistics
import httpx
from typing import List


async def measure_healthcheck_latency(url: str, count: int = 100) -> List[float]:
    """Measure healthcheck endpoint latency over multiple requests."""
    latencies = []
    
    async with httpx.AsyncClient() as client:
        for i in range(count):
            start_time = time.perf_counter()
            try:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    end_time = time.perf_counter()
                    latency = (end_time - start_time) * 1000  # Convert to milliseconds
                    latencies.append(latency)
                else:
                    print(f"Request {i+1} failed with status {response.status_code}")
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.01)
    
    return latencies


def print_statistics(latencies: List[float]):
    """Print detailed statistics for the latency measurements."""
    if not latencies:
        print("No successful requests measured")
        return
    
    print(f"\nHealthcheck Performance Statistics ({len(latencies)} requests)")
    print("=" * 60)
    print(f"Mean latency:     {statistics.mean(latencies):.2f} ms")
    print(f"Median latency:   {statistics.median(latencies):.2f} ms")
    print(f"Min latency:      {min(latencies):.2f} ms")
    print(f"Max latency:      {max(latencies):.2f} ms")
    print(f"Std deviation:    {statistics.stdev(latencies):.2f} ms")
    print(f"95th percentile:  {sorted(latencies)[int(len(latencies) * 0.95)]:.2f} ms")
    print(f"99th percentile:  {sorted(latencies)[int(len(latencies) * 0.99)]:.2f} ms")


async def main():
    """Run the healthcheck performance benchmark."""
    urls = [
        "http://localhost:8000/healthcheck",  # Graph Service
    ]
    
    print("Healthcheck Performance Benchmark")
    print("Note: Make sure the services are running before executing this script")
    print()
    
    for url in urls:
        print(f"Testing: {url}")
        try:
            latencies = await measure_healthcheck_latency(url, count=50)
            print_statistics(latencies)
        except Exception as e:
            print(f"Failed to test {url}: {e}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
