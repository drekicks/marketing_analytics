# from pathlib import Path
#
# print("utils.py is located at:", Path(__file__).resolve())
# print("Its parent folder is:", Path(__file__).resolve().parent)
import os
from dotenv import load_dotenv
from pathlib import Path

# def find_project_root(start: Path, marker: str = ".env") -> Path:
#     current = start
#     for _ in range(6):
#         if (current / marker).is_file():
#             return current
#         current = current.parent
#     raise FileNotFoundError(f"Could not find '{marker}' above {start}")
#
# env_path = find_project_root(Path(__file__).resolve().parent) / ".env"
# load_dotenv(dotenv_path=env_path)

env_path = Path(__file__).resolve().parent.parent.parent/ ".env"  # adjust based on where .env actually lives
load_dotenv(dotenv_path=env_path)
# load_dotenv()

print("DB_USER:", os.getenv('DB_USER'))
print("DB_PASSWORD:", os.getenv('DB_PASSWORD'))
print("DB_HOST:", os.getenv('DB_HOST'))
print("DB_PORT:", os.getenv('DB_PORT'))
print("DB_NAME:", os.getenv('DB_NAME'))