from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.postgres.aggregates import ArrayAgg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView

from .models import Question, Answer, TestPaper, Profile, Subject
from .serializers import (SubjectSerializer, ProfileSerializer, QuestionSerializer,
QuestionDetailSerializer)

User = get_user_model()

class UserCreation(APIView):
    
    def post(self, request, *args, **kwargs):
        params = request.data
        if 'username' in params:
            username = params['username']
        else:
            return Response({"message": "User Name is required Value"},
            status=status.HTTP_400_BAD_REQUEST)
        if 'first_name' not in params or 'last_name' not in params:
            return Response({"message": "first and last names are required Values"},
            status=status.HTTP_400_BAD_REQUEST)
        first_name = params['first_name']
        last_name = params['last_name']
        if 'contact' not in params:
            return Response({"message": "Contact number is required field"},
            status=status.HTTP_400_BAD_REQUEST)
        contact = params['contact']
        if 'email' not in params:
            return Response({"message": "email is required field"},
            status=status.HTTP_400_BAD_REQUEST)
        if 'subject' not in params:
            return Response({"message": "subject is required field"},
            status=status.HTTP_400_BAD_REQUEST)
        if 'profile_choice' not in params:
            return Response({"message": "profile_choice is required field"},
            status=status.HTTP_400_BAD_REQUEST)
        email = params['email']
        lookup = Q(user__email=email) | Q(mobile_number=contact)
        if Profile.objects.filter(lookup).exists():
            return Response({"message": "Contact or Email already exists"},
            status=status.HTTP_400_BAD_REQUEST)
        transaction.set_autocommit(autocommit=False)
        user_obj = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user_obj.set_password(params['password'])
        user_obj.save()
        profile = Profile.objects.create(
            user=user_obj,
            subject_id=params['subject'],
            profile_choice=params['profile_choice'],
            mobile_number=contact
        )

        data = ProfileSerializer(profile, many=False).data
        transaction.commit()
        return Response({"result": data}, status=status.HTTP_201_CREATED)

class UserDetails(APIView):

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get('profile_id')
        profile_obj = get_object_or_404(Profile, id=pk)
        data = ProfileSerializer(profile_obj, many=False).data
        return Response({"result": data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_subjects_list(request):
    subjects = Subject.objects.filter(is_active=True,
                                    is_delete=False)
    serializer = SubjectSerializer(subjects, many=True).data
    print(serializer)
    return Response({"result":serializer}, status=status.HTTP_200_OK)


class QuestionApiView(APIView):
    model = Question
    queryset = Question.objects.filter(is_active=True,
    is_delete=False)

    def get(self, request, *args, **kwargs):
        params = request.query_params
        dilo = {}
        if 'subject' in params:
            dilo['subject_id'] = params['subject']
        if 'user' in params:
            dilo['creater_id'] = params['user']
        if 'search' in params:
            dilo['question__icontains'] = params['search']
        if 'question_id' in params:
            question_objs = self.queryset.filter(id=params['question_id'])
        else:
            question_objs = self.queryset.filter(**dilo)
        data = QuestionSerializer(question_objs, many=True).data
        return Response(
            {"result": data,}, status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        data = request.data
        if 'question' not in data or 'q_marks' not in data:
            return Response({'messgae': "Required Fields are not there",},
            status=status.HTTP_400_BAD_REQUEST)
        question = data['question']
        marks = data['q_marks']
        # TODO ned to update after authorization
        user = User.objects.filter(profile__profile_choice=0).last()
        subject = user.profile_set.first().subject
        if 'answer' not in data:
            return Response({"message": "Answer deails should provide"},
            status=status.HTTP_400_BAD_REQUEST)
        answer = data['answer']
        transaction.set_autocommit(autocommit=False)
        if Question.objects.filter(question=question).exists():
            return Response({"message": "Question With same details aleady exists, plese search with question"},
            status=status.HTTP_400_BAD_REQUEST)
        que_obj = Question.objects.create(
            question=question,
            creater_id=user.id,
            subject_id=subject.id,
            question_marks=marks
        )
        answer_obj = Answer.objects.create(
            question_id=que_obj.id,
            answer=answer,
            answer_type='TEXT'
        )
        seriliazer = QuestionDetailSerializer(answer_obj, many=False)
        transaction.commit()
        return Response({"result": seriliazer.data},
        status=status.HTTP_201_CREATED)


class TestPaperCreationView(CreateAPIView):
    model = TestPaper

    def post(self, request, *args, **kwargs):
        data = request.data
        if "questions" not in data:
            return Response({"message": "Need Questions"}, status=status.HTTP_400_BAD_REQUEST)
        questions = data['questions'].split(",")
        number_of_questions = len(questions)
        que_objs = Question.objects.filter(
            id__in=questions)
        total_marks = que_objs.aggregate(
                total_marks=Sum('question_marks'))['total_marks']
        if 'cut_off_marks' not in data:
            return Response({"message": "Need to mention Cut Off Marks"}, status=status.HTTP_400_BAD_REQUEST)
        cutoffmarks = data['cut_off_marks']
        if cutoffmarks > total_marks:
            return Response({"message": "Cut Off Marks Are greater than Total marks"}, status=status.HTTP_400_BAD_REQUEST)
        # TODO ned to update after authorization
        user = User.objects.filter(profile__profile_choice=0).last()
        subject = user.profile_set.first().subject
        test_paper_obj = self.model.objects.create(
            total_marks=total_marks,
            cut_off_marks=cutoffmarks,
            setter_id=user.id,
            subject_id=subject.id,
            number_of_questions=number_of_questions
        )
        test_paper_obj.questions.add(*questions)
        test_paper_obj.save()
        return Response({"message": "Test Paper is created"}, status=status.HTTP_201_CREATED)


class TestPaperSetterSubmission(APIView):
    model = TestPaper
    queryset = TestPaper.objects.filter(is_active=True,
            is_delete=False)

    def get(self, request, *args, **kwargs):
        # TODO ned to update after authorization
        user = User.objects.filter(profile__profile_choice=0).first()
        test_papers = TestPaper.objects.filter(
            setter_id=user.id,
            is_active=True,
            is_delete=False,
            checker__isnull=True,
            is_checker_approved=False,
            is_examinar_approved=False,
            is_sent_for_cheeck=False
        ).annotate(question=ArrayAgg('questions__question'),
        answers=ArrayAgg('questions__answer__answer')
        ).values('question', 'answers', 'total_marks', 'cut_off_marks',
        'subject__subject_name', 'is_checker_approved', 'is_examinar_approved',
        'checker_review', 'examiner_review'
        )
        return Response({"result": test_papers}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if "testpaper_id" not in data:
            return Response({"message": "Test Paper is Required"}, status=status.HTTP_400_BAD_REQUEST)
        testpepr_obj = get_object_or_404(TestPaper, id=data['testpaper_id'])
        testpepr_obj.is_sent_for_cheeck = True
        testpepr_obj.save()
        return Response({"message": "Sent For checking"}, status=status.HTTP_200_OK)
