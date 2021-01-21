from typing import TypeVar, Callable, Dict, List, Any
from inspect import signature, isclass

from django.http.request import HttpRequest
from pydantic import BaseModel, ValidationError, create_model

from .utils import merge_query_dict, is_class_view
from .exceptions import RequestValidationError
from .fields import QueryInfo, HeaderInfo, CookieInfo, BodyInfo, PathInfo, ExclusiveInfo

HTTPHandler = TypeVar("HTTPHandler", bound=Callable)


def create_model_config(title: str = None, description: str = None):
    class ExclusiveModelConfig:
        @staticmethod
        def schema_extra(schema, model) -> None:
            if title is not None:
                schema["title"] = title
            if description is not None:
                schema["description"] = description

    return ExclusiveModelConfig


def _parse_and_bound_params(handler: HTTPHandler) -> HTTPHandler:
    sig = signature(handler)

    __parameters__ = {}
    __exclusive_models__ = {}
    path: Dict[str, Any] = {}
    query: Dict[str, Any] = {}
    header: Dict[str, Any] = {}
    cookie: Dict[str, Any] = {}
    body: Dict[str, Any] = {}

    for name, param in sig.parameters.items():
        default = param.default
        annotation = param.annotation

        if isinstance(default, QueryInfo):
            _type_ = query
        elif isinstance(default, HeaderInfo):
            _type_ = header
        elif isinstance(default, CookieInfo):
            _type_ = cookie
        elif isinstance(default, BodyInfo):
            _type_ = body
        elif isinstance(default, PathInfo):
            _type_ = path
        elif isinstance(default, ExclusiveInfo):
            if isclass(annotation) and issubclass(annotation, BaseModel):
                model = annotation
            else:
                model = create_model(
                    "temporary_exclusive_model",
                    __config__=create_model_config(default.title, default.description),
                    __root__=(annotation, ...),
                )
            __parameters__[default.name] = model
            __exclusive_models__[model] = name
            continue
        else:
            continue

        if annotation != param.empty:
            _type_[name] = (annotation, default)
        else:
            _type_[name] = default

    __locals__ = locals()
    for key in filter(
        lambda key: bool(__locals__[key]), ("path", "query", "header", "cookie", "body")
    ):
        if key in __parameters__:
            raise RuntimeError(
                f'Exclusive("{key}") and {key.capitalize()} cannot be used at the same time'
            )
        __parameters__[key] = create_model("temporary_model", **locals()[key])  # type: ignore

    if "body" in __parameters__:
        setattr(handler, "__request_body__", __parameters__.pop("body"))

    if __parameters__:
        setattr(handler, "__parameters__", __parameters__)

    if __exclusive_models__:
        setattr(handler, "__exclusive_models__", __exclusive_models__)

    return handler


def _generate_parameters(
    handler: HTTPHandler, request: HttpRequest, may_path_params: Dict[str, Any]
) -> Dict[str, Any]:
    parameters = getattr(handler, "__parameters__", None)
    request_body = getattr(handler, "__request_body__", None)
    exclusive_models = getattr(handler, "__exclusive_models__", {})
    if not (parameters or request_body):
        return {}

    data: List[Any] = []
    kwargs: Dict[str, Any] = {}

    try:
        # try to get parameters model and parse
        if parameters:
            if "path" in parameters:
                data.append(parameters["path"].parse_obj(may_path_params))

            if "query" in parameters:
                data.append(
                    parameters["query"].parse_obj(merge_query_dict(request.GET))
                )

            if "header" in parameters:
                data.append(
                    parameters["header"].parse_obj(merge_query_dict(request.headers))
                )

            if "cookie" in parameters:
                data.append(parameters["cookie"].parse_obj(request.COOKIES))

        # try to get body model and parse
        if request_body:
            data.append(request_body.parse_obj(request.DATA))

    except ValidationError as e:
        raise RequestValidationError(e)

    for _data in data:
        if _data.__class__.__name__ == "temporary_model":
            kwargs.update(_data.dict())
        elif _data.__class__.__name__ == "temporary_exclusive_model":
            kwargs[exclusive_models[_data.__class__]] = _data.__root__
        else:
            kwargs[exclusive_models[_data.__class__]] = _data

    return kwargs


def parse_and_bound_params(handler: Any) -> None:
    if is_class_view(handler):
        view_class = handler.view_class
        for method in view_class.http_method_names:
            if not hasattr(view_class, method):
                continue
            setattr(
                view_class, method, _parse_and_bound_params(getattr(view_class, method))
            )
    else:
        _parse_and_bound_params(handler)


def generate_parameters(
    handler: Any, request: HttpRequest, may_path_params: Dict[str, Any]
) -> Dict[str, Any]:
    if is_class_view(handler):
        return _generate_parameters(
            getattr(
                handler.view_class,
                request.method.lower(),
                handler.view_class.http_method_not_allowed,
            ),
            request,
            may_path_params,
        )
    return _generate_parameters(handler, request, may_path_params)