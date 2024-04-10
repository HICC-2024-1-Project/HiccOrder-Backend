def get_fields(model, field_list):
    """serializer로 얻은 값에서 특정 field만 반환해주는 함수이빈다.

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
