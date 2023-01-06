def is_ajax(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"
