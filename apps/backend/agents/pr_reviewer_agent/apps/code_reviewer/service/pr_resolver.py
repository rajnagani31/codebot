from argparse import Action
from dataclasses import dataclass
from enum import Enum


class PullRequestAction(str, Enum):
    OPENED = "opened"
    READY_FOR_REVIEW = "ready_for_review"
    SYNCHRONIZE = "synchronize"
    REOPENED = "reopened"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass
class PrChoiceResolverInput:
    action : str

class PrResolver:
    def resolver(self, payload):
        action = payload.get("action", "unknown")
        return self._pr_action_normalize_choice(
            PrChoiceResolverInput(action=action)
        )


    def _pr_action_normalize_choice(
            self, 
            action_choice : PrChoiceResolverInput
    ) -> PullRequestAction:
        
        return action_choice.action