import time
import os
import psutil

# OpenTelemetry Imports
from opentelemetry import metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)

# Try to import the gRPC exporter; fall back to console if unavailable.
try:
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

# 1. IDENTIFY OURSELVES (The "Resource")
resource = Resource.create({
    "service.name": "ubuntu-demo-app",
    "host.name": "ubuntu-vm-1"
})

# 2. SETUP THE EXPORTER
endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
if GRPC_AVAILABLE:
    print(f"Sending metrics to OTel Collector via gRPC at: {endpoint}")
    exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
else:
    print("gRPC exporter not available, using console exporter.")
    exporter = ConsoleMetricExporter()

# 3. SETUP THE READER & PROVIDER
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader], resource=resource)
metrics.set_meter_provider(provider)

# 4. CREATE OUR METRICS (Instruments) & 5. FETCH REAL SERVER DATA
meter = metrics.get_meter("vm-simulator")

def get_cpu_info(options):
    cpu_percent = psutil.cpu_percent(interval=None)
    yield metrics.Observation(cpu_percent)

def get_mem_info(options):
    memory_info = psutil.virtual_memory()
    mem_mb = memory_info.used / (1024 * 1024)
    yield metrics.Observation(mem_mb)

cpu_gauge = meter.create_observable_gauge(
    name="cpu_usage_percentage",
    callbacks=[get_cpu_info],
    description="Real CPU usage percentage",
)

mem_gauge = meter.create_observable_gauge(
    name="memory_usage_mb",
    callbacks=[get_mem_info],
    description="Real memory usage in megabytes",
)

# 6. KEEP THE APP RUNNING
if __name__ == "__main__":
    print("Ubuntu VM Simulator Started! Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping simulator...")
