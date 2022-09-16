from urllib import response
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, Case, When, BooleanField
from django.contrib.postgres.aggregates import ArrayAgg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from .models import CheckingTestPaper, Question, Answer, TestPaper, Profile, Subject
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
        # if 'profile_choice' not in params:
        #     return Response({"message": "profile_choice is required field"},
        #     status=status.HTTP_400_BAD_REQUEST)
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
        Token.objects.create(user=user_obj)
        profile = Profile.objects.create(
            user=user_obj,
            subject_id=params['subject'],
            # profile_choice=params['profile_choice'],
            mobile_number=contact
        )
        data = ProfileSerializer(profile, many=False).data
        transaction.commit()
        return Response({"result": data}, status=status.HTTP_201_CREATED)

class UserDetails(APIView):
    permission_classes = [IsAuthenticated]


    def get(self, request, *args, **kwargs):
        # pk = request.query_params.get('profile_id')
        user = request.user
        pk = user.profile_set.first().id
        profile_obj = get_object_or_404(Profile, id=pk)
        data = ProfileSerializer(profile_obj, many=False).data
        return Response(data, status=status.HTTP_200_OK)


class SubjectsList(APIView):

    def get(self, request, *args, **kwargs):
        subjects = Subject.objects.filter(is_active=True,
                                        is_delete=False)
        serializer = SubjectSerializer(subjects, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)


class QuestionApiView(APIView):
    model = Question
    queryset = Question.objects.filter(is_active=True,
    is_delete=False)
    permission_classes = [IsAuthenticated]


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
             data, status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        data = request.data
        if 'question' not in data or 'q_marks' not in data:
            return Response({'messgae': "Required Fields are not there",},
            status=status.HTTP_400_BAD_REQUEST)
        question = data['question']
        marks = data['q_marks']
        user = request.user
        if "subject" in data:
            subject_id = data['subject']
        else:
            subject = user.profile_set.first().subject
            subject_id = subject.id
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
            subject_id=subject_id,
            question_marks=marks
        )
        answer_obj = Answer.objects.create(
            question_id=que_obj.id,
            answer=answer,
            answer_type='TEXT'
        )
        seriliazer = QuestionDetailSerializer(answer_obj, many=False)
        transaction.commit()
        return Response(seriliazer.data,
        status=status.HTTP_201_CREATED)


class TestPaperCreationView(CreateAPIView):
    model = TestPaper
    permission_classes = [IsAuthenticated]


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
        cutoffmarks = int(data['cut_off_marks'])
        if cutoffmarks > total_marks:
            return Response({"message": "Cut Off Marks Are greater than Total marks"}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
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

class TestPaperListView(APIView):
    model = TestPaper
    queryset = TestPaper.objects.filter(is_active=True,
            is_delete=False)
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        params = request.query_params
        user = request.user

        query_dict = {'is_active': True,
                    'is_delete': False,
                    'setter_id': user.id,
                    }
        if 'is_sent_checker' in params:
            query_dict['is_sent_for_cheeck'] = True
            query_dict['is_checker_approved'] = False
        if 'is_sent_examiner' in params:
            query_dict['is_sent_for_cheeck'] = True
            query_dict['is_examinar_approved'] = False
        test_papers = TestPaper.objects.filter(
           **query_dict
        ).annotate(question=ArrayAgg('questions__question'),
                   question_ids=ArrayAgg('questions'),
                   is_checker_pending=Case(
                       When((Q(checker__isnull=False)&Q(is_checker_approved=False)), then=True),
                       default=False, output_field=BooleanField()
                   ),
                    is_examiner_pending=Case(
                       When((Q(examiner__isnull=False)&Q(is_examinar_approved=False)), then=True),
                       default=False, output_field=BooleanField()
                   ),
        answers=ArrayAgg('questions__answer__answer')
        ).values("id", 'question', 'answers', 'total_marks', 'cut_off_marks',
        'subject__subject_name', 'is_checker_approved', 'is_examinar_approved',
        'checker_review', 'examiner_review', 'question_ids', 'is_checker_pending', 'is_examiner_pending', "is_sent_for_cheeck"
        )
        return Response({"result": test_papers}, status=status.HTTP_200_OK)

class TestPaperSetterSubmission(APIView):
    model = TestPaper
    queryset = TestPaper.objects.filter(is_active=True,
            is_delete=False)

    def get(self, request, *args, **kwargs):
        # TODO ned to update after authorization
        user =request.user
        test_papers = TestPaper.objects.filter(
            setter_id=user.id,
            is_active=True,
            is_delete=False,
            is_sent_for_cheeck=False
        ).annotate(question=ArrayAgg('questions__question'),
        answers=ArrayAgg('questions__answer__answer')
        ).values('question', 'answers', 'total_marks', 'cut_off_marks',
        'subject__subject_name', 'is_checker_approved', 'is_examinar_approved',
        'checker_review', 'examiner_review', "is_sent_for_cheeck"
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

class TestPapersListSetterView(APIView):
    model = TestPaper
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user =request.user
        dic = {'is_active': True,
                    'is_delete': False, "is_sent_for_cheeck": True}
        profile_ch = user.profile_set.first().profile_choice
        if profile_ch == "1":
            dic['checker__isnull'] = True
        elif profile_ch == "2":
            dic['checker__isnull'] = False
            dic['is_checker_approved'] = True
            dic['examiner__isnull'] = True
        test_papers = TestPaper.objects.filter(
           **dic
        ).annotate(question=ArrayAgg('questions__question'),
                question_ids=ArrayAgg('questions'),
                is_checker_pending=Case(
                    When((Q(checker__isnull=False)&Q(is_checker_approved=False)), then=True),
                    default=False, output_field=BooleanField()
                ),
                is_examiner_pending=Case(
                    When((Q(examiner__isnull=False)&Q(is_examinar_approved=False)), then=True),
                    default=False, output_field=BooleanField()
                ),
        answers=ArrayAgg('questions__answer__answer')
        ).values("id", 'question', 'answers', 'total_marks', 'cut_off_marks',
        'subject__subject_name', 'is_checker_approved', 'is_examinar_approved',
        'checker_review', 'examiner_review', 'question_ids', 'is_checker_pending', 'is_examiner_pending', "is_sent_for_cheeck", "setter__username",
        "checker__username", "examiner__username"
        )
        print(test_papers.count())
        return Response(test_papers, status=status.HTTP_200_OK)

class TestPaperCheckerAcception(APIView):
    model = TestPaper
    permission_classes = [IsAuthenticated]


    def get(self, request):
        qp_id = request.query_params.get('testpaper_id')
        testpaper = self.model.objects.get(id=qp_id)
        user = request.user
        testpaper.checker = user
        testpaper.save()
        response = {
            "message": "Accepted For checking",
            "id": qp_id,
            "Number of Questions": testpaper.number_of_questions,
            "questions": testpaper.questions.values_list('question', flat=True),
            "Total Marks": testpaper.total_marks,
            "Cut Off Marks": testpaper.cut_off_marks
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        import json
        data = request.data
        if "testpaper_id" not in data:
            return Response({"message": "Test Paper is Required"}, status=status.HTTP_400_BAD_REQUEST)
        testpaper_obj = get_object_or_404(TestPaper, id=data['testpaper_id'])
        if "approval" not in data:
            return Response({"message": "Approval is Required"}, status=status.HTTP_400_BAD_REQUEST)
        checker_message = data.get('messgae')
        approval = data['approval'] == "True"
        user = request.user
        profile_ch = user.profile_set.first().profile_choice
        response = {
            'message': 'paper is approved By Checker Sent to Examiner'
        }
        if profile_ch == "1":
            testpaper_obj.is_checker_approved = approval
            testpaper_obj.checker_review = checker_message
            if not approval:
                response['message'] = "Paper is Not approved please check"
                testpaper_obj.checker = None
                testpaper_obj.is_sent_for_cheeck = False
            
        elif profile_ch == "2":
            testpaper_obj.is_examinar_approved = approval
            testpaper_obj.examiner = checker_message
            if not approval:
                testpaper_obj.is_checker_approved = approval
                testpaper_obj.is_sent_for_cheeck = False
                testpaper_obj.checker = None
                testpaper_obj.examiner = None
                response['message'] = "Paper is Not approved please check"
                

        # check_paper_obj, is_created = CheckingTestPaper.objects.get_or_create(test_paper_id=testpaper_obj.id)
        
        # check_paper_obj.checker_review = checker_message
        # check_paper_obj.is_checker_approved = approval
        # check_paper_obj.save()

        # if not approval:
        #     testpaper_obj.checker = None
        #     testpaper_obj.is_sent_for_cheeck = False
        testpaper_obj.save()
        return Response(response, status=status.HTTP_200_OK)

class TestPaperAcceptedList(APIView):
    model = TestPaper
    permission_classes = [IsAuthenticated]   
    
    def get(self, request):
        user =request.user
        dic = {'is_active': True,
                    'is_delete': False}
        profile_ch = user.profile_set.first().profile_choice
        if profile_ch == "1":
            dic['checker_id'] = user.id
        elif profile_ch == "2":
            dic['examiner_id'] = user.id
        test_papers = TestPaper.objects.filter(
           **dic
        ).annotate(question=ArrayAgg('questions__question'),
                question_ids=ArrayAgg('questions'),
                is_checker_pending=Case(
                    When((Q(checker__isnull=False)&Q(is_checker_approved=False)), then=True),
                    default=False, output_field=BooleanField()
                ),
                is_examiner_pending=Case(
                    When((Q(examiner__isnull=False)&Q(is_examinar_approved=False)), then=True),
                    default=False, output_field=BooleanField()
                ),
        answers=ArrayAgg('questions__answer__answer')
        ).values("id", 'question', 'answers', 'total_marks', 'cut_off_marks',
        'subject__subject_name', 'is_checker_approved', 'is_examinar_approved',
        'checker_review', 'examiner_review', 'question_ids', 'is_checker_pending', 'is_examiner_pending', "is_sent_for_cheeck", "setter__username",
        "checker__username", "examiner__username"
        )
        return Response(test_papers, status=status.HTTP_200_OK)
