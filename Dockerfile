FROM python:3.8-alpine

RUN pip install -U pip pymodbus
COPY ./pypoller.py /app/pypoller.py

ENTRYPOINT ["python3", "/app/pypoller.py"]
