from rest_framework import serializers
from view.models import VideoView,ViewSession



class ListVideoViewListSerializer(serializers.ModelSerializer):
    video_name = serializers.CharField(source="video.name")  
    student_id = serializers.CharField(source="student.id") 
    student_name = serializers.CharField(source="student.name")  
    student_username = serializers.CharField(source="student.user.username")  
    total_watch_time = serializers.SerializerMethodField()
    total_sessions = serializers.SerializerMethodField()
    class Meta:
        model = VideoView
        fields = [
            'id',
            'video_name', 
            'student_id',
            'student_name', 
            'student_username',
            'counter',
            'total_watch_time',
            'total_sessions',
            'created',

            ] 
        
    def get_total_watch_time(self, obj):
        duration = 0
        for session in obj.viewsession_set.all():
            duration += session.watch_time
        return duration

    def get_total_sessions(self, obj):
        return obj.viewsession_set.count() if obj.viewsession_set.exists() else 0
    
    




class ViewSessionListSerializer(serializers.ModelSerializer):
    video_name = serializers.CharField(source="view.video.name")  
    student_id = serializers.CharField(source="view.student.id") 
    student_name = serializers.CharField(source="view.student.name")  
    student_username = serializers.CharField(source="view.student.user.username")  

    class Meta:
        model = ViewSession
        fields = [
            'id',
            'video_name', 
            'student_id',
            'student_name', 
            'student_username',
            'session',
            'watch_time',
            'created'
            ]