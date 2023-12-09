from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import HTTPException, Security
from datetime import datetime, timedelta
from passlib.hash import bcrypt

from database import Users

import jwt
import configs


class AuthHandler:
    security = HTTPBearer()
    secret = configs.JWT_SECRET

    @staticmethod
    def get_password_hash(password):
        return bcrypt.hash(password)

    @staticmethod
    def verify_password(plain_password, hashed_password):
        # checks if passwords matches
        return bcrypt.verify(plain_password, hashed_password)

    def encode_token(self, user_id):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=0, minutes=180),  # time jwt expires
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload, self.secret, algorithm='HS256'
        )

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            user_id = payload['sub']

            return user_id

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Signature has expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid token')

    @staticmethod
    def verify_user(user_id):
        # get user from db
        user = Users.get_by_id(user_id)
        if user is None:
            raise HTTPException(401, detail="user doesn't exist")

        return user

    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        user_id = self.decode_token(auth.credentials)
        return self.verify_user(user_id)

    def auth_wrapper_decode_token(self, auth: HTTPAuthorizationCredentials = Security(security)):
        try:
            payload = jwt.decode(auth.credentials, self.secret, algorithms=['HS256'])

            # get user id from payload
            user_id = payload['sub']

            if not user_id:
                return None

            return user_id

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


auth_handler = AuthHandler()
