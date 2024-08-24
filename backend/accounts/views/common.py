import jwt
import pickle

from accounts.models import User
from backend.settings import SECRET_KEY
from django.shortcuts import get_object_or_404


def get_fields(model, field_list):
    """serializer로 얻은 값에서 특정 field만 반환해주는 함수이다.

    Args:
        model: serializer를 통해 얻은 인스턴스 값(단일 혹은 다중값 상관없이 전부 가능).
        field_list: 사용할 field_list 목록, field의 이름을 리스트로 넣어주면 됩니다.

    Returns:
        리스트 안에 딕셔너리 자료형을 반환합니다.
    """
    data = []

    # 인스턴스가 여러 개인 경우
    if isinstance(model, list):
        for instance in model:
            single_data = {}
            for field_name in field_list:
                if hasattr(instance, field_name):
                    single_data[field_name] = getattr(instance, field_name)
            data.append(single_data)

    # 인스턴스가 한 개인 경우
    else:
        single_data = {}
        for field_name in field_list:
            if hasattr(model, field_name):
                single_data[field_name] = getattr(model, field_name)
        data = single_data

    return data


def check_authority(request, booth_id):
    access_token = request.headers.get('Authorization', None).replace('Bearer ', '')
    payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
    user = User.objects.get(email=payload['email'])  # 이메일 값으로 유저 확인
    user_instance = get_object_or_404(User, pk=booth_id)
    if user == user_instance:  # 토큰의 유저 정보와 유저 정보가 일치할 때만 허가
        return True
    else:
        return False

def search_cache(cache, target_field, target_value):
    """cache에서 특정 키와 value를 찾는 함수이다.

        Args:
            cache: cache object in django LocMemCache
            target_field: cache에서 찾을 키
            target_value: cache에서 찾을 키의 값

        Returns:
            list 형태로 key만 반환 반환
        """
    keys = cache._cache.keys()
    result_list = []
    for key in keys:
        value = cache._cache.get(key)
        obj = pickle.loads(value)
        if target_field in obj.keys():
            if obj[target_field] == target_value:
                result_list.append(key_seperator(key))
    return result_list


def key_seperator(key):
    parts = key.split(':')

    # 세 번째 부분 (인덱스 2)을 추출합니다.
    if len(parts) > 2:
        desired_part = parts[2]
        return desired_part
    else:
        raise ValueError("문자열이 예상된 형식을 따르지 않습니다. ':' 구분자가 부족합니다.")
