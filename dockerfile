# Start from AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# Install system dependencies for OpenCV
RUN yum update -y && yum install -y \
    gcc gcc-c++ make cmake git wget tar gzip \
    libX11-devel libXrandr libXinerama libXcursor \
    libSM libICE \
    mesa-libGL mesa-libGLU libpng zlib \
    && yum clean all

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy Lambda function code
COPY app.py ${LAMBDA_TASK_ROOT}

# Lambda handler
CMD ["app.lambda_handler"]
