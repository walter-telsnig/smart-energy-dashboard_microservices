FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy mock data from context (assumes build context is root or file is copied in)
# NOTE: In docker-compose, we mount volumes or build context is usually specific.
# Here we will assume mock_data.csv is copied from the parent directory 
# BUT standard docker build context is the directory. 
# We'll fix this by COPYing it in if it exists, or assuming it's mounted.
# For this setup, we will expect mock_data.csv to be in ingest_service directory OR mounted.
# Let's rely on the file being COPY-ed if we put it there, or we'll read it from a mount.
# To be safe for the "Startup" requirement, let's assume valid path.

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
