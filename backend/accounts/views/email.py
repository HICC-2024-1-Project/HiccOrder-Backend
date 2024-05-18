from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import random
import string


def generate_verification_code(length=6):
    """랜덤 인증번호 생성"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def send_verification_email(email, verification_code):
    title = "HICC Order 이메일 인증"
    context = {
        'subject_message': '인증번호',
        'content_message': verification_code,
    }
    content = render_to_string('email_template.html', context)
    mail = EmailMessage(title, content, settings.EMAIL_HOST_USER, [email])
    mail.content_subtype = "html"
    mail.send()


class SendVerificationCodeView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        verification_code = generate_verification_code()
        send_verification_email(email, verification_code)
        return Response({'message': 'Verification code sent successfully'}, status=status.HTTP_200_OK)
