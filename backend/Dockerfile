FROM python:3.10-slim

ARG BRAVE_API
ARG GROK_API
ENV BRAVE_API=${BRAVE_API}
ENV GROK_API=${GROK_API}

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD "sh -c cd src; fastapi run server.py"