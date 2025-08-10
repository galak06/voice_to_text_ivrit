# Include Python
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

# Define your working directory
WORKDIR /

# Configure LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/nvidia/cudnn/lib:/opt/conda/lib/python3.11/site-packages/nvidia/cublas/lib"

# Install runpod
RUN pip install runpod
RUN pip install stable-ts==2.18.3

# Add your files
ADD main.py .
ADD infer.py .
ADD src/ ./src/

# Call your file when your container starts
CMD [ "python", "-u", "/main.py", "--serverless" ]

