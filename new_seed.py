import pandas as pd
import datetime, requests, json
import os
from datetime import date
import django
from tqdm import tqdm

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "backend.settings")

django.setup()

from esra_backend.models import *

def add_entries(df):
    print('start adding entries!')
    for i, row in tqdm(df.iterrows(), total=len(df)):
        # print(row.publish_date)
        p = Paper.objects.create(
            arxiv_id=row.arxiv_id,
            paper_title=row.title,
            citation_count=row.cc,
            publish_date=row.publish_date[:10],
            abstract=row.abstract
        )
        authors = row.authors_parsed
        if not isinstance(authors, list):
            authors = eval(authors)
        for author in authors:
            a, created = Author.objects.get_or_create(author_name=author)
            PaperAuthorAffiliation.objects.create(
                paper=p, author=a, affiliation=None
            )
    print('finish adding entries!')
            
if __name__ == '__main__':
    # csv
    df = pd.read_csv('merged.csv')
    df.cc = df.cc.fillna(0)
    df.rc = df.rc.fillna(0)
    add_entries(df)