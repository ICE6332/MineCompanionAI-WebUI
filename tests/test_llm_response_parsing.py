"""覆盖 _response_to_dict 的所有分支逻辑。"""

from dataclasses import dataclass

import pytest
from pydantic import BaseModel
from pydantic.v1 import BaseModel as V1BaseModel

from core.llm.service import LLMService


@dataclass
class SerializablePayload:
    """用于验证可序列化对象的示例数据。"""

    title: str
    score: int


class NonSerializablePayload:
    """包含 set 字段，无法被 JSON 序列化。"""

    def __init__(self) -> None:
        self.title = "bad"
        self.tags = {1, 2, 3}


class JsonLikeResponse:
    """模拟仅提供 json() 方法的响应对象。"""

    def json(self) -> str:
        return "{\"status\": \"ok\", \"count\": 2}"


class DemoV2Model(BaseModel):
    """Pydantic v2 模型，触发 model_dump() 分支。"""

    name: str
    size: int


class DemoV1Model(V1BaseModel):
    """Pydantic v1 模型，触发 dict() 分支。"""

    flag: bool
    note: str

    class Config:
        extra = "allow"

    def __init__(self, **data):
        super().__init__(**data)
        self._dict_called = False

    def dict(self, *args, **kwargs):  # noqa: A003 - 与 Pydantic 一致
        self._dict_called = True
        return {"flag": self.flag, "note": self.note}


def test_response_to_dict_with_string_valid_json():
    """验证字符串输入为合法 JSON 时可正确解析。"""

    data = "{\"msg\": \"hello\", \"value\": 1}"
    result = LLMService._response_to_dict(data)
    assert result == {"msg": "hello", "value": 1}


def test_response_to_dict_with_string_invalid_json():
    """验证非法 JSON 字符串会抛出包含 JSON 关键字的异常。"""

    bad_data = "<html><body>oops</body></html>"
    with pytest.raises(ValueError, match="JSON"):
        LLMService._response_to_dict(bad_data)


def test_response_to_dict_with_dict():
    """验证传入字典会被原样返回。"""

    payload = {"a": 1, "b": "two"}
    result = LLMService._response_to_dict(payload)
    assert result is payload


def test_response_to_dict_with_pydantic_model():
    """验证 Pydantic v2 模型通过 model_dump 转字典。"""

    model = DemoV2Model(name="alpha", size=3)
    result = LLMService._response_to_dict(model)
    assert result == {"name": "alpha", "size": 3}


def test_response_to_dict_with_pydantic_v1_model():
    """验证 Pydantic v1 模型通过 dict 转字典。"""

    model = DemoV1Model(flag=True, note="legacy")
    result = LLMService._response_to_dict(model)
    assert result == {"flag": True, "note": "legacy"}
    assert model._dict_called is True


def test_response_to_dict_with_json_method():
    """验证仅提供 json() 方法的对象可被解析。"""

    mock_response = JsonLikeResponse()
    result = LLMService._response_to_dict(mock_response)
    assert result == {"status": "ok", "count": 2}


def test_response_to_dict_with_serializable_object():
    """验证普通可序列化对象会通过 json.dumps/loads 返回字典。"""

    payload = SerializablePayload(title="demo", score=99)
    result = LLMService._response_to_dict(payload)
    assert result == {"title": "demo", "score": 99}


def test_response_to_dict_with_non_serializable():
    """验证无法序列化的对象会抛出 ValueError。"""

    payload = NonSerializablePayload()
    with pytest.raises(ValueError, match="序列化"):
        LLMService._response_to_dict(payload)
