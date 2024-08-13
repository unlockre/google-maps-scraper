FROM chetan1111/botasaurus:latest

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN python -m pip install -r requirements.txt

RUN mkdir app
WORKDIR /app
COPY . /app

# Set the KUBERNETES_SERVICE_HOST environment variable
ENV KUBERNETES_SERVICE_HOST=127.0.0.1

RUN python run.py install

ENTRYPOINT ["./scripts/startup.sh"]
