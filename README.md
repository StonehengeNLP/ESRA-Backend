# ESRA-Backend

## Elastic Search
1. Create directory
```mkdir elasticsearch-library```
2. Download elasticsearch based-on your system to that directory [ https://www.elastic.co/downloads/elasticsearch ]
3. Extract file
```tar -xzf elasticsearch-5.1.1.tar.gz```
4. Get in to directory
```cd elasticsearch-library```
5. To start elasticsearch server run this command:
```./elasticsearch-5.1.1/bin/elasticsearch```


## Enviroment
This project use Django framework(port:8000) connect with MySQL database(port:3306). In order to run the project, you need to create .env file (you can look the example at .env.example).

## Administrator
In order to create super user of Django, run this command:

```
python manage.py createsuperuser
```

Then put your username, email, and password respectively. You can access the admin at ```localhost:8000/admin``` after runthe project.

## Run the project
Run the following command:

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Using shell
```
python manage.py shell
```
