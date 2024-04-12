# Python image to use.
FROM python:3.12-alpine

# Set the working directory to /app
WORKDIR /app

# Install ffmpeg, libmagic, and other dependencies
RUN apk add --no-cache ffmpeg
RUN apk add --no-cache libmagic

# copy the requirements file used for dependencies
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the working directory contents into the container at /app
COPY . .

# Run app.py when the container launches
ENTRYPOINT ["python", "app.py"]
