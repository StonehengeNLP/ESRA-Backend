from django.db import models
import datetime

class Paper(models.Model):
    paper_id = models.AutoField(primary_key=True, null=False)
    paper_title = models.CharField(max_length=512, null=False)
    conference = models.CharField(max_length=512, null=True, blank=True)
    arxiv_id = models.CharField(max_length=32, null=False, unique=True)
    # mag_id = models.CharField(max_length=12, null=False)
    citation_count = models.IntegerField(null=False)
    publish_date = models.DateField(null=False)
    abstract = models.TextField(null=True)
    cite_to = models.ManyToManyField('self', symmetrical=False, null=True, blank=True)
    journal_name = models.CharField(max_length=512, null=True)

    class Meta:
        indexes = models.Index(fields=['arxiv_id'], name='arxiv_idx')

    @property
    def popularity(self):
        days_diff = datetime.date.today() - self.publish_date
        return self.citation_count/days_diff.days

class Author(models.Model):
    author_id = models.AutoField(primary_key=True, null=False)
    author_name = models.CharField(max_length=512, null=False)
    
class Affiliation(models.Model):
    affiliation_id = models.AutoField(primary_key=True, null=False)
    affiliation_name = models.CharField(max_length=256, null=False)

class PaperAuthorAffiliation(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    affiliation = models.ForeignKey(Affiliation, on_delete=models.CASCADE,
                                    null=True, blank=True)