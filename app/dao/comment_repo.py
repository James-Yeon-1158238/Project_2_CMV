from typing import List
from app.dao.enhance import BaseRepository
from app.dao.model.comment import Comment
from mysql.connector import pooling
from app import get_connection

class CommentRepository(BaseRepository[Comment]):

    def __init__(self, connection_pool: pooling.MySQLConnectionPool):
        super().__init__("COMMENTS", Comment, connection_pool)

    def find_visible_by_event_id(self, event_id: int) -> List[Comment]:
        return self.findByEventIdAndIsHiddenOrderByCreatedAtAsc(event_id, False)

    def _get_connection(self):
        return get_connection()

    def has_user_reported(self, comment_id: int, user_id: int) -> bool:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM COMMENT_REPORTS WHERE comment_id = %s AND reported_by = %s", (comment_id, user_id))
        result = cur.fetchone()
        cur.close()
        return result is not None

    def insert_comment_report(self, comment_id: int, user_id: int, reason: str):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO COMMENT_REPORTS (comment_id, reported_by, report_reason)
            VALUES (%s, %s, %s)
        """, (comment_id, user_id, reason))
        conn.commit()
        cur.close()

    def get_reported_comment_ids_by_user(self, user_id: int) -> set:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT comment_id FROM COMMENT_REPORTS WHERE reported_by = %s", (user_id,))
        result = set(row[0] for row in cur.fetchall())
        cur.close()
        return result
