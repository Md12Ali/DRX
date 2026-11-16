"""Make the logged-in user's role available in every template."""


def user_role(request):
    """Adds ``is_instructor`` and ``instructor`` to the template context."""
    user = request.user
    instructor = getattr(user, "instructor", None) if user.is_authenticated else None
    return {"is_instructor": instructor is not None, "current_instructor": instructor}
