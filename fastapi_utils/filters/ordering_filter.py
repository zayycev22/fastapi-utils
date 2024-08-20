from typing import Sequence, Any, Type, Optional
from pydantic import BaseModel, Field, create_model
from fastapi import Request
from fastapi_utils.filters.base import BaseFilterBackend


class OrderingFilter(BaseFilterBackend):
    order_query_param = "ordering"

    def __init__(self, *ordering_fields, primary_key: Optional[str] = None, default_ordering: str = 'id',
                 primary_key_bool: bool = False):
        self.default_ordering = default_ordering
        self.ordering_fields = ordering_fields
        self.primary_key_bool = primary_key_bool
        if primary_key_bool:
            if primary_key is None:
                raise TypeError("When primary_key_bool is True - primary_key must be set")
            self.primary_key = primary_key

    async def filter_queryset(self, request: Request, data: Sequence[Any]) -> Sequence[Any]:
        if len(data) == 0:
            return data
        param = request.query_params.get(self.order_query_param)
        if param is not None and self._prepare_param(param) in self.ordering_fields and param != '':
            new_data = self._order_queryset(param.strip(), data)
        else:
            new_data = self._order_queryset(self.default_ordering, data)

        return new_data

    def _prepare_param(self, param: str) -> str:
        new_param = param.strip()
        if new_param.startswith("-"):
            new_param = new_param[1:]
        return new_param

    def _sort(self, data: Sequence[Any], param: str, reverse: bool = False):
        if self.primary_key_bool:
            return sorted(data,
                          key=lambda x: (getattr(x, self._prepare_param(param)), getattr(x, self.primary_key)),
                          reverse=reverse)
        else:
            return sorted(data,
                          key=lambda x: getattr(x, self._prepare_param(param)),
                          reverse=reverse)

    def _order_queryset(self, param: str, data: Sequence[Any]) -> Sequence[Any]:
        self._check_queryset(data, self._prepare_param(param))
        if param.startswith("-"):
            return self._sort(data, param, reverse=True)
        return self._sort(data, param)

    @classmethod
    def request_schema(cls) -> Type[BaseModel]:
        request_schema = {
            cls.order_query_param: (Optional[str], Field(default=None)),
        }
        return create_model(f"{cls.__name__.split('.')[-1]}", **request_schema)

    def _check_queryset(self, data: Sequence[Any], param: str) -> None:
        for d in data:
            if not hasattr(d, param):
                raise AttributeError(f"{data[0]} has no attribute {self._prepare_param(param)}")
            elif self.primary_key_bool:
                if not hasattr(d, self.primary_key):
                    raise AttributeError(f"{data[0]} has no attribute {self._prepare_param(self.primary_key)}")
                break
            else:
                break
