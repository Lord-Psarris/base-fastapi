from fastapi.testclient import TestClient
from bson import json_util

from utils.app_handler import create_app
from database import user_crud

import requests
import json

app = create_app()

class TestBase:
    client = TestClient(app)

    urlbase = ''
    headers = {"Content-type": "application/json", "Authorization": ""}
    user_details = {"first_name": "test", "last_name": "user", "email": "test@user.com", "password": "c23832r@##@$fsg"}

    data_store = {}

    def set_token(self):
        """
        This runs tests on the auth endpoints in order to derive the required token
        """
        self.urlbase = ''

        # create user
        user = user_crud.get({"email": self.user_details["email"]})
        if user is None:
            user_crud.create(self.user_details)

        # get token
        data = {"email": self.user_details["email"], "password": self.user_details["password"]}
        response = self.post("/auth/sign-in", json=data)

        self.headers["Authorization"] = "Bearer " + response["token"]

    @staticmethod
    def parse_json(data):
        return json.loads(json_util.dumps(data))

    def response_handler(self, *args, **kwargs):
        try:
            response = self.client.request(*args, **kwargs)
        except requests.exceptions.Timeout:
            # ensuring the request didn't exceed the required duration
            response = 'timeout'

        return response

    def requests(self, url: str, method: str, expected_status: int = 200, expected_response: dict = None,
                non_json: bool = None, max_response_time: float = 2.0, json: dict = None, data: dict = None,
                files: dict = None) -> dict:
        """
        Abstracts the request process to the test client
        :param url: final url to the url being accessed
        :param method: the request method
        :param expected_status: setting this asserts the expected status code from the response
        :param expected_response: setting this asserts the expected json response
        :param max_response_time: setting this asserts the response didn't exceed this duration
        :param non_json: setting this specifies that the response coming back is not in json format
        :param json: json data to be passed
        :param data: non json data to be passed
        :param files: file binary to be passed in request
        :return: response
        """
        url = self.urlbase + url
        response = self.response_handler(method, url, headers=self.headers, json=json, data=data, files=files,
                                        timeout=max_response_time)

        # verify the request execution was within time range
        assert response != 'timeout'
        print(response)

        # verify the status code is what is expected
        assert response.status_code == expected_status

        # verify the response is what os expected
        if expected_response:
            assert self.parse_json(response.json()) == expected_response

        print(response.text)
        return self.parse_json(response.json()) if not non_json else response

    def get(self, url: str, **kwargs):
        response = self.requests(url, method="get", **kwargs)

        return response

    def post(self, url: str, **kwargs):
        response = self.requests(url, method="post", **kwargs)

        return response

    def put(self, url: str, **kwargs):
        response = self.requests(url, method="put", **kwargs)

        return response

    def patch(self, url: str, **kwargs):
        response = self.requests(url, method="patch", **kwargs)

        return response

    def delete(self, url: str, **kwargs):
        response = self.requests(url, method="delete", **kwargs)

        return response

    def clear_base(self):
        """
        This runs once the class is cleared and deletes the existing user
        """
        # delete user
        user = user_crud.get({"email": self.user_details["email"]})
        if user:
            user_crud.delete(user.id)

        self.data_store = {}
    