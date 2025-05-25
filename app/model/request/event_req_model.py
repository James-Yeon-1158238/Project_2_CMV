from datetime import datetime
from typing import List
from wtforms import DateTimeLocalField, FieldList, FileField, Form, IntegerField, StringField
from wtforms.validators import DataRequired, NumberRange, Optional
from werkzeug.datastructures import FileStorage

from app.dao.model import event_photo

class AddEventRequest(Form):

    journey_id: IntegerField = IntegerField('journey_id', validators = [
        DataRequired(message = 'invalid journet id'),
        NumberRange(min = 1, message = 'invalid journey id')
    ])
    event_photo_ids: List[str] = [] 
    event_title: StringField = StringField('event_title', validators = [
        DataRequired(message = 'invalid event title')
    ])
    event_desc: StringField = StringField('event_desc', validators = [
        Optional()
    ])
    event_start_date: DateTimeLocalField = DateTimeLocalField('event_start_date', format = '%Y-%m-%dT%H:%M', validators = [DataRequired(message = 'invalid start date input')])
    event_end_date: DateTimeLocalField = DateTimeLocalField('event_end_date', format = '%Y-%m-%dT%H:%M', validators = [Optional()])
    event_location: StringField = StringField('event_location', validators = [DataRequired(message = 'invalid location input')])

    def validate(self):
        if not super().validate():
            return False
        start_date = self.event_start_date.data
        end_date = self.event_end_date.data
        if end_date and start_date and end_date < start_date:
            self.event_end_date.errors.append("End date cannot be before start date")
            return False
        return True

    def get_journey_id(self) -> int:
        return self.journey_id.data

    def get_event_title(self) -> str:
        return self.event_title.data

    def get_event_desc(self) -> str:
        return self.event_desc.data

    def get_start_date(self) -> datetime:
        return self.event_start_date.data
    
    def get_end_date(self) -> datetime:
        return self.event_end_date.data

    def get_location(self) -> str:
        return self.event_location.data
    
    def get_event_photos(self) -> List[FileStorage]:
        return self.event_photo_ids
    

class EditEventRequest(AddEventRequest):

    event_id: IntegerField = IntegerField('event_id', validators = [
        DataRequired(message = 'invalid event id'),
        NumberRange(min = 1, message = 'invalid event id')
    ])

    def get_event_id(self) -> int:
        return self.event_id.data


class EventDeleteRequest(Form):

    journey_id: IntegerField = IntegerField('journey_id', validators = [
        DataRequired(message = 'invalid journet id'),
        NumberRange(min = 1, message = 'invalid journey id')
    ])

    event_id: IntegerField = IntegerField('event_id', validators = [
        DataRequired(message = 'invalid event id'),
        NumberRange(min = 1, message = 'invalid event id')
    ])

    def get_journey_id(self) -> int:
        return self.journey_id.data

    def get_event_id(self) -> int:
        return self.event_id.data
    
class EventPhotoAddRequest(Form):

    event_id: IntegerField = IntegerField('event_id', validators = [
        Optional()
    ])

    event_photo: FileField = FileField('event_photo', validators = [
        Optional()
    ])

    def get_event_id(self) -> int:
        return self.event_id.data
    
    def get_event_photo(self) -> FileStorage:
        return self.event_photo.data