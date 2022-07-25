from django.urls import path

from .views import *

app_name = "papers_app"

urlpatterns = [
    path('register/', UserCreation.as_view(), name='user_register'),
    path('user_details/', UserDetails.as_view(), name='user_details'),
    path('subjects/', get_subjects_list, name='subjects_list'),
    path('questions/', QuestionApiView.as_view(), name='questions'),
    path('test_papers_list_checker/', TestPaperSetterSubmission.as_view(), name='test_papers_list_checker'),
    path('checker_test_approval/', TestPaperCheckerAcception.as_view(),
        name='checker_test_approval'),
]
