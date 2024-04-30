# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /scheduler

# Copy the current directory contents into the container at /app
COPY myapp.py /scheduler/
COPY alert_files /scheduler/alert_files
COPY . /scheduler

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "myapp.py"]