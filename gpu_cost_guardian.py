#!/usr/bin/env python3
"""
GPU Cost Guardian - Final upgraded local version
- Simulation mode (safe)
- Prometheus metrics at :8000
- Dry-run by default
"""
import time
import subprocess
from datetime import datetime
from prometheus_client import start_http_server, Gauge, Counter

# Prometheus metrics
gpu_idle_count = Gauge("gpu_idle_count", "Number of GPUs currently idle")
gpu_savings_usd_total = Gauge("gpu_savings_usd_total", "Estimated USD saved per hour (current session)")
gpu_kill_events_total = Counter("gpu_kill_events_total", "Total number of GPU kill events (simulated)")

class GPUCostGuardian:
    def __init__(self, dry_run=True, utilization_threshold=5):
        self.dry_run = dry_run
        self.utilization_threshold = utilization_threshold
        self.total_savings = 0.0
        self.gpu_cost_per_hour = 3.06

    def check_gpu_availability(self):
        try:
            r = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False

    def get_gpu_status(self):
        # Try to read nvidia-smi; if not present, return empty list to trigger simulation
        gpus = []
        try:
            r = subprocess.run([
                'nvidia-smi',
                '--query-gpu=index,utilization.gpu,memory.used,memory.total,temperature.gpu,name',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                for line in r.stdout.strip().split('\n'):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 5:
                        g = {
                            'id': parts[0],
                            'utilization': int(parts[1]),
                            'memory_used': int(parts[2]),
                            'memory_total': int(parts[3]),
                            'temperature': int(parts[4]),
                            'name': parts[5] if len(parts) > 5 else 'Unknown'
                        }
                        gpus.append(g)
        except Exception:
            pass
        return gpus

    def should_kill_gpu(self, gpu):
        return (gpu['utilization'] < self.utilization_threshold and gpu['memory_used'] < 1024)

    def kill_gpu(self, gpu_id):
        # Simulation / dry-run increments counter only
        if self.dry_run:
            print(f"💀 [SIMULATION] Would kill GPU {gpu_id}")
            gpu_kill_events_total.inc()
            return True
        try:
            r = subprocess.run(['nvidia-smi', '-i', str(gpu_id), '-gpu-reset'], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                print(f"✅ Reset GPU {gpu_id}")
                gpu_kill_events_total.inc()
                return True
            else:
                print(f"❌ Failed reset GPU {gpu_id}: {r.stderr.strip()}")
                return False
        except Exception as e:
            print(f"❌ Error resetting GPU {gpu_id}: {e}")
            return False

    def calculate_savings(self, gpus_killed):
        hourly = gpus_killed * self.gpu_cost_per_hour
        monthly = hourly * 24 * 30
        return hourly, monthly

    def run_simulation(self):
        # Simulation used when no real GPUs available
        print("🔍 Running simulation with 4 virtual GPUs...")
        simulated = [
            {'id': 0, 'utilization': 85, 'memory_used': 12000, 'status':'ACTIVE'},
            {'id': 1, 'utilization': 3, 'memory_used': 512, 'status':'IDLE'},
            {'id': 2, 'utilization': 92, 'memory_used': 14000, 'status':'ACTIVE'},
            {'id': 3, 'utilization': 2, 'memory_used': 256, 'status':'IDLE'},
        ]
        killed = 0
        idle_count = 0
        for g in simulated:
            print(f"   GPU {g['id']}: {g['utilization']}% util, {g['memory_used']}MB - {g['status']}")
            if g['utilization'] < self.utilization_threshold and g['memory_used'] < 1024:
                self.kill_gpu(g['id'])
                killed += 1
                idle_count += 1
        gpu_idle_count.set(idle_count)
        if killed > 0:
            hourly, monthly = self.calculate_savings(killed)
            self.total_savings += hourly
            gpu_savings_usd_total.set(self.total_savings)
            print(f"💰 This run: ${hourly:.2f}/hour | Total: ${self.total_savings:.2f}")
            print(f"📈 Monthly projection: ${monthly:.2f}")
        else:
            print("✅ No idle GPUs found")

    def run_check(self):
        print(f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking GPUs...")
        if not self.check_gpu_availability():
            print("❌ No NVIDIA GPU detected - running simulation")
            self.run_simulation()
            return
        gpus = self.get_gpu_status()
        if not gpus:
            print("❌ Could not read GPU status - running simulation")
            self.run_simulation()
            return
        print(f"📊 Found {len(gpus)} GPU(s):")
        killed = 0
        idle = 0
        for gpu in gpus:
            status = "IDLE" if self.should_kill_gpu(gpu) else "ACTIVE"
            print(f"   GPU {gpu['id']}: {gpu['utilization']}% util, {gpu['memory_used']}MB - {status}")
            if self.should_kill_gpu(gpu):
                if self.kill_gpu(gpu['id']):
                    killed += 1
                    idle += 1
        gpu_idle_count.set(idle)
        if killed > 0:
            hourly, monthly = self.calculate_savings(killed)
            self.total_savings += hourly
            gpu_savings_usd_total.set(self.total_savings)
            print(f"💰 This run: ${hourly:.2f}/hour | Total: ${self.total_savings:.2f}")
            print(f"📈 Monthly projection: ${monthly:.2f}")
        else:
            print("✅ No idle GPUs found")

def main():
    start_http_server(8000)
    print("🚀 GPU Cost Guardian - Final (metrics at http://localhost:8000/metrics)")
    print("⚠️ Running in DRY RUN mode (no destructive actions)")
    guardian = GPUCostGuardian(dry_run=True)
    try:
        while True:
            guardian.run_check()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")

if __name__ == "__main__":
    main()
