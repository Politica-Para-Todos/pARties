FROM alpine:3.6

WORKDIR /parties

#########################################
## Install Requirements
#########################################
RUN apk add --no-cache \
        python3 \
        python3-dev \
        build-base \
        uwsgi \
        uwsgi-python3 \
        nginx \
        supervisor


########################################
## Install requirements
########################################

COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN rm requirements.txt

########################################
## Configure host
########################################

RUN rm /etc/nginx/nginx.conf

COPY server_conf/nginx.conf /etc/nginx/nginx.conf
COPY server_conf/uwsgi.ini /parties/
COPY server_conf/supervisor.ini /etc/supervisor.d/supervisor.ini

########################################
## Create the file structure and copy
########################################

RUN mkdir host
RUN mkdir engine
RUN mkdir data

COPY run.py .
COPY data/ data/

##########################################
## Entrypoint for the container
##########################################
CMD ["supervisord", "-n"]
