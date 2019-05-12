# Use an official Python runtime as a parent image
FROM python:3.6

ENV KUBERNETES_SERVICE_HOST=paas.psi.redhat.com \
  KUBERNETES_SERVICE_PORT=443 \
  ENV_PLUGIN_CONFIG_FILE=package-build-controller/plugins/tensorflow_config.json \
  JOB_BACKOFF_LIMIT=3

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY package-build-controller /app/package-build-controller

# Install any needed packages
RUN pip3 install requests pybloom-mirror "kubernetes<9.0.0,>=8.0.0" openshift

# Run app.py when the container launches
CMD ["python3", "package-build-controller/controller.py"]
