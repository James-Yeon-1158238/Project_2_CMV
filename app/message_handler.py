from app import get_connection
from datetime import datetime


def get_senders_for_user(user_id: int) -> list:
    """
    Gets a list of users who have exchanged messages with the current user.
    Also returns how many unread messages each sender has sent.

    Args:
        user_id (int): The ID of the current user.

    Returns:
        list: A list of users with the latest message time and unread message count.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            u.user_id AS sender_id,
            u.user_name AS sender_name,
            u.user_fname AS sender_fname,
            u.user_lname AS sender_lname,
            u.user_photo AS sender_photo,
            MAX(m.sent_at) AS last_sent,
            SUM(
                CASE 
                    WHEN m.recipient_id = %s 
                         AND m.sender_id = u.user_id 
                         AND m.is_read = FALSE 
                    THEN 1 ELSE 0 
                END
            ) AS unread_count
        FROM PRIVATE_MESSAGES m
        JOIN USERS u
          ON u.user_id IN (m.sender_id, m.recipient_id)
        WHERE (m.sender_id = %s OR m.recipient_id = %s)
          AND u.user_id != %s
        GROUP BY u.user_id, u.user_name, u.user_fname, u.user_lname, u.user_photo
        ORDER BY last_sent DESC
    """, (user_id, user_id, user_id, user_id))
    senders = cur.fetchall()
    cur.close()
    return senders




def get_conversation(user_id: int, sender_id: int) -> tuple[list, str]:
    """
    Loads all messages between the current user and another user.
    Also marks messages as read if they were received by the current user.

    Args:
        user_id (int): The ID of the current (logged-in) user.
        sender_id (int): The ID of the other user in the chat.

    Returns:
        tuple: A list of messages and the sender's username for display.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        UPDATE PRIVATE_MESSAGES
        SET is_read = TRUE
        WHERE sender_id = %s AND recipient_id = %s AND is_read = FALSE
    """, (sender_id, user_id))
    conn.commit()

    cur.execute("""
        SELECT PRIVATE_MESSAGES.*, 
               USERS.user_name AS sender_username,
               USERS.user_fname AS sender_fname, 
               USERS.user_lname AS sender_lname
        FROM PRIVATE_MESSAGES
        JOIN USERS ON USERS.user_id = PRIVATE_MESSAGES.sender_id
        WHERE (PRIVATE_MESSAGES.sender_id = %s AND PRIVATE_MESSAGES.recipient_id = %s)
           OR (PRIVATE_MESSAGES.sender_id = %s AND PRIVATE_MESSAGES.recipient_id = %s)
        ORDER BY PRIVATE_MESSAGES.sent_at ASC
    """, (sender_id, user_id, user_id, sender_id))

    raw_messages = cur.fetchall()
    selected_messages = []
    selected_sender_name = None

    for msg in raw_messages:
        selected_messages.append({
            "message_id": msg["message_id"],
            "sender_username": msg["sender_username"],
            "sender_fname": msg["sender_fname"],
            "sender_lname": msg["sender_lname"],
            "sent_at": msg["sent_at"],
            "message_text": msg["message_text"],
            "is_from_me": msg["sender_id"] == user_id
        })

    if not selected_messages:
        cur.execute("SELECT user_name FROM USERS WHERE user_id = %s", (sender_id,))
        row = cur.fetchone()
        selected_sender_name = row["user_name"] if row else "Unknown"
    else:
        selected_sender_name = (
            selected_messages[0]["sender_username"]
            if not selected_messages[0]["is_from_me"]
            else "You"
        )

    cur.close()
    return selected_messages, selected_sender_name


def send_private_message(sender_id: int, recipient_id: int, message_text: str) -> None:
    """
    Sends a private message from one user to another.
    The new message is marked as unread by default.

    Args:
        sender_id (int): ID of the user sending the message.
        recipient_id (int): ID of the user receiving the message.
        message_text (str): The message content.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO PRIVATE_MESSAGES (sender_id, recipient_id, message_text, sent_at, is_read)
        VALUES (%s, %s, %s, %s, FALSE)
    """, (sender_id, recipient_id, message_text.strip(), datetime.now()))
    conn.commit()
    cur.close()

def count_unread_messages(user_id: int) -> int:
    """
    Counts how many messages the user has received but not read yet.

    Args:
        user_id (int): ID of the user checking for unread messages.

    Returns:
        int: Total number of unread messages.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM PRIVATE_MESSAGES
        WHERE recipient_id = %s AND is_read = FALSE
    """, (user_id,))
    count = cur.fetchone()[0]
    cur.close()
    return count
