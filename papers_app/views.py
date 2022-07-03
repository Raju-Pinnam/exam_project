from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth import get_user_model

from .models import Question, Answer, TestPaper

User = get_user_model()


class QuestionCreationUpdate(View):
    """
    Basic View to create 
    """
    
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("id")
        
    
