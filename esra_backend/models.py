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

class Author(models.Model):
    author_id = models.AutoField(primary_key=True,null=False)
    author_name = models.CharField(max_length=512,null=False)
    

class WriteEntity(models.Model):
    write_id = models.AutoField(primary_key=True,null=False)
    paper = models.ForeignKey(Paper,on_delete=models.CASCADE)
    author = models.ForeignKey(Author,on_delete=models.CASCADE)

class Affiliation(models.Model):
    affiliation_id = models.AutoField(primary_key=True,null=False)
    author = models.ForeignKey(Author,on_delete=models.CASCADE)
    affiliation_name = models.CharField(max_length=256,null=False)

class Citation(models.Model):
    citation_id = models.AutoField(primary_key=True,null=False)
    cite_paper = models.ForeignKey(Paper,on_delete=models.CASCADE)
    cited_paper_id = models.IntegerField(null=False)