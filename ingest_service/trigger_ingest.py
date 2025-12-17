
import sys
import os
import asyncio

# Ensure ingest_service is in path
sys.path.append(os.path.join(os.getcwd(), 'ingest_service'))

# Set env vars if needed (defaults are usually localhost:8086)
# os.environ["INFLUX_URL"] = "http://localhost:8086"

try:
    from main import startup_event
except ImportError:
    # Try importing as package
    from ingest_service.main import startup_event

async def main():
    print("Triggering startup_event manually...")
    await startup_event()
    print("Finished startup_event.")

if __name__ == "__main__":
    asyncio.run(main())
