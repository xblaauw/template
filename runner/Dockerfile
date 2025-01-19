FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Install Jupyter dependencies
RUN pip install ipykernel jupyter

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x run.sh

CMD ["bash", "run.sh"]