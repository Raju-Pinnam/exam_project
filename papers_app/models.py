from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Answer(models.Model):
    """
    Answer For Question For now i have added Only text base answer
    For this if you guys want add image answer or mutliple choises also
    """
    answer = models.TextField()
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Answer is for {self.question}"


class Subject(models.Model):
    """
    SUbject Name
    """
    subject_name = models.CharField(max_length=64)
    
    def __str__(self):
        return self.subject_name

class Question(models.Model):
    """
    Question For now i have given normal text Question
    if required we can add Multiple choise questions also
    if we delete subject then all related Questions and answers also deleted
    Question marks means Just how many marks this question will contains
    suppose 5 marks or 10 marks like this
    """
    question = models.CharField(max_length=256)
    creater = models.ForeignKey(User, on_delete=models.CASCADE)
    question_marks = models.IntegerField(default=0)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.question}-{self.subject}-{self.marks}"


class TestPaper(models.Model):
    """
    num_of_questions = total nuber of questions contains by this paper
    questions = One question can be in number of papers and one paper contains many questions
    total_marks = marks for this paper
    subject = for which subject belongs to this paper 
              if subject deleted then Test paper also be deleted
    setter = He is Lecturer
             if he is removed then Test paper also be deleted
    checker = 
    examiner 
    checker_review
    examiner review
    is_approved = Is finally paper approved or not
    """
    number_of_questions = models.IntegerField()
    questions = models.ManyToManyField(Question)
    total_marks = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    setter = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="set_papers")
    checker = models.ForeignKey(User, on_delete=models.DO_NOTHING,
                               related_name="checked_papers")
    examiner = models.ForeignKey(User, on_delete=models.DO_NOTHING,
                               related_name="examined_papers")
    checker_review = models.TextField()
    examiner_review = models.TextField()
    is_approved = models.BooleanField(default=False)

