from model.pull_request import PullRequest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


class CodeReviewRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory