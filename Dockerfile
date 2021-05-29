FROM python:3.9-alpine

WORKDIR /usr/src/app

ADD requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

ADD . .

RUN mkdir data

CMD ["python", "./run.py"]
