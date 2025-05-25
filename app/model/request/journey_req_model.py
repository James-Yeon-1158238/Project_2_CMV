from datetime import date
from wtforms import DateField, FileField, Form, IntegerField, StringField
from wtforms.validators import DataRequired, NumberRange
from werkzeug.datastructures import FileStorage


class CreateJourneyRequest(Form):

    title: StringField = StringField('title', validators = [DataRequired(message = 'invalid title input')])
    description: StringField = StringField('description', validators = [DataRequired(message = 'invalid description input')])
    start_date: DateField = DateField('start_date', format = '%Y-%m-%d', validators = [DataRequired(message = 'invalid start date input')])
    status: StringField = StringField('status', default = 'private')

    def get_title(self) -> str:
        return self.title.data

    def get_desc(self) -> str:
        return self.description.data

    def get_start_date(self) -> date:
        return self.start_date.data
    
    def get_status(self) -> str:
        return self.status.data


class EditJourneyRequest(CreateJourneyRequest):

    journey_id: IntegerField = IntegerField('journey_id', validators = [
        DataRequired(message = 'invalid journet id'),
        NumberRange(min = 1, message = 'invalid journey id')
    ])

    def get_journey_id(self) -> int:
        return self.journey_id.data
    

class DeleteJourneyRequest(Form):

    journey_id: IntegerField = IntegerField('journey_id', validators = [
        DataRequired(message = 'invalid journet id'),
        NumberRange(min = 1, message = 'invalid journey id')
    ])

    def get_journey_id(self) -> int:
        return self.journey_id.data
