FROM python:3.14-alpine
WORKDIR /opt/dsmr2mqtt
COPY requirements.txt requirements.txt
# RUN pip install --root-user-action ignore --no-cache-dir -r requirements.txt

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

RUN rm requirements.txt

COPY *.py .
ARG VERSION_TAG=0.3
ENV DSMR2MQTT_VERSION=$VERSION_TAG
CMD [ "env", "SERIAL_DEVICE=/dev/ttyDSMR", "./dsmr2mqtt.py" ]
