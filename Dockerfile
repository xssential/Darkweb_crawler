FROM ubuntu:22.04

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y curl wget vim
RUN apt-get install -y python3 python3-pip python3-dev libssl-dev libffi-dev build-essential
RUN apt install -y net-tools openssh-server
RUN apt-get install libcapstone-dev -y
RUN python3 -m pip install --upgrade pip
RUN apt install -y tor 
RUN echo "SocksPort 9050" >> /etc/tor/torrc
RUN echo "ControlPort 9051" >> /etc/tor/torrc
RUN echo "CookieAuthentication 1" >> /etc/tor/torrc

COPY ./requirements.txt /app/requirements.txt
COPY ./app/ /app/

WORKDIR /app/

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y tzdata
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get install -y cron
RUN echo "0 9,21 * * * python3 /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/tor_py
RUN chmod 0644 /etc/cron.d/tor_py
RUN crontab /etc/cron.d/tor_py

RUN pip install opencv-python
RUN pip3 install -r /app/requirements.txt

RUN apt install -y tesseract-ocr
RUN apt install -y libtesseract-dev
RUN playwright install
RUN playwright install-deps


EXPOSE 9050 9051

CMD service tor start && cron && tail -F /var/log/mysql/error.log && ["bash"]