from app import get_connection

def toggle_like_dislike(user_id, target_type, target_id, is_like):
    """
    Toggles a like/dislike for a given target by the user.
    Returns a dict with current status and counts.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Check existing like/dislike
    cur.execute("""
        SELECT like_id, is_like
        FROM LIKES
        WHERE user_id = %s AND target_type = %s AND target_id = %s
    """, (user_id, target_type, target_id))
    existing = cur.fetchone()

    action = None

    if existing:
        if existing["is_like"] == is_like:
            # Clicked same button again → remove
            cur.execute("DELETE FROM LIKES WHERE like_id = %s", (existing["like_id"],))
            action = "removed"
        else:
            # Switch like <-> dislike
            cur.execute("""
                UPDATE LIKES SET is_like = %s, created_at = NOW()
                WHERE like_id = %s
            """, (is_like, existing["like_id"]))
            action = "switched"
    else:
        # Add new like or dislike
        cur.execute("""
            INSERT INTO LIKES (user_id, target_type, target_id, is_like)
            VALUES (%s, %s, %s, %s)
        """, (user_id, target_type, target_id, is_like))
        action = "added"

    # Get updated counts
    cur.execute("""
        SELECT
            SUM(CASE WHEN is_like THEN 1 ELSE 0 END) AS like_count,
            SUM(CASE WHEN NOT is_like THEN 1 ELSE 0 END) AS dislike_count
        FROM LIKES
        WHERE target_type = %s AND target_id = %s
    """, (target_type, target_id))
    counts = cur.fetchone()

    conn.commit()
    cur.close()

    return {
        "action": action,
        "is_like": is_like,
        "like_count": counts["like_count"] or 0,
        "dislike_count": counts["dislike_count"] or 0,
    }
