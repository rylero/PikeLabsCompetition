FROM python:3.10-slim

ARG TAVILY_API_KEY
ARG GROK_API
ENV TAVILY_API_KEY=${TAVILY_API_KEY}
ENV GROK_API=${GROK_API}

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT 8000
EXPOSE 8000

RUN mkdir data
RUN chmod +x start.sh

CMD ["./start.sh"]
