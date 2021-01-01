from django.views import View
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from .utils import get_urls
from .functional import bind_params, allow_methods, describe_response
from .field_functions import Path, Query, Body


def get_docs(request: HttpRequest):
    for url_pattern, view in get_urls():
        # TODO 完成文档生成
        print(url_pattern, view)
        if hasattr(view, '__methods__'):
            print(view.__methods__)

        if hasattr(view, '__params__'):
            print(view.__params__)

        if hasattr(view, '__responses__'):
            print(view.__responses__)
        getattr(bind_params(view), "__params__")
    return HttpResponse("")


def redoc(request: HttpRequest):
    return HttpResponse("")


class Home(View):
    def get(self, request, param1):
        print(param1)
        return HttpResponse()


def default_func():
    return "111"


@allow_methods(['GET', 'POST'])
@describe_response(200)
def func(
    request: HttpRequest,
    param1: int = Path(description="param1 ...", default_factory=default_func),
    param2: str = Query("222", description="param2 ..."),
    param3: int = Body(333, description="param3 ..."),
) -> HttpResponse:

    print(type(param1), param1)
    print(type(param2), param2)
    print(type(param3), param3)

    return HttpResponse()