"""Small helpers shared by several apps."""
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def is_ajax(request):
    """True when the request was sent by our JavaScript (fetch)."""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def redirect_back(request, fallback, *args):
    """
    Redirect to the ``next`` value posted with the form if it is a safe,
    same-site URL; otherwise redirect to the named ``fallback`` URL.
    """
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(fallback, *args)
