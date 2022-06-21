FROM public.ecr.aws/amazonlinux/amazonlinux
FROM public.ecr.aws/lambda/python:3.8
COPY . ${LAMBDA_TASK_ROOT}
WORKDIR ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
CMD [ "stream.handler" ]