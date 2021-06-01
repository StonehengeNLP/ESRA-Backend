# pull official base image
FROM python:3.8-slim

# set work directory
WORKDIR /usr/src/backend

EXPOSE 8000

# install dependencies
COPY ./requirements.txt .
RUN set -ex \
    && pip install --upgrade --no-cache-dir pip \
    && pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

EXPOSE 8000

CMD ["sh", "start.sh"]