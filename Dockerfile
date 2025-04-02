FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install tensorflow==2.18.1
RUN pip install --no-cache-dir -r requirements.txt

# tensorflow==2.18.1

COPY . .

CMD [ "python", "./train.py" ]
