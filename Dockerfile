FROM python:3.11-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies using uv
RUN uv sync --frozen

# Expose port
EXPOSE 8080

# Run the application
CMD ["uv", "run", "python", "app.py"]