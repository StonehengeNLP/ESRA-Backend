import pandas as pd
import datetime, pickle
import os
from datetime import date
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "backend.settings")

django.setup()

from esra_backend.models import *

# read csv 
df = pd.read_csv('.csv')


 