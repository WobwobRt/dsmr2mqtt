FROM python:3.15-alpine
WORKDIR /opt/dsmr2mqtt
COPY requirements.txt requirements.txt
# RUN pip install --root-user-action ignore --no-cache-dir -r requirements.txt

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

RUN rm requirements.txt

COPY *.py .
ARG VERSION_TAG=0.4
ENV DSMR2MQTT_VERSION=$VERSION_TAG
HEALTHCHECK --interval=10s --start-period=5s --retries=3 \
  CMD pgrep -f python > /dev/null || exit 1
CMD [ "env", "SERIAL_DEVICE=/dev/ttyDSMR", "./dsmr2mqtt.py" ]
