from utils.tests_handler import TestBase


class TestAuth(TestBase):
    urlbase = "/auth"

    def test_create_user(self):
        self.clear_base()
        self.post('/sign-up', json=self.user_details)

    def test_login_user(self):
        response = self.post('/sign-in', json={"email": self.user_details["email"], "password": self.user_details["password"]})
        token = response["token"]

        self.headers["Authorization"] = f'Bearer {token}'

    def test_verify_user_is_authenticated(self):
        response = self.get('/is-authed')
        assert response

    def test_change_password(self):
        new_password = "susdfuikvhbsdvs"
        self.put('/update-password', json={"old_password": self.user_details["password"], "new_password": new_password})

        self.put('/update-password', json={"old_password": new_password, "new_password": self.user_details["password"]})

        # clear user base
        self.clear_base()
