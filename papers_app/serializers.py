from rest_framework import serializers

from .models import Profile, Subject, Question, Answer


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = '__all__'
    
    def to_representation(self, instance):
        # data = super().to_representation(instance)
        user_choices = dict([("0",'Setter'),("2" ,'Examinar'),("1",'Checker')])
        return {
            'id': instance.id,
            'user_id': instance.user.id,
            'username': instance.user.username,
            'first_name': instance.user.first_name,
            'last_name': instance.user.last_name,
            'email': instance.user.email,
            'contact': instance.mobile_number,
            'subject': instance.subject.subject_name if instance.subject else None,
            'profile_choice': user_choices.get(instance.profile_choice)
        }


class SubjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subject
        fields = "__all__"

class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = '__all__'


class QuestionDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Answer
        fields = '__all__'
    
    def to_representation(self, instance):
        que_obj = instance.question
        return {
            'question': que_obj.question,
            'marks': que_obj.question_marks,
            'subject': que_obj.subject.subject_name,
            'creater': que_obj.creater.username,
            'answer': instance.answer
        }