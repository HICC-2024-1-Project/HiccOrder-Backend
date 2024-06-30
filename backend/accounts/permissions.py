from rest_framework.permissions import BasePermission


# 쿠키의 세션 정보가 유효한지 체크하는 코드 permission_classes = [TemporaryUserPermission]로 권한을 확인하면 됨
class TemporaryUserPermission(BasePermission):
    def has_permission(self, request, view):
        # 세션에서 임시 사용자 ID를 가져옵니다.
        temporary_user_id = request.COOKIES.get('temporary_user_id')
        return bool(temporary_user_id)
