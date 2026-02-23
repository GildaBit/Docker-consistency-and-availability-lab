FROM python:3.12-slim

# Create a owrking directory 
WORKDIR /app

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set working directory to src
WORKDIR /app/src

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]