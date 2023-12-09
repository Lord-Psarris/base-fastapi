from dotenv import load_dotenv
import os

load_dotenv()

# environment configs
ENVIRONMENT = os.getenv('ENVIRONMENT')
DEBUG_MODE = ENVIRONMENT == 'DEVELOPMENT'

# secret keys
JWT_SECRET = os.getenv('JWT_SECRET')
