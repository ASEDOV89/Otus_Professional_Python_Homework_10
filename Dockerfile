FROM python:3.12-slim

RUN apt-get update && apt-get install -y build-essential

WORKDIR /app

COPY requirements.txt .
COPY entrypoint.sh .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --upgrade setuptools
RUN pip install --no-cache-dir --upgrade python-jose
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "entrypoint.sh"]


#FROM python:3.12-slim
#
#RUN apt-get update && apt-get install -y build-essential
#
#WORKDIR /app
#
#COPY . /app
#
#RUN pip install --no-cache-dir --upgrade pip
#RUN pip install --no-cache-dir --upgrade setuptools
#RUN pip install --no-cache-dir -r requirements.txt
#
#RUN chmod +x entrypoint.sh
#
#EXPOSE 8000
#
#ENTRYPOINT ["sh", "entrypoint.sh"]
