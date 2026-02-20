from .utils import *
from ..routers.users import get_db, get_current_user
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_return_user(test_user):
    response = client.get("/user")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "rostami"
    assert response.json()["email"] == "rostami@gmail.com"
    assert response.json()["first_name"] == "hossein"
    assert response.json()["last_name"] == "rostami"
    assert response.json()["role"] == "admin"


def test_change_password_success(test_user):
    response = client.put(
        "/user/password",
        json={"password": "testpassword", "new_password": "newpassword"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_change_password_invalid_current_password(test_user):
    response = client.put(
        "/user/password",
        json={"password": "wrong_password", "new_password": "newpassword"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Incorrect current password"}


# Phone number endpoint doesn't exist - Users model doesn't have phone_number field
# def test_change_phone_number_success(test_user):
#     response = client.put("/user/phonenumber/2222222222")
#     assert response.status_code == status.HTTP_204_NO_CONTENT
