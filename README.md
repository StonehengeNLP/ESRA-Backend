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
This project use Django framework(port:8000) connect with MySQL database(port:3306). In order to run the project, you need to create .env file (you can look the example at .env.example).

## Administrator
In order to create super user of Django, run this command:

```
python manage.py createsuperuser
```

Then put your username, email, and password respectively. You can access the admin at ```localhost:8000/admin``` after runthe project.

## Run the project with elascticsearch

After  you clone the project, please copy file from:

```./synonyms/synonyms.txt``` (project directory) into ```./elasticsearch-{version}/config/analysis``` (elasticsearch directory)

Run the following command:
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
