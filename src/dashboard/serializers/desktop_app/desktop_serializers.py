from rest_framework import serializers
from desktop_app.models import ExamCenter,ResultExamCenter

class ExamCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamCenter
        fields = '__all__'

class ResultExamCenterSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source='exam.name', read_only=True,allow_null=True)
    exam_date = serializers.DateField(source='exam.date', read_only=True,allow_null=True)
    student_name = serializers.CharField(source='student.name', read_only=True,allow_null=True)
    student_user_username = serializers.CharField(source='student.user.username', read_only=True,allow_null=True)
    student_parent_phone = serializers.CharField(source='student.parent_phone', read_only=True,allow_null=True)
    
    class Meta:
        model = ResultExamCenter
        fields = '__all__'

