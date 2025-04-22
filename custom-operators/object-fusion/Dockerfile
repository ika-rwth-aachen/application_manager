FROM python:3.12
# Install Helm
RUN apt-get update && \
    apt-get install -y curl && \
    curl -s https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
ADD ./requirements.txt /tmp/requirements.txt
RUN pip install -r ./tmp/requirements.txt
ADD ./operator /operator
ADD ./operator/config.yml /config/config.yml
CMD kopf run /operator/object_fusion_operator.py