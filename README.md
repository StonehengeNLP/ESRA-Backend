# ESRA-Backend

## Enviroment
This project use Django framework(port:8000) connect with MySQL database(port:3306). In order to run the project, you need to create .env file (you can look the example at .env.example).

## Administrator
In order to create super user of Django, run this command:

``` python manage.py createsuperuser ```

Then put your username, email, and password respectively. You can access the admin at ```localhost:8000/admin``` after runthe project.

## Run the project
Run the following command:

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Using shell
``` python manage.py shell ```
