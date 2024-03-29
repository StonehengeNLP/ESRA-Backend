# ESRA-Backend
This repository is for the backend of ESRA using Django connect with Elasticsearch.

## Repository Struture

```
[backend]
    ├── settings.py     :   setting port, host, database, and etc from django
    └── ...
[esra_backend]
    ├── documents.py    :   elasticsearch analyser and registry document
    ├── helps.py        :   elasticsearch query services
    ├── models.py       :   data model
    ├── serializer.py   :   data serializers
    ├── urls.py         :   api url lists 
    ├── views.py        :   api logics
    └── ...
[synonyms]
    ├── synonyms.py     :   create synonym.txt using embedding vector list of all entities
    └── synonyms.txt    :   file for put in elasticsearch for synonyms feature
.env                    :   enviroments same as in .env.example
new_seed.py             :   dumping items to database
requirements.txt        :   list of all libraries
DockerFile              :   for running with gunicorn
start.sh                :   for running with gunicorn
esra.sqlite3            :   our database file (download: https://bit.ly/35eEFLt)
...
```

## Elasticsearch
1. Create directory
```mkdir elasticsearch-library```
2. Download elasticsearch based-on your system to that directory [ https://www.elastic.co/downloads/elasticsearch ]
3. Extract file
```tar -xzf elasticsearch-{version}.tar.gz```
4. Get in to directory
```cd elasticsearch-library```
5. To start elasticsearch server run this command:
```./elasticsearch-{version}/bin/elasticsearch```

To use the synonym, please follow the instruction below in Run the project with elascticsearch section.


## Enviroment
In order to run the project, you need to create .env file (you can look the example at .env.example).

## Administrator
In order to create super user of Django, run this command:

```
python manage.py createsuperuser
```

Then put your username, email, and password respectively. You can access the admin at ```localhost:8000/admin``` after run the project.

## Run the project with elascticsearch

After  you clone the project, please follow the two steps before run the application:
1. Copy ```./synonyms/synonyms.txt``` (project directory) into ```./elasticsearch-{version}/config/analysis``` (elasticsearch directory).
2. Download a database file (https://bit.ly/35eEFLt) and add it to the project directory as shown in the repository struture.

Run the following commands:
```
python manage.py makemigrations
python manage.py migrate
python manage.py search_index --rebuild
python manage.py runserver
```

## Using shell
```
python manage.py shell
```

## Serve Django application

We use gunicorn for serving our backend application. First install gunicorn(this is not fixed, pick anything that suit your liking) then run the following command:

```
gunicorn --bind 0.0.0.0:8000 --workers 8 backend.wsgi
```

This command will create 8 workers and binded them at port 8000

## Docker image

The docker image of this project is publicly available at backgroundboy/esra-backend dockerhub repository. The image requires an environment variable **ELASTICSEARCH_HOST** for the name of external elasticsearch host in order to connenect and run.
