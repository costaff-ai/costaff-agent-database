FROM python:3.12-slim

WORKDIR /app

# TODO: Add any system-level dependencies your MCP server needs.
# Example: fonts-noto-cjk for CJK font support (used by viz-report-agent)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# TODO: Update this port if your MCP server uses a different one
EXPOSE 8082

CMD ["python", "server.py"]
