"""
Simple TCP Load Balancer
========================
A minimal load balancer with two ports:
- Config port (8080): REST API to update backend hosts
- App port (9000): TCP proxy that round-robins to backends
"""

import asyncio
import os
from typing import List
from fastapi import FastAPI
from uvicorn.config import Config
from uvicorn.server import Server

# Configuration from environment variables
CONFIG_PORT = 9999
SOURCE_PORT = int(os.getenv("SOURCE_PORT", "9000"))
TARGET_PORT = int(os.getenv("TARGET_PORT", "8000"))

app = FastAPI()

# Shared state
backends: List[str] = []
current_index = 0


@app.post("/config")
async def update_config(hosts: List[str]):
    """
    Update backend hosts. Format: ["host1", "host2", ...]
    Example: ["backend1.local", "backend2.local"]
    All backends use TARGET_PORT from environment.
    """
    global backends
    backends.clear()
    backends.extend(hosts)
    return {"status": "updated", "backends": hosts, "target_port": TARGET_PORT}


@app.get("/config")
async def get_config():
    """Get current backend configuration"""
    return {"backends": backends, "target_port": TARGET_PORT}


def get_next_backend():
    """Get next backend hostname using round-robin"""
    global current_index

    if not backends:
        return None

    backend = backends[current_index]
    current_index = (current_index + 1) % len(backends)
    return backend


async def proxy_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Proxy a single TCP connection to a backend"""
    host = get_next_backend()

    if not host:
        writer.close()
        await writer.wait_closed()
        return

    try:
        # Connect to backend using TARGET_PORT
        backend_reader, backend_writer = await asyncio.open_connection(
            host, TARGET_PORT
        )

        # Bidirectional relay
        async def forward(src, dst):
            try:
                while True:
                    data = await src.read(8192)
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
            finally:
                dst.close()
                await dst.wait_closed()

        # Run both directions concurrently
        await asyncio.gather(
            forward(reader, backend_writer),
            forward(backend_reader, writer),
            return_exceptions=True,
        )

    finally:
        writer.close()
        await writer.wait_closed()


async def run_tcp_server(port: int):
    """Run the TCP proxy server"""
    server = await asyncio.start_server(proxy_connection, "0.0.0.0", port)
    print(f"TCP proxy listening on port {port} (SOURCE_PORT)")
    print(f"Forwarding to backends on port {TARGET_PORT} (TARGET_PORT)")

    async with server:
        await server.serve_forever()


async def run_fastapi(port: int):
    """Run FastAPI config server asynchronously"""
    config = Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = Server(config)
    await server.serve()


async def main():
    """Start both servers concurrently"""
    print(f"Config API listening on port {CONFIG_PORT}")
    print(f"Send POST to http://localhost:{CONFIG_PORT}/config")
    print()

    # Run both servers concurrently
    await asyncio.gather(run_fastapi(CONFIG_PORT), run_tcp_server(SOURCE_PORT))


if __name__ == "__main__":
    asyncio.run(main())
