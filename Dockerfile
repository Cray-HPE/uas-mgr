#########################
### Base
#########################
FROM python:3-slim as base

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY setup.py requirements.txt /usr/src/app/
COPY api/ swagger_server/ /usr/src/app/swagger_server/

RUN pip3 install --no-cache-dir -r requirements.txt

#########################
### Testing
#########################
FROM base as testing

COPY test-requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r test-requirements.txt
RUN mkdir -p /var/run/secrets/kubernetes.io/
COPY serviceaccount/ /var/run/secrets/kubernetes.io/serviceaccount/
ENTRYPOINT pytest --cov swagger_server

#########################
### Application
#########################
FROM base as application

EXPOSE 8080
ENTRYPOINT ["python3"]
CMD ["-m", "swagger_server"]
