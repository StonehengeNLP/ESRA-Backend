from django.db import models
import uuid

# Create your models here.

class Paper(models.Model):
    paper_id = models.AutoField(primary_key=True,null=False)
    paper_title = models.CharField(max_length=512,null=False)
    conference = models.CharField(max_length=512,null=False)
    arxiv_id = models.CharField(max_length=32,null=False)
    mag_id = models.CharField(max_length=12,null=False)
    citation_count = models.IntegerField(null=False)
    publish_date = models.DateField(null=False)

class Author(models.Model):
    author_id = models.AutoField(primary_key=True,null=False)
    author_name = models.CharField(max_length=512,null=False)
    

class WriteEntity(models.Model):
    class Meta:
        unique_together = (('paper', 'author'),)

    paper = models.ForeignKey(Paper,on_delete=models.CASCADE,primary_key=True)
    author = models.ForeignKey(Author,on_delete=models.CASCADE)

class Affiliation(models.Model):
    class Meta:
        unique_together = (('author', 'affiliation_name'),)

    author = models.ForeignKey(Author,on_delete=models.CASCADE,primary_key=True)
    affiliation_name = models.CharField(max_length=256,null=False)

class Citation(models.Model):
    class Meta:
        unique_together = (('cite_paper', 'cited_paper_id'),)

    cite_paper = models.ForeignKey(Paper,on_delete=models.CASCADE,primary_key=True)
    cited_paper_id = models.IntegerField(null=False)