# Use pinned AWS Lambda Python 3.12 base image (Amazon Linux 2023)
FROM public.ecr.aws/lambda/python:3.12

# Install system dependencies needed for OpenCV and image processing
RUN dnf install -y \
    gcc gcc-c++ make cmake git wget tar gzip \
    libX11-devel libXrandr libXinerama libXcursor \
    libSM libICE \
    mesa-libGL mesa-libGLU libpng zlib \
    && dnf clean all

# Copy requirements file and install Python packages into Lambda task root
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy your Lambda function code into the container
COPY app.py ${LAMBDA_TASK_ROOT}

# Set the Lambda handler
CMD ["app.lambda_handler"]
