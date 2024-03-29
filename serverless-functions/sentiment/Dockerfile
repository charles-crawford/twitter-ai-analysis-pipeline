ARG FUNCTION_DIR="/function/"

FROM huggingface/transformers-pytorch-cpu as build-image


# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Install aws-lambda-cpp build dependencies
RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev


# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

# Copy handler function
COPY *.py ${FUNCTION_DIR}

# Install the function's dependencies
RUN pip uninstall --yes jupyter
RUN pip install --target ${FUNCTION_DIR} awslambdaric
RUN pip install --target ${FUNCTION_DIR} sentencepiece protobuf boto3 scipy

FROM huggingface/transformers-pytorch-cpu

# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

ENTRYPOINT [ "python3", "-m", "awslambdaric" ]

# This will get replaced by the proper handler by the CDK script
CMD [ "sentiment.handler" ]