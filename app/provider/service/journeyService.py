from abc import ABC, abstractmethod

from app.dao import journey_repo
from app.dao.model.journey import Journey


class JourneyService():

    def get_journey(self, journey_id: int) -> Journey:
        return journey_repo.find_by_journey_id(journey_id)