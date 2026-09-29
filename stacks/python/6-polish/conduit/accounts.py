from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from ninja import Router, Schema

from .http import APIError, require_value
from .models import LoginAttempt, User

router = Router()


def password(value):
    require_value("password", value)
    if len(value) < 8:
        raise APIError(422, "password", "is too short")
    return value


def validate_identity(data):
    for field, validator in (("username", UnicodeUsernameValidator()), ("email", validate_email)):
        if field in data:
            require_value(field, data[field])
            try:
                validator(data[field])
            except DjangoValidationError:
                raise APIError(422, field, "is invalid") from None
            if field == "email":
                data[field] = User.objects.normalize_email(data[field])


def unique_user(data, exclude=None):
    for field in ("username", "email"):
        if field in data:
            users = User.objects.filter(**{field: data[field]})
            if exclude:
                users = users.exclude(pk=exclude.pk)
            if users.exists():
                raise APIError(409, field, "has already been taken")


def token_for(user):
    claims = {"sub": str(user.pk), "exp": datetime.now(UTC) + timedelta(days=30)}
    return jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")


def viewer(request):
    header = request.headers.get("Authorization", "")
    if not header:
        return None
    try:
        scheme, token = header.split(" ", 1)
        if scheme != "Token":
            raise ValueError
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return User.objects.get(pk=claims["sub"])
    except ValueError, jwt.InvalidTokenError, User.DoesNotExist, KeyError:
        raise APIError(401, "token", "is invalid") from None


def required_user(request):
    user = viewer(request)
    if user is None:
        raise APIError(401, "token", "is missing")
    return user


def user_data(user):
    return {
        "email": user.email,
        "token": token_for(user),
        "username": user.username,
        "bio": user.bio,
        "image": user.image,
    }


def profile_data(user, current=None, *, following=None):
    if following is None:
        following = bool(current and current.following.filter(pk=user.pk).exists())
    return {
        "username": user.username,
        "bio": user.bio,
        "image": user.image,
        "following": following,
    }


def profile_or_404(username):
    user = User.objects.filter(username=username).first()
    if user is None:
        raise APIError(404, "profile", "not found")
    return user


class Registration(Schema):
    username: str
    email: str
    password: str


class RegistrationBody(Schema):
    user: Registration


class Login(Schema):
    email: str
    password: str


class LoginBody(Schema):
    user: Login


class UserChanges(Schema):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    bio: str | None = None
    image: str | None = None


class UserChangesBody(Schema):
    user: UserChanges


@router.post("/users", response={201: dict})
def register(request, payload: RegistrationBody):
    data = payload.user.model_dump()
    validate_identity(data)
    password(data["password"])
    unique_user(data)
    user = User.objects.create_user(**data)
    return 201, {"user": user_data(user)}


@router.post("/users/login")
def login(request, payload: LoginBody):
    data = payload.user
    require_value("email", data.email)
    require_value("password", data.password)
    email = User.objects.normalize_email(data.email)
    user = User.objects.filter(email=email).first()
    if user is None:
        User().set_password(data.password)
    if user is None or not user.check_password(data.password):
        if LoginAttempt.failed(email):
            raise APIError(429, "credentials", "too many attempts")
        raise APIError(401, "credentials", "invalid")
    return {"user": user_data(user)}


@router.get("/user", auth=required_user)
def current_user(request):
    return {"user": user_data(request.auth)}


@router.put("/user", auth=required_user)
def update_user(request, payload: UserChangesBody):
    user = request.auth
    data = payload.user.model_dump(exclude_unset=True)
    validate_identity(data)
    new_password = None
    if "password" in data:
        new_password = data.pop("password")
        password(new_password)
    unique_user(data, user)
    for field, value in data.items():
        if field in ("bio", "image") and not value:
            value = None
        setattr(user, field, value)
    if new_password is not None:
        user.set_password(new_password)
    user.save()
    return {"user": user_data(user)}


@router.get("/profiles/{username}")
def get_profile(request, username: str):
    return {"profile": profile_data(profile_or_404(username), viewer(request))}


@router.post("/profiles/{username}/follow", auth=required_user)
def follow(request, username: str):
    target = profile_or_404(username)
    request.auth.following.add(target)
    return {"profile": profile_data(target, request.auth)}


@router.delete("/profiles/{username}/follow", auth=required_user)
def unfollow(request, username: str):
    target = profile_or_404(username)
    request.auth.following.remove(target)
    return {"profile": profile_data(target, request.auth)}
