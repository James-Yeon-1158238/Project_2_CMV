from typing import Callable

from app import T, get_connection
from app.dao import user_repo, user_view_repo
from app.dao.example import Example, ExampleMatcher, LogicMode, MatchMode
from app.dao.model.user import User, UserView
from typing import Callable, List

from app.exception.custom_error import ArgumentError


class UserService:
    
    def list_users(self, query_str: str, convert: Callable[[User], T]) -> List[User]:
        matcher: ExampleMatcher = ExampleMatcher()

        if query_str:
            matcher.with_match_mode("user_name", MatchMode.CONTAINS, logic = LogicMode.OR)
            matcher.with_match_mode("user_email", MatchMode.CONTAINS, logic = LogicMode.OR)
            matcher.with_match_mode("user_fname", MatchMode.CONTAINS, logic = LogicMode.OR)
            matcher.with_match_mode("user_lname", MatchMode.CONTAINS, logic = LogicMode.OR)
            matcher.with_match_mode("user_full_name", MatchMode.CONTAINS, logic = LogicMode.OR)
        example: Example = Example(
            probe = UserView(None, query_str, query_str, None, query_str, query_str, None, None, None, None, None, None, query_str), 
            matcher = matcher
        )
        return user_view_repo.find_by(example, lambda q: q.sort('user_name', 'ASC').project(convert))
    
    def update_user_role(self, user_id: int, new_role: str) -> None:
        user = user_repo.find_by_user_id(user_id)
        user.user_role = new_role
        user_repo.save_or_update(user)

    def update_user_status(self, user_id: int, new_status: str) -> None:
        user = user_repo.find_by_user_id(user_id)
        user.user_status = new_status
        user_repo.save_or_update(user)


    def update_user_profile(self, user_id: int, update_data: dict) -> dict:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # check that user_name is unique
        cur.execute(
            "SELECT user_id FROM USERS WHERE user_name = %s AND user_id != %s",
            (update_data["user_name"], user_id)
        )
        if cur.fetchone():
            cur.close()
            raise ArgumentError("Username already taken.")

        # check that email is unique
        cur.execute(
            "SELECT user_id FROM USERS WHERE user_email = %s AND user_id != %s",
            (update_data["user_email"], user_id)
        )
        if cur.fetchone():
            cur.close()
            raise ArgumentError("Email already in use.")

        # lists to keep all updates
        fields = []
        values = []

        for field in ["user_name", "user_email", "user_fname", "user_lname", "user_location", "user_description", "user_status", "user_role", "user_photo"]:
            if field in update_data:
                fields.append(f"{field} = %s")
                values.append(update_data[field])

        if not fields:
            cur.close()
            raise ArgumentError("No fields to update.")

        # add user_id at the end of all parameter list
        values.append(user_id)

        sql = f"""
            UPDATE USERS
            SET {', '.join(fields)}
            WHERE user_id = %s
        """
        cur.execute(sql, tuple(values))
        conn.commit()
        cur.close()

        updated_user = user_repo.find_by_user_id(user_id)
        return {
            "user_id": updated_user.user_id,
            "user_name": updated_user.user_name,
            "user_email": updated_user.user_email,
            "user_fname": updated_user.user_fname,
            "user_lname": updated_user.user_lname,
            "user_location": updated_user.user_location,
            "user_role": updated_user.user_role,
            "user_status": updated_user.user_status,
            "user_photo": updated_user.user_photo,
            "user_description": updated_user.user_description
        }

    def admin_update_user_profile(self, user_id: int, update_data: dict) -> dict:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        fields = []
        values = []

        # update only allowed information
        if "user_description" in update_data:
            fields.append("user_description = %s")
            values.append(update_data["user_description"])

        if "user_status" in update_data:
            fields.append("user_status = %s")
            values.append(update_data["user_status"])

        if "user_role" in update_data:
            fields.append("user_role = %s")
            values.append(update_data["user_role"])

        if "user_photo" in update_data:
            # might be empty (to dlete ptoto)
            fields.append("user_photo = %s")
            values.append(update_data["user_photo"])

        if not fields:
            cur.close()
            raise ArgumentError("No fields to update.")

        sql = f"""
            UPDATE USERS
            SET {', '.join(fields)}
            WHERE user_id = %s
        """
        values.append(user_id)
        cur.execute(sql, tuple(values))
        conn.commit()
        cur.close()

        # return updated data
        updated_user = user_repo.find_by_user_id(user_id)

        return {
            "user_id": updated_user.user_id,
            "user_name": updated_user.user_name,
            "user_email": updated_user.user_email,
            "user_fname": updated_user.user_fname,
            "user_lname": updated_user.user_lname,
            "user_location": updated_user.user_location,
            "user_role": updated_user.user_role,
            "user_status": updated_user.user_status,
            "user_description": updated_user.user_description,
            "user_photo": updated_user.user_photo,
        }
