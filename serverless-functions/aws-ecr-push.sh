# the only argument is the name of the image
# this should match the name you put in your Parameters section of ml-streaming-pipeline.yaml
# Build the docker image
docker build -t  ${1} .

# Create a ECR repository
aws ecr create-repository --repository-name ${1} --image-scanning-configuration scanOnPush=true --region ${AWS_REGION}

# Tag the image to match the repository name
docker tag ${1}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${1}:latest

# Register docker to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Push the image to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${1}:latest