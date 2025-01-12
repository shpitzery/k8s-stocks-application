FROM python:3.11-alpine3.20

# Copy the requirements.txt file and the application code to the Docker container. If the directory does not exist, it will be created.
COPY requirements.txt /app/ 
COPY app.py /app/

# Set the working directory in the Docker container.
WORKDIR /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PORT=8000

# Expose the port on which the Flask application will run (the container port)
EXPOSE 8000

# Start the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]