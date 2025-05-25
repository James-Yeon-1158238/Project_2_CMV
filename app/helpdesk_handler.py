from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore
from app import get_connection
from decimal import Decimal

from app import get_connection
from datetime import datetime

def create_helpdesk_request(user_id, user_name, email, help_type, category, title, description):
    """
    Inserts a new helpdesk request into the database.
    Also inserts an initial 'create' history record into HELPDESK_HISTORY.
    """
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now()

# Step 1: Insert new request into the HELPDESK table
    query = """
        INSERT INTO HELPDESK (
            request_user_id, request_user_name,
            request_email, request_type,
            request_category, request_title,
            request_description, created_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
    cur.execute(query, (
        user_id, user_name, email,
        help_type, category,
        title, description,
        now, now
    ))

    # Step 2: Retrieve the last inserted request_id (AUTO_INCREMENT value)
    request_id = cur.lastrowid

    # Step 3: Copy the inserted request into the HELPDESK_HISTORY table
    history_query = """
        INSERT INTO HELPDESK_HISTORY (
            request_id, request_user_id, request_user_name, request_email,
            request_type, request_category, request_title, request_description,
            request_status, request_priority, request_assigned_to, request_assigned_name,
            request_take_pending, request_take_candidate_id,
            request_created_at, request_updated_at
        )
        SELECT
            request_id, request_user_id, request_user_name, request_email,
            request_type, request_category, request_title, request_description,
            request_status, request_priority, request_assigned_to, request_assigned_name,
            request_take_pending, request_take_candidate_id,
            created_at, updated_at
        FROM HELPDESK
        WHERE request_id = %s
    """
    cur.execute(history_query, (request_id,))

    # Step 4: Commit all changes to the database
    conn.commit()

def edit_helpdesk_request(request_id, request_description):
    """
    Inserts a new comment into the HELPDESK_COMMENT table.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Step 1: UPDATE HELPDESK   
      
    query = """
    UPDATE HELPDESK 
        SET request_description = %s
        WHERE request_id = %s;
        """
    cur.execute(query, (request_description, request_id))
    
    
    history_query = """
            INSERT INTO HELPDESK_HISTORY (
            request_id,request_user_id,request_user_name,request_email,request_type,
            request_category,request_title,request_description,request_status,
            request_priority,request_assigned_to,request_assigned_name,
            request_created_at,request_updated_at
        )
        SELECT
            r.request_id,r.request_user_id,r.request_user_name,r.request_email,
            r.request_type,r.request_category,r.request_title,r.request_description,
            r.request_status,r.request_priority,r.request_assigned_to,r.request_assigned_name,
            r.created_at,r.updated_at
        FROM HELPDESK r
        WHERE r.request_id = %s;
    """
    cur.execute(history_query, ( request_id,)) 

    
    conn.commit()


def add_helpdesk_comment(request_id, comment_user, comment_text, request_status):
    """
    Inserts a new comment into the HELPDESK_COMMENT table.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    if request_status is None:
        request_status = "new"

    query = """
        INSERT INTO HELPDESK_COMMENTS (
            request_id, comment_user, comment_text, request_status
        )
        VALUES (%s, %s, %s, %s)
    """
    cur.execute(query, (request_id, comment_user, comment_text, request_status))
    conn.commit()


    cur.execute("SELECT request_status FROM HELPDESK WHERE request_id = %s", (request_id,))
    current_status = cur.fetchone()
    current_status_1= current_status[0]

    query = """
        UPDATE HELPDESK
            SET request_status = %s
        Where request_id = %s
    """
    cur.execute(query, (request_status, request_id))


    if current_status_1 != request_status:
        cur.execute("""
            INSERT INTO HELPDESK_HISTORY (
                request_id, request_user_id, request_user_name, request_email,
                request_type, request_category, request_title, request_description, request_status,
                request_priority, request_assigned_to, request_assigned_name, request_created_at,
                request_updated_at, request_take_pending, request_take_candidate_id
                )SELECT
                h.request_id,  h.request_user_id,  h.request_user_name,  h.request_email,
                h.request_type,  h.request_category,  h.request_title,  h.request_description,
                h.request_status,  h.request_priority,  h.request_assigned_to,  h.request_assigned_name,
                h.created_at,  h.updated_at,  h.request_take_pending,  h.request_take_candidate_id
                FROM HELPDESK h
                WHERE h.request_id = %s
            """, (request_id,))

    
    conn.commit()
    

def update_helpdesk_status_and_assign(request_id, new_status, changed_by_user_id, changed_by_user_name):
    """
    Updates the status of a helpdesk request and logs the change in the HELPDESK_HISTORY table.
    Only proceeds if the status has actually changed.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    now = datetime.now()

    try:
        # Step 1: Retrieve current status
        cur.execute("SELECT request_status FROM HELPDESK WHERE request_id = %s", (request_id,))
        current = cur.fetchone()

        if not current:
            raise Exception("Helpdesk request not found")

        previous_status = current["request_status"]

        # Step 2: Update only if the status has changed
        if previous_status != new_status:
            # Update HELPDESK table
            cur.execute("""
                UPDATE HELPDESK
                SET request_status = %s, updated_at = %s
                WHERE request_id = %s
            """, (new_status, now, request_id))

            # Insert history record
            cur.execute("""
                INSERT INTO HELPDESK_HISTORY (
                    request_id, changed_by_user_id, changed_by_user_name,
                    change_type, previous_status, new_status,
                    change_comment, changed_at
                )
                VALUES (%s, %s, %s, 'status_change', %s, %s, %s, %s)
            """, (
                request_id, changed_by_user_id, changed_by_user_name,
                previous_status, new_status,
                f"Status changed from {previous_status} to {new_status}",
                now
            ))

            # Commit the transaction
            conn.commit()

    finally:
        # Always close the cursor and connection
        cur.close()


def update_request_assigned_to(request_id: int, assigned_to: int, assigned_name: str):
    """
    Assigns a helpdesk request to a user (typically an admin).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE HELPDESK
        SET request_assigned_to = %s, request_assigned_name = %s, updated_at = NOW()
        WHERE request_id = %s
    """, (assigned_to, assigned_name, request_id))
    conn.commit()


# def get_request_with_comments(request_id: int, assigned_to: int, assigned_name: str):
#     """
#     Assigns a helpdesk request to a user (typically an admin).
#     """
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute("""
#         UPDATE helpdesk
#         SET request_assigned_to = %s, request_assigned_name = %s, updated_at = NOW()
#         WHERE request_id = %s
#     """, (assigned_to, assigned_name, request_id))
#     conn.commit()

