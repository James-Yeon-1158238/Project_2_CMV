from wtforms import Form, StringField
from wtforms.validators import DataRequired, Regexp, Optional

from app.constant.user_role import Role
from app.constant.user_status import UserStatus


class RegisterRequest(Form):

    user_name: StringField = StringField('user_name', validators = [DataRequired(message = 'invalid user name input')])
    password: StringField = StringField('password', validators = [
        DataRequired(message = 'invalid password input'),
        Regexp(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", message = 'invalid password input')
    ])
    email: StringField = StringField('email', validators = [
        DataRequired(message = 'invalid user email input'),
        Regexp(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", message = 'invalid email input')
    ])
    first_name: StringField = StringField('first_name', validators = [], default = '')
    last_name: StringField = StringField('last_name', validators = [], default = '')
    location: StringField = StringField('location', validators = [], default = '')
    description: StringField = StringField('description', validators = [], default = '')
    role: StringField = StringField('role', default = 'traveller')
    status: StringField = StringField('status', default = 'active')

    def get_user_name(self) -> str:
        return self.user_name.data
    
    def get_password(self) -> str:
        return self.password.data
    
    def get_first_name(self) -> str:
        return self.first_name.data
    
    def get_last_name(self) -> str:
        return self.last_name.data
    
    def get_email(self) -> str:
        return self.email.data

    def get_location(self) -> str:
        return self.location.data
    
    def get_desc(self) -> str:
        return self.description.data
    
    def get_role(self) -> Role:
        return Role.of(self.role.data)
    
    def get_user_status(self) -> Role:
        return UserStatus.of(self.status.data)


class LoginRequest(Form):

    user_name = StringField('user_name', validators = [DataRequired(message = 'invalid user name input')])
    password = StringField('password', validators = [
        DataRequired(message = 'invalid password input'),
        Regexp(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", message = 'invalid password input')
    ])

    def get_user_name(self) -> str:
        return self.user_name.data
    
    def get_password(self) -> str:
        return self.password.data
