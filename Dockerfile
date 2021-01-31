# pull official base image
FROM python:3

# set work directory
WORKDIR /usr/src/backend

EXPOSE 8000

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

CMD python manage.py runserver 0.0.0.0:8000