import pandas as pd
import numpy as np
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

def add_cite(df):
    print('start adding citation!')
    # use reference field
    for i, row in tqdm(df.iterrows(), total=len(df)):
        ref = row.references
        if not isinstance(ref, list) and ref != 0:
            ref = eval(ref)
        if ref == None or ref == [] or ref == 0: 
            continue
        ref_papers = Paper.objects.filter(arxiv_id__in=ref)
        og_paper = Paper.objects.get(arxiv_id=row.arxiv_id)
        og_paper.cite_to.add(*ref_papers)
    print('finish adding citation!')


if __name__ == '__main__':
    # csv
    df = pd.read_csv('merged.csv')
    df.cc = df.cc.fillna(0)
    df.rc = df.rc.fillna(0)
    df.references = df.references.fillna(0)
    df.citations = df.citations.fillna(0)
    # add_entries(df)
    add_cite(df)