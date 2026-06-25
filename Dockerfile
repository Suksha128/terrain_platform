FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user specifically for Hugging Face Spaces (User 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy requirement and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY --chown=user . .

# Ensure the entrypoint script is executable
RUN chmod +x entrypoint.sh

# Expose Streamlit port
EXPOSE 7860

# Run the entrypoint
CMD ["./entrypoint.sh"]
