from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from .serializers import RegistrationSerializer
from .models import CustomUser

class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "phone_number": user.phone_number,
                "newsletter_subscription": user.newsletter_subscription,
                "created_at": user.date_joined,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            raise ValidationError({'email': "This field is required"})
        
        try:
            user = CustomUser.objects.get(email=email)
            token_generator = PasswordResetTokenGenerator()
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            
            reset_url = f"http://127.0.0.1:8000/auth/reset-password/{uidb64}/{token}"
            
            send_mail(
                'Password Reset Request',
                f"Click the link to reset your password: {reset_url}",
                'noreply@rajapi-cop.com',
                [user.email]
            )
            return Response({"detail": "Password reset email sent"}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({"detail": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)
        
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
            
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not new_password or not confirm_password:
            return Response({"detail": "Both passwords are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if new_password != confirm_password:
            return Response({"detail": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password reset successful"}, status=status.HTTP_200_OK)