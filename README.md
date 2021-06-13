# ESRA-Backend

## Elastic Search
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

Then put your username, email, and password respectively. You can access the admin at ```localhost:8000/admin``` after runthe project.

## Run the project with elascticsearch

After  you clone the project, please copy file from:

```./synonyms/synonyms.txt``` (project directory) into ```./elasticsearch-{version}/config/analysis``` (elasticsearch directory)

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

We use gunicorn for serving our backend application. First install gunicorn(this is not fix, pick any that suite your liking) then run the following command:

```
gunicorn --bind 0.0.0.0:8000 --workers 8 backend.wsgi
```

This command will create 8 workers and binded at port 8000

## Docker image

The docker image of this project is publicly available at backgroundboy/esra-backend dockerhub repository. The image requires an environment variable **ELASTICSEARCH_HOST** for the name of external elasticsearch host in order to connenect and run.
