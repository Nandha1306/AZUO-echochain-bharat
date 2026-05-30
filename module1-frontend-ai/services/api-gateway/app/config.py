from dotenv import load_dotenv

import os


# load env variables
load_dotenv()


# mongodb url
MONGODB_URL = os.getenv("MONGODB_URL")
# database name
DATABASE_NAME = os.getenv("DATABASE_NAME")
# jwt secret key
SECRET_KEY = os.getenv("SECRET_KEY")
# jwt algorithm
ALGORITHM = os.getenv("ALGORITHM")

BLOCKCHAIN_URL = os.getenv(
    "BLOCKCHAIN_URL"
)