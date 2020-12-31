import pandas as pd
import datetime, requests, json
import os
from datetime import date
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "backend.settings")

django.setup()

from esra_backend.models import *


def add_papers(df):
    cols = ['paper_title', 'abstract', 'arxiv_id', 'mag_id', 
        'citation_count', 'publish_date', 'jornal_name', 'conference']
    papers = df[cols]
    papers_list = papers.to_dict('records')
    paper_ids = dict()

    for paper in papers_list:
        p = Paper.objects.create(**paper)
        paper_ids[p.paper_title] = p.paper_id
    
    print('Paper yay')
    return paper_ids

def get_paper_ids():   
    papers = Paper.objects.all().values('paper_id','paper_title')
    paper_ids = {paper['paper_title']:paper['paper_id'] for paper in papers}
    return paper_ids

def add_author(authors_data):
    author_ids = dict()
    for author in authors_data:
        a = Author.objects.create(**author)
        author_ids[a.author_name] = a.author_id
    print('Author yay')
    return author_ids

def get_author_ids():
    authors = Author.objects.all().values('author_id', 'author_name')
    author_ids = {author['author_name']:author['author_id'] \
                  for author in authors}
    return author_ids

def add_affiliation(affiliations_data):
    aff_ids = dict()
    for aff in affiliations_data:
        a = Affiliation.objects.create(**aff)
        aff_ids[a.affiliation_name] = a.affiliation_id
    print('Affiliation yay')
    return aff_ids

def get_affiliation_ids():
    affs = Affiliation.objects.all().values('affiliation_id', 'affiliation_name')
    aff_ids = {aff['affiliation_name']:aff['affiliation_id'] \
               for aff in affs}
    
    return aff_ids

def add_paper_relation(
    paper_relations, 
    paper_ids, 
    author_ids,
    affiliation_ids
    ):
    for title, relations in paper_relations.items():
        print(title) # 
        pid = paper_ids[title]
        for relation in relations:
            author_name, affiliation_name = relation
            auid = author_ids[author_name]
            affid = None
            if affiliation_name != None:
                affid = affiliation_ids[affiliation_name]
            data = {
                "paper": Paper.objects.get(pk=pid),
                "author": Author.objects.get(pk=auid),
                "affiliation": Affiliation.objects.get(pk=affid)
            }
            en = PaperAuthorAffiliation.objects.create(**data)
    print("Success")
    return True

def get_paper_mag_ids():
    papers = Paper.objects.all().values('paper_id','mag_id')
    paper_mag_ids = {
        paper['mag_id']:paper['paper_id'] for paper in papers
    }
    return paper_mag_ids


def add_cite_relations(paper_mag_ids, citations):
    for paper_mag, cited_mag in citations.items():
        paper_id = paper_mag_ids[str(paper_mag)]
        print(paper_id) # 
        p = Paper.objects.get(pk=paper_id)
        for cited_paper_mag in cited_mag:
            cited_paper_id = paper_mag_ids.get(str(cited_paper_mag), None)
            # print(cited_paper_id)
            if cited_paper_id is not None:
                p.cite_to.add(
                    Paper.objects.get(pk=cited_paper_id)
                )
    return True


def re_assing_relations(paper_relations):
    paper_ids = get_paper_ids()
    author_ids = get_author_ids()
    affiliation_ids = get_affiliation_ids()
    add_paper_relation(
        paper_relations=paper_relations,
        paper_ids=paper_ids,
        author_ids=author_ids,
        affiliation_ids=affiliation_ids
    )

if __name__ == "__main__":
    

    df = pd.read_csv('cscl-cleaned-2020-12-29.csv')
    df = df.rename(columns={
        'authors_affitiation': 'authors_affiliation',
        'title': 'paper_title',
        'conference_name': 'conference'
    })

    df.authors_affiliation = df.authors_affiliation.apply(lambda x: eval(x))
    df.RId = df.RId.fillna('[]')
    df.RId = df.RId.apply(lambda x: eval(x))
    # df['conference'] = 'IDK Con'


    # authors & affiliations
    cols = ['paper_title', 'authors_affiliation']
    author_set = set()
    affiliation_set = set()
    paper_relations = dict()

    for index, row in df[cols].iterrows():
        title = row['paper_title']
        for relation in row['authors_affiliation']:
            author_name = relation['AuN']
            affiliation_name = relation.get('AfN', '')
            author_set.add(author_name)
            affiliation_set.add(affiliation_name)
            if title not in paper_relations:
                paper_relations[title] = []
            paper_relations.get(title, []).append(
                (author_name, affiliation_name,)
            )
    authors_data = [{'author_name':name} for name in author_set]
    affiliations_data = [{'affiliation_name':name} for name in affiliation_set]
    

    # papers 
    paper_ids = add_papers(df)
    author_ids = add_author(authors_data)
    affiliation_ids = add_affiliation(affiliations_data)
    add_paper_relation(
        paper_relations=paper_relations,
        paper_ids=paper_ids,
        author_ids=author_ids,
        affiliation_ids=affiliation_ids
    )

    # re-assign
    # re_assing_relations(paper_relations)

    # Citations 
    cite_cols = ['mag_id', 'RId']
    cite_df =  df[cite_cols]
    citations = {
        row['mag_id']:row['RId'] for _,row in cite_df.iterrows()
    }
    paper_mag_ids = get_paper_mag_ids()
    print(
        add_cite_relations(paper_mag_ids,citations)
    )
    # print(paper_mag_ids)