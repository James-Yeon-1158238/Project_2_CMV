from app import get_connection


def get_user_like_activity(user_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Total likes
    cur.execute("""
        SELECT COUNT(*) AS total_likes
        FROM LIKES
        WHERE user_id = %s AND is_like = TRUE
    """, (user_id,))
    total_likes = cur.fetchone()["total_likes"]

    # Last 5 events liked by user
    cur.execute("""
        SELECT E.event_id, E.event_title, J.journey_title
        FROM LIKES L
        JOIN EVENTS E ON L.target_id = E.event_id
        JOIN JOURNEYS J ON E.journey_id = J.journey_id
        WHERE L.user_id = %s AND L.target_type = 'event'
        ORDER BY L.created_at DESC
        LIMIT 5
    """, (user_id,))
    recent_liked_events = cur.fetchall()

    # ✅ Last 5 comments the user liked
    cur.execute("""
        SELECT C.comment_text, C.created_at, E.event_title
        FROM LIKES L
        JOIN COMMENTS C ON L.target_id = C.comment_id
        JOIN EVENTS E ON C.event_id = E.event_id
        WHERE L.user_id = %s AND L.target_type = 'comment' AND C.is_hidden = FALSE
        ORDER BY L.created_at DESC
        LIMIT 5
    """, (user_id,))
    recent_liked_comments = cur.fetchall()

    cur.close()
    return {
        "total_likes": total_likes,
        "recent_liked_events": recent_liked_events,
        "recent_liked_comments": recent_liked_comments
    }


def get_user_comment_activity(user_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Total comments
    cur.execute("""
        SELECT COUNT(*) AS total_comments
        FROM COMMENTS
        WHERE user_id = %s
    """, (user_id,))
    total_comments = cur.fetchone()["total_comments"]

    # 5 latest comments
    cur.execute("""
        SELECT C.comment_text, C.created_at, E.event_title
        FROM COMMENTS C
        JOIN EVENTS E ON C.event_id = E.event_id
        WHERE C.user_id = %s
        ORDER BY C.created_at DESC
        LIMIT 5
    """, (user_id,))
    recent_comments = cur.fetchall()

    cur.close()
    return {
        "total_comments": total_comments,
        "recent_comments": recent_comments
    }

def get_recent_journeys(user_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT journey_id, journey_title, updated_at, journey_status
        FROM JOURNEYS
        WHERE user_id = %s AND journey_status IN ('public', 'share')
        ORDER BY updated_at DESC
        LIMIT 3
    """, (user_id,))
    journeys = cur.fetchall()

    cur.close()
    return journeys
