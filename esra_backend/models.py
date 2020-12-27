from django.db import models

# Create your models here.

class Paper(models.Model):
    paper_id = models.AutoField(primary_key=True,null=False)
    paper_title = models.CharField(max_length=512,null=False)
    conference = models.CharField(max_length=512,null=False)
    arxiv_id = models.CharField(max_length=32,null=False)
    mag_id = models.CharField(max_length=12,null=False)
    citation_count = models.IntegerField(null=False)
    publish_date = models.DateField(null=False)
    abstract = models.TextField(null=True)
    cite_to = models.ManyToManyField('self', symmetrical=False, null=True, blank=True)

class Author(models.Model):
    author_id = models.AutoField(primary_key=True,null=False)
    author_name = models.CharField(max_length=512,null=False)
    paper = models.ManyToManyField(Paper)
    

class Affiliation(models.Model):
    affiliation_id = models.AutoField(primary_key=True,null=False)
    affiliation_name = models.CharField(max_length=256,null=False)
    author = models.ManyToManyField(Author)

# class Citation(models.Model):
#     citation_id = models.AutoField(primary_key=True,null=False)
#     cite_paper = models.ForeignKey(Paper,on_delete=models.CASCADE)
#     cited_paper_id = models.IntegerField(null=False)