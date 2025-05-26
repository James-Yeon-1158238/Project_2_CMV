from sched import Event
from typing import List
from flask import (
    Blueprint,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from datetime import datetime, timedelta

# type: ignore
from dateutil.relativedelta import relativedelta  # type: ignore

from app import T, get_connection
from app.constant.journey_status import JourneyStatus
from app.constant.user_role import Role
from app.dao import user_repo
from app.model.response.event_res_model import EventResponse
from app.exception.custom_error import AccessDeclinedError, ArgumentError
from app.dao.model.user import User
from mysql.connector import cursor
from flask import request
from flask import Blueprint, render_template
from app.provider.context.event_context import EventContext
from app.session_holder import SessionHolder
from app import subscription_handler
from app.dao import comment_repo
from app.dao.model.comment import Comment
from app import get_connection
from app.dao.model.journey import Journey
from app.provider.service import event_service
from app.services import journey_service, user_service
from app.subscription_handler import create_subscription, get_current_subscription_status, days_until_subscription_ends, is_subscription_expiring_soon
from app.message_handler import get_senders_for_user, get_conversation, send_private_message
from app.message_handler import count_unread_messages

###########################
from app.helpdesk_handler import create_helpdesk_request, add_helpdesk_comment, update_helpdesk_status_and_assign,edit_helpdesk_request


from werkzeug.utils import secure_filename
import os
from app.recent_activity import (
        get_user_like_activity,
        get_user_comment_activity,
        get_recent_journeys,
    )

from app.like_utils import toggle_like_dislike

"""
Defines route handlers for rendering HTML pages in a Flask web application.

This class sets up a Flask Blueprint named "page" and maps various URL paths
to their respective HTML templates for user authentication, issue tracking,
and user management.
"""

page: Blueprint = Blueprint("page", __name__)


@page.get("/login")
def login_page() -> str:
    """
    Renders the login page.

    Returns:
        str: The rendered HTML content of the login page.
    """
    if SessionHolder.current_login():
        return redirect(url_for("page.home_page"))
    return render_template("login.html")


@page.get("/register")
def register_page() -> str:
    """
    Renders the user registration page.

    Returns:
        str: The rendered HTML content of the signup page.
    """
    return render_template("signup.html")


@page.get("/home_page")
def home_page() -> str:
    user = SessionHolder.current_login()

    subscription_status = None
    subscription_expiring_soon = None
    days_until_expiry = None

    if user:
        subscription_status = get_current_subscription_status(user.user_id)
        subscription_expiring_soon = is_subscription_expiring_soon(user.user_id)
        days_until_expiry = days_until_subscription_ends(user.user_id)

    cur = get_connection().cursor(dictionary=True)
    cur.execute("""
        SELECT announcement_title 
        FROM ANNOUNCEMENTS 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    latest = cur.fetchone()
    cur.close()

    return render_template(
        "home.html",
        user=user,
        latest_announcement=latest,
        subscription_status=subscription_status,
        subscription_expiring_soon=subscription_expiring_soon,
        days_until_expiry=days_until_expiry,
    )


@page.get("/accounts")
def accounts_page() -> str:
    """
    Renders users accounts page.

    Returns:
        str: The rendered HTML content of the users accounts page.
    """
    user = SessionHolder.current_login()
    if not user or user.user_role not in ["admin", "itadmin"]:    
        raise AccessDeclinedError("You are not allowed to view this page.")

    search_query = request.args.get("search_query", default=None, type=str)
    if search_query:
        users = user_service.list_users(search_query, lambda x: x)
    else:
        users = user_service.list_users(None, lambda x: x)

    managing_users = [u for u in users if u.user_role in ("admin", "editor","moderator","itadmin")]
    travellers = [u for u in users if u.user_role == "traveller"]

    cur = get_connection().cursor(dictionary=True)
    cur.execute("""
        SELECT plan_id, plan_name, plan_duration, plan_price
        FROM PLANS
        WHERE plan_price > 0
        ORDER BY plan_duration
    """)
    gift_plans = cur.fetchall()

    cur.close()

    user_roles = ["admin", "editor", "traveller", "moderator"]
    user_statuses = ["active", "blocked", "banned"]
    success = request.args.get("success") == "true"

    return render_template(
        "user_accounts_management.html",
        user=user,
        managing_users=managing_users,
        travellers=travellers,
        user_roles=user_roles,
        success=success,
        user_statuses=user_statuses,
        search_query=search_query,
        gift_plans=gift_plans,
    )


@page.post("/accounts/update-role")
def update_user_role_page() -> Response:
    user = SessionHolder.current_login()
    if not user or user.user_role != "admin":
        raise AccessDeclinedError("Only admins can change roles")

    user_id = request.form.get("user_id", type=int)
    new_role = request.form.get("new_role")

    if not user_id or not new_role:
        raise ArgumentError("Missing user_id or new_role")

    user_service.update_user_role(user_id, new_role)
    return redirect(url_for("page.accounts_page", success="true"))


@page.post("/accounts/update-status")
def update_user_staus_page() -> Response:
    user = SessionHolder.current_login()
    if not user or user.user_role not in ("admin", "editor", "itadmin"):
        raise AccessDeclinedError("Only admins and editors can change status")

    user_id = request.form.get("user_id", type=int)
    new_status = request.form.get("new_status")

    if not user_id or not new_status:
        raise ArgumentError("Missing user_id or new_status")

    user_service.update_user_status(user_id, new_status)
    return redirect(url_for("page.accounts_page", success="true"))


@page.get("/events/<int:journey_id>")
def events_page(journey_id: int) -> str:
    """
    Renders events page.

    Returns:
        str: The rendered HTML content of the event page.
    """
    user: User = SessionHolder.current_login()
    if user is None:
        return redirect(url_for("page.login_page"))
    
    journey: Journey = journey_service.get_journey(journey_id)
    is_owner: bool = journey.user_id == user.user_id if journey else False
    creator = user_repo.find_by_user_id(journey.user_id)
    creator_name = creator.user_name if creator else "Unknown"

    context: EventContext = EventContext()
    context.current_user = user   
    events: List[EventResponse] = event_service.list_events(journey_id, lambda j, e, p: EventResponse(True, True, e.event_id, e.journey_id, e.event_title, e.event_description, e.event_start_date, e.event_end_date, e.event_location, p), context)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    for event in events:
        # Get total like count
        cur.execute("""
            SELECT COUNT(*) AS like_count
            FROM LIKES
            WHERE target_type = 'event' AND target_id = %s
        """, (event.event_id,))
        like_row = cur.fetchone()
        event.like_count = like_row["like_count"] if like_row else 0

        # Check if user liked
        cur.execute("""
            SELECT 1 FROM LIKES
            WHERE target_type = 'event' AND target_id = %s AND user_id = %s
        """, (event.event_id, user.user_id))
        liked = cur.fetchone() is not None
        event.liked_by_user = liked

    cur.close()

    event_comments = {}
    cur = get_connection().cursor(dictionary=True)

    for e in events:
        comments = comment_repo.find_visible_by_event_id(e.event_id)
        reported_ids = comment_repo.get_reported_comment_ids_by_user(user.user_id)
        comment_details = []

        for c in comments:
            commenter = user_repo.find_by_user_id(c.user_id)

            # number of likes
            cur.execute("SELECT COUNT(*) AS count FROM LIKES WHERE target_type = 'comment' AND target_id = %s AND is_like = TRUE", (c.comment_id,))
            like_count = cur.fetchone()["count"]

            # number of dislikes
            cur.execute("SELECT COUNT(*) AS count FROM LIKES WHERE target_type = 'comment' AND target_id = %s AND is_like = FALSE", (c.comment_id,))
            dislike_count = cur.fetchone()["count"]

            # is liked
            cur.execute("""
                SELECT 1 FROM LIKES
                WHERE target_type = 'comment' AND target_id = %s AND user_id = %s AND is_like = TRUE
            """, (c.comment_id, user.user_id))
            liked = cur.fetchone() is not None

            # is disliked
            cur.execute("""
                SELECT 1 FROM LIKES
                WHERE target_type = 'comment' AND target_id = %s AND user_id = %s AND is_like = FALSE
            """, (c.comment_id, user.user_id))
            disliked = cur.fetchone() is not None

            comment_details.append({
                "comment_id": c.comment_id,
                "user_name": commenter.user_name if commenter else "Unknown",
                "text": c.comment_text,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
                "like_count": like_count,
                "dislike_count": dislike_count,
                "liked_by_user": liked,
                "disliked_by_user": disliked,
                "has_reported": c.comment_id in reported_ids
            })


        event_comments[e.event_id] = comment_details

    cur.close()

    return render_template(
        "events.html", events=events, journey=journey, journey_id=journey_id, is_owner=is_owner, creator_name=creator_name, event_comments=event_comments
    )


@page.get("/my_journeys_paging")
def my_journeys_paging() -> str:
    """
    Renders the my_journeys_paging page with pagination support.

    Returns:
        str: The rendered HTML content of the my_journey page.
    """
    user_id = SessionHolder.current_login().user_id
    user_role = SessionHolder.current_login().user_role

    # Get page number from request, default to 1
    page = request.args.get("page", 1, type=int)
    per_page = 3  # Number of items per page
    offset = (page - 1) * per_page

    cur: cursor.MySQLCursor = get_connection().cursor(dictionary=True, buffered=False)

    cur.execute(
        f"""
                SELECT journey_id, journey_title, journey_description, 
                journey_start_date, journey_photo_url,
                journey_status 
                FROM JOURNEYS                 
                ORDER BY journey_start_date DESC 
                LIMIT {per_page} OFFSET {offset};
                """
    )

    my_journeys_list = cur.fetchall()

    # Get total journey count for pagination controls
    cur.execute("SELECT COUNT(*) as total FROM JOURNEYS ;")
    total_count = cur.fetchone()["total"]
    total_pages = (total_count + per_page - 1) // per_page  # Calculate total pages

    return render_template(
        "my_journeys_panging.html",
        my_journeys_list=my_journeys_list,
        page=page,
        total_pages=total_pages,
    )


@page.get("/my_journeys")
def my_journeys() -> str:
    """
    Renders the my_journey page.
    Returns:
        str: The rendered HTML content of the my_journey page.
    """

    cur: cursor.MySQLCursor = get_connection().cursor(dictionary=True, buffered=False)
    user = SessionHolder.current_login()

    if not user:
        return render_template("login.html")

    user_id = user.user_id
    user_role = user.user_role

    # Get user's journeys
    cur.execute("""
        SELECT journey_id, journey_title, journey_description, updated_at,
               journey_start_date, journey_photo_url, journey_status
        FROM JOURNEYS
        WHERE user_id = %s
        ORDER BY updated_at DESC;
    """, (user_id,))
    my_journeys_list = cur.fetchall()

    # Check premium access based on active premier record
    cur.execute("""
        SELECT 1
        FROM PREMIER_USERS
        WHERE user_id = %s AND premier_start_at <= NOW() AND premier_end_at >= NOW()
        LIMIT 1;
    """, (user_id,))
    is_premium = cur.fetchone()

    cur.close()

    # If user is premium or a staff member, show card view
    if is_premium or user_role in ("admin", "editor"):
        return render_template("my_journeys_card.html", my_journeys_list=my_journeys_list)

    # Otherwise, show basic view
    return render_template("my_journeys.html", my_journeys_list=my_journeys_list)



@page.get("/my_journeys_search")
def my_journeys_search() -> str:
    """
    Renders the my_journeys_search page.
    Returns:
        str: The rendered HTML content of the my_journeys page.
    """
    user = SessionHolder.current_login()
    if not user:
        return render_template("login.html")

    user_id = user.user_id
    user_role = user.user_role
    journey_title = request.args.get("journey_title")

    cur: cursor.MySQLCursor = get_connection().cursor(dictionary=True, buffered=False)

    # Fetch journeys based on search
    qstr = """
        SELECT journey_id, journey_title, journey_description, updated_at,
               journey_start_date, journey_photo_url, journey_status
        FROM JOURNEYS
        WHERE journey_title LIKE %s AND user_id = %s
        ORDER BY updated_at DESC
    """
    cur.execute(qstr, (f"%{journey_title}%", user_id))
    my_journeys_list = cur.fetchall()

    # Check for current premium status
    cur.execute("""
        SELECT 1
        FROM PREMIER_USERS
        WHERE user_id = %s
          AND premier_start_at <= NOW()
          AND premier_end_at >= NOW()
        LIMIT 1;
    """, (user_id,))
    is_premium = cur.fetchone()

    cur.close()

    if is_premium or user_role in ("admin", "editor"):
        return render_template("my_journeys_card.html", my_journeys_list=my_journeys_list)

    return render_template("my_journeys.html", my_journeys_list=my_journeys_list)





@page.get("/all_journeys")
def all_journeys() -> str:
    """
    Renders the all_journey page.

    page

    Returns:
        str: The rendered HTML content of the my_journey page.
    """

    # traveller,editor,admin need to split the work
    check_date = datetime.now() - timedelta(days=1)
    cur: cursor.MySQLCursor = get_connection().cursor(dictionary=True, buffered=False)
    user_id = SessionHolder.current_login().user_id
    user_role = SessionHolder.current_login().user_role

    # session, traveller, edit, admin
    if user_id == "None":

        return redirect("/login")

    else:

        cur.execute(
            """
                 SELECT journey_id, journey_title, journey_description, updated_at, journey_photo_url,
                 journey_start_date,
                 journey_status FROM JOURNEYS where journey_status in('public', 'share')
                 order by updated_at desc ;
                 """
        )

    all_journeys_list = cur.fetchall()

    return render_template(
        "all_journeys.html",
        all_journeys_list=all_journeys_list,
        user_role=user_role,
        check_date=check_date,
    )


@page.post("/all_journeys_search")
def all_journeys_search() -> str:
    """
    Renders the all_journeys_search page.

    page 11

    Returns:
        str: The rendered HTML content of the my_journey page.
    """

    # journey_title = request.args.get("journey_title")
    # journey_description = request.args.get("journey_description")
    journey_title = request.form["journey_title"]
    journey_description = request.form["journey_description"]
    user_id = SessionHolder.current_login().user_id
    user_role = SessionHolder.current_login().user_role
    check_date = datetime.now() - timedelta(days=1)

    # traveller,editor,admin need to split the work

    cur: cursor.MySQLCursor = get_connection().cursor(dictionary=True, buffered=False)

    if journey_description == "":

        qstr = """
                    SELECT journey_id, journey_title, journey_description, updated_at,
                     journey_start_date, journey_photo_url,
                    journey_status FROM JOURNEYS where journey_title like %s 
                    and journey_status in('public', 'share') 
                    order by updated_at desc"""

        params = (f"%{journey_title}%",)
        cur.execute(qstr, params)
        all_journeys_list = cur.fetchall()
        return render_template(
            "all_journeys.html",
            all_journeys_list=all_journeys_list,
            user_role=user_role, check_date=check_date,
        )

    elif journey_title == "":

        qstr = """
                    SELECT journey_id, journey_title, journey_description, updated_at,
                    journey_start_date, journey_photo_url,
                    journey_status FROM JOURNEYS where journey_description like %s 
                    and  journey_status in('public', 'share')
                    order by updated_at desc"""

        params = (f"%{journey_description}%",)
        cur.execute(qstr, params)
        all_journeys_list = cur.fetchall()
        return render_template(
            "all_journeys.html",
            all_journeys_list=all_journeys_list,
            user_role=user_role, check_date=check_date,
        )

    else:

        qstr = """
                    SELECT journey_id, journey_title, journey_description, updated_at,
                    journey_start_date, journey_photo_url,
                    journey_status FROM JOURNEYS where journey_title like %s 
                    and journey_description like %s 
                    and journey_status in('public', 'share') order by updated_at desc"""

        params = (
            f"%{journey_title}%",
            f"%{journey_description}%",
        )
        cur.execute(qstr, params)
        all_journeys_list = cur.fetchall()
        return render_template(
            "all_journeys.html",
            all_journeys_list=all_journeys_list,
            user_role=user_role, check_date=check_date
        )


@page.get("/profile")
def profile_page() -> str:
    user = SessionHolder.current_login()
    if not user:
        return redirect(url_for("page.login_page"))

    # Allow admin to view other users' profiles
    view_user = user
    user_id = request.args.get("user_id", type=int)
    if user_id and user.user_role == "admin":
        target_user = user_repo.find_by_user_id(user_id)
        if not target_user:
            return "User not found", 404
        view_user = target_user

    # Subscription status (for currently viewed user)
    subscription_status = get_current_subscription_status(view_user.user_id)
    subscription_expiring_soon = is_subscription_expiring_soon(view_user.user_id)
    days_until_expiry = days_until_subscription_ends(view_user.user_id)

    # Success flags
    info_success = request.args.get("info_updated") == "true"
    photo_success = request.args.get("photo_updated") == "true"
    password_success = request.args.get("password_updated") == "true"

    # Error flags
    password_error = request.args.get("password_error")
    error_message = request.args.get("error_message")

    password_error_msg = None
    if password_error == "mismatch":
        password_error_msg = "Passwords do not match."
    elif password_error == "incorrect":
        password_error_msg = "Current password is incorrect."

    return render_template(
        "profile.html",
        user=view_user,
        info_success=info_success,
        photo_success=photo_success,
        password_success="Password updated successfully" if password_success else None,
        password_error=password_error_msg,
        error_message=error_message,
        subscription_status=subscription_status,
        subscription_expiring_soon=subscription_expiring_soon,
        days_until_expiry=days_until_expiry,
    )


@page.get("/profile/subscriptions/<int:user_id>")
def profile_subscriptions(user_id: int):
    conn = get_connection()
    if conn is None:
        return "Database connection failed", 500

    try:
        cur = conn.cursor(dictionary=True)

        # get all data about subscriptions from database
        cur.execute("""
            SELECT 
                SUBSCRIPTIONS.subscription_id,
                SUBSCRIPTIONS.start_date,
                SUBSCRIPTIONS.end_date,
                SUBSCRIPTIONS.is_gifted,
                PLANS.plan_name,
                PLANS.plan_duration,
                PLANS.plan_price,
                PAYMENTS.payment_date,
                PAYMENTS.gst_amount,
                PAYMENTS.payment_total,
                PAYMENTS.card_number_last4,
                PAYMENTS.billing_country
            FROM SUBSCRIPTIONS
            LEFT JOIN PLANS ON SUBSCRIPTIONS.plan_id = PLANS.plan_id
            LEFT JOIN PAYMENTS ON SUBSCRIPTIONS.subscription_id = PAYMENTS.subscription_id
            WHERE SUBSCRIPTIONS.user_id = %s
            ORDER BY SUBSCRIPTIONS.start_date DESC;
        """, (user_id,))
        subscriptions = cur.fetchall()

        today = datetime.today().date()
        current_subs = [
            s for s in subscriptions
            if not s["end_date"] or s["end_date"] >= today
        ]

        # get subscription end date
        cur.execute("""
            SELECT premier_end_at 
            FROM PREMIER_USERS 
            WHERE user_id = %s
        """, (user_id,))
        row = cur.fetchone()
        max_end_date = row["premier_end_at"] if row else None

        user = SessionHolder.current_login()
        cur.close()

    except Exception as e:
        print("Error fetching subscriptions:", e)
        return "Failed to retrieve subscriptions", 500

    return render_template(
        "profile_subscriptions.html",
        subscriptions=subscriptions,
        current_subs=current_subs,  
        max_end_date=max_end_date,
        user=user
    )



@page.get("/profile/likes/<int:user_id>")
def profile_likes(user_id):
    # render likes/comments
    return render_template("profile_likes.html", user_id=user_id)

@page.post("/my_journey_update")
def my_journey_update() -> str:
    """
    Renders the my_journey_update page.

    page

    Returns:
        str: The rendered HTML content of the my_journey page.
    """

    # traveller,editor,admin need to split the work

    cur: cursor.MySQLCursor = get_connection().cursor(dictionary=True, buffered=False)

    user_id = SessionHolder.current_login().user_id
    journey_status = request.form["journey_status"]
    journey_journey_id = request.form["journey_id"]

    # Correct the SQL query to use 'UPDATE' instead of 'UPDAET'
    qstr = """ 
    UPDATE JOURNEYS 
    SET journey_status = %s 
    WHERE user_id = %s and journey_id = %s;
    """

    params = (journey_status, user_id, journey_journey_id)
    cur.execute(qstr, params)

    get_connection().commit()

    # Close the cursor (best practice)
    cur.close()

    return redirect("/my_journeys")

@page.get("/access_denied")
def access_denied_page() -> str:
    reason = request.args.get("reason", "Access denied.")
    return render_template("access_denied.html", reason=reason)

def calculate_price_incl_gst(price_str):
    if not price_str.startswith("NZ $"):
        return "Free"
    price = float(price_str.replace("NZ $", ""))
    price_incl = price * 1.15
    return f"NZ ${price_incl:.2f}"

@page.get("/subscription")
def subscription_page() -> str:
    user = SessionHolder.current_login()
    if not user or user.user_role != "traveller":
        return redirect(url_for("page.access_denied_page", reason="Only travellers can view subscription options."))

    error_message = request.args.get("error_message") 

    cur = get_connection().cursor(dictionary=True)
    cur.execute("""
        SELECT 
            plan_id,
            plan_name,
            plan_duration,
            plan_price,
            plan_discount
        FROM PLANS
        ORDER BY plan_duration
    """)

    plans = cur.fetchall()

    # add price with GST
    for plan in plans:
        price = float(plan["plan_price"])
        gst_price = price * 1.15
        plan["price_incl_gst"] = round(gst_price, 2)
        plan["price_display"] = "Free" if price == 0 else f"NZ ${gst_price:.2f}"

    return render_template("subscription.html", subscription_plans=plans, error_message=error_message)


@page.post("/subscription/purchase")
def purchase_subscription():
    user = SessionHolder.current_login()
    if not user or user.user_role != "traveller":
        return redirect(url_for("page.access_denied_page", reason="Only travellers can purchase subscriptions."))

    form = request.form
    plan_id = int(form.get("plan_id"))
    billing_country = form.get("billing_country")

    try:
        subscription_handler.create_subscription(user, plan_id, billing_country)
    except ValueError as e:
         return redirect(url_for("page.subscription_page", error_message=str(e))) 

    return redirect(url_for("page.profile_subscriptions", user_id=user.user_id))


@page.get("/announcements")
def announcements_page() -> str:
    user = SessionHolder.current_login()
    if not user:
        return redirect(url_for("page.login_page"))

    cur = get_connection().cursor(dictionary=True)
    cur.execute("""
        SELECT announcement_id, announcement_title, announcement_content, created_at
        FROM ANNOUNCEMENTS
        ORDER BY created_at DESC
    """)
    announcements = cur.fetchall()

    latest = announcements[0] if announcements else None

    cur.close()

    return render_template("announcements.html",
        user=user,
        announcements=announcements,
        latest_announcement=latest
    )


@page.get("/announcements/manage")
def manage_announcements_page() -> str:
    user = SessionHolder.current_login()
    if not user or user.user_role not in ("admin", "editor"):
        return redirect(url_for("page.access_denied_page", reason="Only admins or editors can manage announcements."))

    cur = get_connection().cursor(dictionary=True)
    cur.execute("""
        SELECT announcement_id, announcement_title, announcement_content, created_at
        FROM ANNOUNCEMENTS
        ORDER BY created_at DESC
    """)
    announcements = cur.fetchall()
    cur.close()

    return render_template("manage_announcements.html", user=user, announcements=announcements)

@page.get("/announcements/create")
def create_announcement_form() -> str:
    user = SessionHolder.current_login()
    if not user or user.user_role not in ("admin", "editor"):
        return redirect(url_for("page.access_denied_page", reason="Only admins or editors can create announcements."))
    return render_template("announcement_form.html", user=user)


@page.post("/announcements/create")
def create_announcement_submit() -> Response:
    user = SessionHolder.current_login()
    if not user or user.user_role not in ("admin", "editor"):
        return redirect(url_for("page.access_denied_page"))

    title = request.form.get("title")
    content = request.form.get("content")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    if not title or not content or not start_time:
        return redirect(url_for("page.create_announcement_form"))

    cur = get_connection().cursor()
    cur.execute("""
        INSERT INTO ANNOUNCEMENTS (announcement_title, announcement_content, announcement_type, user_id, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (title, content, "General", user.user_id, start_time, end_time or None))
    get_connection().commit()
    cur.close()

    return redirect(url_for("page.manage_announcements_page"))


@page.get("/announcements/edit/<int:announcement_id>")
def edit_announcement_form(announcement_id: int) -> str:
    user = SessionHolder.current_login()
    if not user or user.user_role not in ("admin", "editor"):
        return redirect(url_for("page.access_denied_page"))

    cur = get_connection().cursor(dictionary=True)
    cur.execute("SELECT * FROM ANNOUNCEMENTS WHERE announcement_id = %s", (announcement_id,))
    ann = cur.fetchone()
    cur.close()

    if not ann:
        return "Announcement not found", 404

    return render_template("announcement_edit_form.html", announcement=ann)


@page.post("/announcements/edit/<int:announcement_id>")
def edit_announcement_submit(announcement_id: int) -> Response:
    user = SessionHolder.current_login()
    if not user or user.user_role not in ("admin", "editor"):
        return redirect(url_for("page.access_denied_page"))

    title = request.form.get("title")
    content = request.form.get("content")

    cur = get_connection().cursor()
    cur.execute("""
        UPDATE ANNOUNCEMENTS 
        SET announcement_title = %s, announcement_content = %s 
        WHERE announcement_id = %s
    """, (title, content, announcement_id))
    get_connection().commit()
    cur.close()

    return redirect(url_for("page.manage_announcements_page"))

@page.get("/announcements/delete/<int:announcement_id>")
def delete_announcement(announcement_id: int) -> Response:
    user = SessionHolder.current_login()
    if not user or user.user_role not in ("admin", "editor"):
        return redirect(url_for("page.access_denied_page"))

    cur = get_connection().cursor()
    cur.execute("DELETE FROM ANNOUNCEMENTS WHERE announcement_id = %s", (announcement_id,))
    get_connection().commit()
    cur.close()

    return redirect(url_for("page.manage_announcements_page"))

def get_latest_announcement():
    """
    Gets the most recent announcement from the database.
    Returns a dict with title and content, or None if there are no announcements.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT announcement_id, announcement_title, announcement_content, created_at
        FROM ANNOUNCEMENTS
        ORDER BY created_at DESC
        LIMIT 1
    """)
    latest = cur.fetchone()
    cur.close()
    return latest

@page.post("/admin/subscription/gift")
def gift_subscription():
    """
    Allows an admin to grant a gifted subscription to a Traveller.
    Sends an automatic message after successful creation.
    """
    user = SessionHolder.current_login()
    if not user or user.user_role != "admin":
        raise AccessDeclinedError("Only admins can grant subscriptions.")

    traveller_id = request.form.get("user_id", type=int)
    plan_id = request.form.get("plan_id", type=int)

    if not traveller_id or not plan_id:
        raise ArgumentError("Missing user_id or plan_id")

    target_user = user_repo.find_by_user_id(traveller_id)
    if not target_user:
        raise ArgumentError("User not found")

    try:
        create_subscription(
            user=target_user,
            plan_id=plan_id,
            billing_country="NZ",
            is_gifted=True
        )

        # message about gift
        message_text = (
            "You’ve just received a gifted premium subscription from our admin team!\n\n"
            "Enjoy full access to Travel Journal premium features.\n"
            "Happy travels!"
        )

        send_private_message(
            sender_id=user.user_id,
            recipient_id=target_user.user_id,
            message_text=message_text
        )

    except Exception as e:
        print("Gift subscription error:", e)
        return redirect(url_for("page.accounts_page", success="false"))

    return redirect(url_for("page.accounts_page", success="true"))


#### James

@page.post("/premium_journey_create")
def Premium_journey_create() -> dict:
    """
    Handles the creation of a new journey.

    Returns:
        dict: JSON response with success or error message.
    """
    from werkzeug.utils import secure_filename

    user = SessionHolder.current_login()
    if user is None or user.user_id == "None":
        return {"error": "Unauthorized access."}, 401

    try:
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        start_date = request.form.get("start_date", "").strip()
        photo_file = request.files.get("journey_photo")

        # Validation
        if not title or len(title.split()) < 2:
            return {"error": "Title must contain at least two words."}, 400
        if not description or len(description.split()) < 5:
            return {"error": "Description must contain at least five words."}, 400

        # File handling
        photo_url = None
        if photo_file and photo_file.filename != "":
            filename = secure_filename(photo_file.filename)
            #upload_path = os.path.join("/app/static/premium", filename)
            upload_path = os.path.join("app","static", "premium", filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            photo_file.save(upload_path)
            # photo_url = f"../static/premium/{filename}"
            photo_url = url_for('static', filename=f"premium/{filename}")
            

        # Insert into DB
        conn = get_connection()
        cur: cursor.MySQLCursor = conn.cursor()

        insert_sql = """
            INSERT INTO JOURNEYS (
                user_id, journey_title, journey_description,
                journey_start_date, journey_photo_url, journey_status, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        cur.execute(insert_sql, (
            user.user_id,
            title,
            description,
            start_date,
            photo_url,
            "private"  
        ))
        conn.commit()

        return {"message": "Journey created successfully."}, 201

    except Exception as e:
        return {"error": str(e)}, 500
    
    
@page.post("/premium_journey_delete")
def premium_journey_delete() -> dict:
    """
    Deletes a premium journey (and its associated events).

    Returns:
        dict: JSON response with success or error message.
    """
    user = SessionHolder.current_login()
    if user is None or user.user_id == "None":
        return {"error": "Unauthorized access."}, 401

    try:
        journey_id = request.form.get("journey_id", type=int)
        if not journey_id:
            return {"error": "Missing journey ID."}, 400

        conn = get_connection()
        cur: cursor.MySQLCursor = conn.cursor(dictionary=True)

        # Check if the journey exists and belongs to the current user
        cur.execute("SELECT user_id FROM JOURNEYS WHERE journey_id = %s", (journey_id,))
        journey = cur.fetchone()

        if not journey:
            return {"error": "Journey not found."}, 404
        if journey["user_id"] != user.user_id:
            return {"error": "Permission denied."}, 403

        # Optional: Delete related events
        cur.execute("DELETE FROM EVENTS WHERE journey_id = %s", (journey_id,))

        # Delete the journey
        cur.execute("DELETE FROM JOURNEYS WHERE journey_id = %s", (journey_id,))
        conn.commit()
        cur.close()

        return {"message": "Journey deleted successfully."}, 200

    except Exception as e:
        return {"error": str(e)}, 500



@page.post("/premium_journey_edit")
def premium_journey_edit() -> dict:
    """
    Handles the editing of an existing journey.
    Returns:
        dict: JSON response with success or error message.
    """
    from werkzeug.utils import secure_filename

    user = SessionHolder.current_login()
    if user is None or user.user_id == "None":
        return {"error": "Unauthorized access."}, 401

    try:
        journey_id = request.form.get("journey_id", type=int)
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        start_date = request.form.get("start_date", "").strip()
        photo_file = request.files.get("journey_photo")

        if not journey_id:
            return {"error": "Missing journey ID."}, 400
        if not title or len(title.split()) < 2:
            return {"error": "Title must contain at least two words."}, 400
        if not description or len(description.split()) < 5:
            return {"error": "Description must contain at least five words."}, 400

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # Check ownership
        cur.execute("SELECT user_id FROM JOURNEYS WHERE journey_id = %s", (journey_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Journey not found."}, 404
        if row["user_id"] != user.user_id:
            return {"error": "Permission denied."}, 403

        # Handle new photo upload
        photo_url = None
        if photo_file and photo_file.filename != "":
            filename = secure_filename(photo_file.filename)
            upload_path = os.path.join("app", "static", "premium", filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            photo_file.save(upload_path)
            photo_url = f"../static/premium/{filename}"

        # Update query
        update_query = """
            UPDATE JOURNEYS
            SET journey_title = %s,
                journey_description = %s,
                journey_start_date = %s,
                updated_at = NOW()
                {photo_clause}
            WHERE journey_id = %s
        """.format(photo_clause=", journey_photo_url = %s" if photo_url else "")

        if photo_url:
            cur.execute(update_query, (title, description, start_date, photo_url, journey_id))
        else:
            cur.execute(update_query, (title, description, start_date, journey_id))

        conn.commit()
        cur.close()

        return {"message": "Journey updated successfully."}, 200

    except Exception as e:
        return {"error": str(e)}, 500
    
@page.get("/my_journeys_card")
def my_journeys_card() -> str:
    """
    Renders the my_journey page.

    page

    Returns:
        str: The rendered HTML content of the my_journey page.
    """

    # traveller,editor,admin need to split the work

    cur: cursor.MySQLCursor = get_connection().cursor(dictionary=True, buffered=False)
    user_id = SessionHolder.current_login().user_id
    user_role = SessionHolder.current_login().user_role

    # session, traveller, edit, admin
    if user_id == "None":
        return render_template("login.html")

    else:
        cur.execute(
            """
                 SELECT journey_id, journey_title, journey_description, updated_at,
                 journey_start_date, journey_photo_url,
                 journey_status FROM JOURNEYS where user_id =%s  order by updated_at desc ;
                 """,
            (user_id,),
        )

    my_journeys_list = cur.fetchall()

    return render_template("my_journeys_card.html", my_journeys_list=my_journeys_list)   

@page.get("/index")
def public_index_page() -> str:
    """
    Public index page showing public journeys for non-logged-in users.
    """
    cur = get_connection().cursor(dictionary=True)


    cur.execute("""   
       SELECT j.journey_id, j.journey_title, j.journey_description, 
              j.journey_photo_url, j.journey_start_date, j.updated_at, j.journey_status, p.premier_end_at,
              u.user_name,  u.user_fname, u.user_lname
        FROM JOURNEYS j
            JOIN PREMIER_USERS p ON j.user_id = p.user_id
            JOIN USERS u ON j.user_id = u.user_id
            WHERE j.journey_status = 'share'
            AND p.premier_end_at > CURRENT_DATE
            ORDER BY j.updated_at DESC
            LIMIT 12;                 
    """)

    public_journeys = cur.fetchall()
    cur.close()

    return render_template("index.html", public_journeys=public_journeys)


@page.get("/")
def root_redirect() -> str:
    """
    Redirect to index page for public users or home page for logged-in users.
    """
    user = SessionHolder.current_login()
    if user:
        return redirect(url_for("page.home_page"))  # Login home
    return redirect(url_for("page.public_index_page"))  # Non Login index 

@page.get("/profile/messages/<int:user_id>")
def profile_messages(user_id: int):
    """
    Renders the personal messages page with chat and sender list.
    """

    user = SessionHolder.current_login()
    if not user or user.user_id != user_id:
        return redirect(url_for("page.access_denied_page", reason="Unauthorized access"))

    sender_id = request.args.get("sender_id", type=int)
    subscription_status = get_current_subscription_status(user.user_id)

    senders = get_senders_for_user(user.user_id)

    selected_messages = []
    selected_sender_name = None

    if sender_id is not None:

        selected_messages, selected_sender_name = get_conversation(user.user_id, sender_id)

    return render_template(
        "profile_messages.html",
        user=user,
        senders=senders,
        selected_messages=selected_messages,
        selected_sender_name=selected_sender_name,
        active_sender_id=sender_id,
        subscription_status=subscription_status
    )

@page.context_processor
def inject_unread_messages():
    """
    This function makes the unread message count available in all HTML templates.
    It checks if the user is logged in and returns the number of unread messages.
    
    Returns:
        dict: A dictionary with the key 'unread_messages_count' for use in templates.
    """
    user = SessionHolder.current_login()
    if not user:
        return {}

    count = count_unread_messages(user.user_id)
    return {"unread_messages_count": count}

@page.post("/profile/messages/send")
def send_message() -> Response:
    """
    Handles sending a private message from one user to another.
    Only users with a subscription can send messages.
    """
    user = SessionHolder.current_login()
    if not user:
        return redirect(url_for("page.login_page"))

    recipient_id = request.form.get("recipient_id", type=int)
    message_text = request.form.get("message_text", "").strip()

    if not recipient_id or not message_text:
        return redirect(url_for("page.profile_messages", user_id=user.user_id, sender_id=recipient_id))

    # Check subscription
    status = get_current_subscription_status(user.user_id)
    if status == "free":
        return redirect(url_for("page.access_denied_page", reason="Only subscribed users can send messages."))

    # Save the message
    send_private_message(sender_id=user.user_id, recipient_id=recipient_id, message_text=message_text)

    return redirect(url_for("page.profile_messages", user_id=user.user_id, sender_id=recipient_id))

@page.post("/profile/messages/delete")
def delete_message() -> Response:
    user = SessionHolder.current_login()
    if not user:
        return redirect(url_for("page.login_page"))

    message_id = request.form.get("message_id", type=int)
    sender_id = request.form.get("sender_id", type=int)

    if not message_id:
        return redirect(url_for("page.profile_messages", user_id=user.user_id, sender_id=sender_id))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT sender_id, recipient_id 
        FROM PRIVATE_MESSAGES 
        WHERE message_id = %s
    """, (message_id,))
    message = cur.fetchone()

    if message and (user.user_id == message["sender_id"] or user.user_id == message["recipient_id"]):
        cur.execute("DELETE FROM PRIVATE_MESSAGES WHERE message_id = %s", (message_id,))
        conn.commit()

    cur.close()
    return redirect(url_for("page.profile_messages", user_id=user.user_id, sender_id=sender_id))


@page.get("/public_users")
def public_users_page() -> str:
    """
    Shows the page with a list of public users.
    Allows search by username, first name, last name, full name, or location.
    """
    user = SessionHolder.current_login()
    if not user:
        return redirect(url_for("page.login_page"))

    raw_query = request.args.get("search_query", "").strip()
    cur = get_connection().cursor(dictionary=True)

    if raw_query:
        like_query = "%" + raw_query + "%"
        cur.execute("""
            SELECT user_id, user_name, user_fname, user_lname, user_location, user_photo, user_role
            FROM USERS
            WHERE is_public = TRUE AND (
                user_name LIKE %s OR
                user_fname LIKE %s OR
                user_lname LIKE %s OR
                user_location LIKE %s OR
                CONCAT(user_fname, ' ', user_lname) LIKE %s
            )
            ORDER BY user_name
        """, (like_query, like_query, like_query, like_query, like_query))
    else:
        cur.execute("""
            SELECT user_id, user_name, user_fname, user_lname, user_location, user_photo, user_role
            FROM USERS
            WHERE is_public = TRUE
            ORDER BY user_name
        """)

    public_users = cur.fetchall()
    cur.close()

    return render_template("public_users.html", users=public_users, search_query=raw_query)

@page.get("/user/<int:user_id>")
def user_public_profile(user_id: int) -> str:
    """
    Renders a public user profile page with recent activity blocks,
    depending on the user's visibility settings.
    """
    user = SessionHolder.current_login()
    if not user:
        return redirect(url_for("page.login_page"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get public profile info (only if is_public = TRUE)
    cur.execute("""
        SELECT user_id, user_name, user_fname, user_lname, user_location, 
               user_description, user_photo, user_role
        FROM USERS
        WHERE user_id = %s AND is_public = TRUE
    """, (user_id,))
    public_user = cur.fetchone()

    if not public_user:
        cur.close()
        return "User not found or not public", 404

    # Get visibility settings for this user's profile blocks
    cur.execute("""
        SELECT pb.block_name, pvs.is_visible
        FROM PROFILE_VISIBILITY_SETTINGS pvs
        JOIN PROFILE_BLOCKS pb ON pvs.block_id = pb.block_id
        WHERE pvs.user_id = %s
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()

    # Convert list of rows into a dictionary like {'liked_events': True, ...}
    visibility = {row["block_name"]: row["is_visible"] for row in rows}

    # Stats and activity blocks
    subscription_status = get_current_subscription_status(user.user_id)
    like_stats = get_user_like_activity(user_id)
    comment_stats = get_user_comment_activity(user_id)
    recent_journeys = get_recent_journeys(user_id)

    return render_template(
        "user_public_profile.html",
        profile=public_user,
        subscription_status=subscription_status,
        like_stats=like_stats,
        comment_stats=comment_stats,
        recent_journeys=recent_journeys,
        visibility=visibility
    )


@page.get("/moderation_comments")
def moderation_comments_page() -> str:
    user = SessionHolder.current_login()
    if not user or user.user_role not in ["moderator","editor", "admin"]:
        return redirect(url_for("page.access_denied_page"))

    cur = get_connection().cursor(dictionary=True)

    cur.execute("""
        SELECT r.report_id, r.comment_id, r.report_reason AS reason, r.reported_at AS created_at,
            r.escalated_to_admin AS escalated,
            c.comment_text, c.is_hidden,
            u.user_name AS reporter,
            cu.user_name AS commenter_name
        FROM COMMENT_REPORTS r
        JOIN COMMENTS c ON r.comment_id = c.comment_id
        JOIN USERS u ON r.reported_by = u.user_id
        JOIN USERS cu ON c.user_id = cu.user_id
        WHERE c.is_hidden = FALSE
        AND r.moderated_by IS NULL
        ORDER BY r.reported_at DESC
        """)
    active_reports = cur.fetchall()

    cur.execute("""
        SELECT r.report_id, r.comment_id, r.report_reason AS reason, r.reported_at AS created_at,
            r.escalated_to_admin AS escalated,
            r.moderated_at,
            c.comment_text, c.is_hidden,
            u.user_name AS reporter,
            cu.user_name AS commenter_name, 
            m.user_name AS moderated_by_name  
        FROM COMMENT_REPORTS r
        JOIN COMMENTS c ON r.comment_id = c.comment_id
        JOIN USERS u ON r.reported_by = u.user_id
        JOIN USERS cu ON c.user_id = cu.user_id          
        LEFT JOIN USERS m ON r.moderated_by = m.user_id
        WHERE r.moderated_by IS NOT NULL
        AND c.is_hidden = TRUE
        ORDER BY r.reported_at DESC
    """)

    hidden_reports = cur.fetchall()

    ignored_reports = []
    if user.user_role in ["editor", "admin"]:
        cur.execute("""
            SELECT r.report_id, r.comment_id, r.report_reason AS reason, r.reported_at AS created_at,
                r.escalated_to_admin AS escalated,
                c.comment_text, c.is_hidden,
                u.user_name AS reporter,
                cu.user_name AS commenter_name,
                m.user_name AS moderated_by_name,
                r.moderated_at
            FROM COMMENT_REPORTS r
            JOIN COMMENTS c ON r.comment_id = c.comment_id
            JOIN USERS u ON r.reported_by = u.user_id
            JOIN USERS cu ON c.user_id = cu.user_id
            LEFT JOIN USERS m ON r.moderated_by = m.user_id
            WHERE r.moderated_by IS NOT NULL AND c.is_hidden = FALSE
            ORDER BY r.reported_at DESC
        """)
    ignored_reports = cur.fetchall()

    cur.close()
    return render_template("moderation_comments.html", reports=active_reports, hidden_reports=hidden_reports, ignored_reports=ignored_reports, current_user=user)


@page.post("/moderator/hide_comment")
def hide_comment():
    user = SessionHolder.current_login()
    if not user or user.user_role not in ["moderator", "editor", "admin"]:
        raise AccessDeclinedError("Only moderators, editors and admins can hide comments.")

    comment_id = request.form.get("comment_id", type=int)
    if not comment_id:
        raise ArgumentError("Missing comment_id")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT report_id FROM COMMENT_REPORTS
        WHERE comment_id = %s
        ORDER BY reported_at DESC
        LIMIT 1
    """, (comment_id,))
    result = cur.fetchone()

    cur.execute("UPDATE COMMENTS SET is_hidden = TRUE WHERE comment_id = %s", (comment_id,))

    if result:
        cur.execute("""
            UPDATE COMMENT_REPORTS
            SET moderated_by = %s, moderated_at = NOW()
            WHERE report_id = %s
        """, (user.user_id, result["report_id"]))

    conn.commit()
    cur.close()
    return redirect(url_for("page.moderation_comments_page"))



@page.post("/moderator/escalate_comment")
def escalate_comment():
    user = SessionHolder.current_login()
    if not user or user.user_role != "moderator":
        raise AccessDeclinedError("Only moderators can escalate comments.")

    report_id = request.form.get("report_id", type=int)
    if not report_id:
        raise ArgumentError("Missing report_id")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE COMMENT_REPORTS
        SET escalated_to_admin = TRUE, escalated_by = %s, escalated_at = NOW()
        WHERE report_id = %s
    """, (user.user_id, report_id))
    conn.commit()
    cur.close()

    return redirect(url_for("page.moderation_comments_page"))


@page.get("/admin/escalated_reports")
def escalated_reports_page():
    user = SessionHolder.current_login()
    if not user or user.user_role != "admin":
        return redirect(url_for("page.access_denied_page"))

    cur = get_connection().cursor(dictionary=True)
    cur.execute("""
    SELECT r.report_id, r.comment_id, r.report_reason AS reason, r.reported_at AS created_at,
           c.comment_text, c.is_hidden,
           u.user_name AS reporter,
           r.reported_by AS reported_by,
           c.user_id AS commenter_id,
           cu.user_name AS commenter_name
    FROM COMMENT_REPORTS r
    JOIN COMMENTS c ON r.comment_id = c.comment_id
    JOIN USERS u ON r.reported_by = u.user_id
    JOIN USERS cu ON c.user_id = cu.user_id  
    WHERE r.escalated_to_admin = TRUE
    ORDER BY r.reported_at DESC
    """)
    reports = cur.fetchall()
    cur.close()
    return render_template("admin_escalated_reports.html", reports=reports)

@page.post("/admin/hide_comment")
def admin_hide_comment():
    user = SessionHolder.current_login()
    if not user or user.user_role != "admin":
        raise AccessDeclinedError("Only admins can hide comments.")

    comment_id = request.form.get("comment_id", type=int)
    if not comment_id:
        raise ArgumentError("Missing comment_id")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT report_id FROM COMMENT_REPORTS
        WHERE comment_id = %s
        ORDER BY reported_at DESC
        LIMIT 1
    """, (comment_id,))
    result = cur.fetchone()

    cur.execute("UPDATE COMMENTS SET is_hidden = TRUE WHERE comment_id = %s", (comment_id,))

    if result:
        cur.execute("""
            UPDATE COMMENT_REPORTS
            SET moderated_by = %s,
                moderated_at = NOW()
            WHERE report_id = %s
        """, (user.user_id, result["report_id"]))

    conn.commit()
    cur.close()
    return redirect(url_for("page.escalated_reports_page"))

@page.post("/admin/dismiss_escalation")
def dismiss_escalation():
    user = SessionHolder.current_login()
    if not user or user.user_role != "admin":
        raise AccessDeclinedError("Only admins can dismiss escalation.")

    report_id = request.form.get("report_id", type=int)
    if not report_id:
        raise ArgumentError("Missing report_id")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE COMMENT_REPORTS
        SET escalated_to_admin = FALSE, escalated_by = NULL, escalated_at = NULL
        WHERE report_id = %s
    """, (report_id,))
    conn.commit()
    cur.close()

    return redirect(url_for("page.escalated_reports_page"))

@page.post("/staff/ignore_comment", endpoint="ignore_comment")
def ignore_comment():
    user = SessionHolder.current_login()
    if not user or user.user_role not in ["admin", "editor"]:
        raise AccessDeclinedError("Only staff can ignore comments.")

    report_id = request.form.get("report_id", type=int)

    if not report_id:
        raise ArgumentError("Missing report_id")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE COMMENT_REPORTS
    SET moderated_by = %s,
        moderated_at = NOW()
    WHERE report_id = %s
    """, (user.user_id, report_id))

    conn.commit()
    cur.close()

    return redirect(url_for("page.moderation_comments_page"))

@page.post("/admin/ban_user")
def ban_user():
    user = SessionHolder.current_login()
    if not user or user.user_role != "admin":
        raise AccessDeclinedError("Only admins can ban users.")

    target_user_id = request.form.get("user_id", type=int)
    if not target_user_id:
        raise ArgumentError("Missing user_id")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE USERS SET is_banned = TRUE WHERE user_id = %s", (target_user_id,))
    conn.commit()

    send_private_message(
    sender_id=0,
    recipient_id=target_user_id,
    message_text="[ACCOUNT BAN] Your account has been banned due to violation of community guidelines."
    )

    cur.close()

    return redirect(url_for("page.escalated_reports_page"))

@page.post("/admin/send_warning", endpoint="send_warning_message")
def send_warning_message():
    user = SessionHolder.current_login()
    if not user or user.user_role != "admin":
        raise AccessDeclinedError("Only admins can send warnings.")

    comment_id = request.form.get("comment_id", type=int)
    warning_text = request.form.get("warning_text", "").strip()

    if not comment_id or not warning_text:
        raise ArgumentError("Missing comment_id or warning_text")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT user_id FROM COMMENTS WHERE comment_id = %s", (comment_id,))
    result = cur.fetchone()
    if not result:
        cur.close()
        raise ArgumentError("Comment not found")

    commenter_id = result["user_id"]

    cur.execute("""
        INSERT INTO PRIVATE_MESSAGES (sender_id, recipient_id, message_text, sent_at)
        VALUES (%s, %s, %s, NOW())
    """, (0, commenter_id, "[ADMIN WARNING] " + warning_text))

    conn.commit()
    cur.close()

    return redirect(url_for("page.escalated_reports_page"))

@page.post("/event/like")
def toggle_event_like():
    """
    Toggle like for an event.
    If user has already liked it, remove the like.
    Otherwise, add a new like.
    """
    user = SessionHolder.current_login()
    if not user:
        return jsonify({"success": False, "message": "Please log in first."}), 401

    event_id = request.form.get("event_id", type=int)
    if not event_id:
        return jsonify({"success": False, "message": "Event ID is missing."}), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Check if the like already exists
    cur.execute("""
        SELECT like_id FROM LIKES
        WHERE user_id = %s AND target_type = 'event' AND target_id = %s
    """, (user.user_id, event_id))
    existing_like = cur.fetchone()

    if existing_like:
        # Remove the existing like
        cur.execute("DELETE FROM LIKES WHERE like_id = %s", (existing_like["like_id"],))
        liked = False
    else:
        # Add a new like
        cur.execute("""
            INSERT INTO LIKES (user_id, target_type, target_id, is_like, created_at)
            VALUES (%s, 'event', %s, TRUE, NOW())
        """, (user.user_id, event_id))
        liked = True

    # Get the updated total like count
    cur.execute("""
        SELECT COUNT(*) AS like_count FROM LIKES
        WHERE target_type = 'event' AND target_id = %s
    """, (event_id,))
    result = cur.fetchone()
    like_count = result["like_count"] if result else 0

    conn.commit()
    cur.close()

    return jsonify({
        "success": True,
        "liked": liked,
        "like_count": like_count
    }), 200

@page.post("/comment/like")
def toggle_comment_like():
    user = SessionHolder.current_login()
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    comment_id = request.form.get("comment_id", type=int)
    if not comment_id:
        return jsonify({"success": False, "message": "Missing comment_id"}), 400

    result = toggle_like_dislike(user.user_id, "comment", comment_id, is_like=True)

    return jsonify({
        "success": True,
        "liked": result["action"] != "removed",
        "like_count": result["like_count"],
        "dislike_count": result["dislike_count"]
    }), 200

@page.post("/comment/dislike")
def toggle_comment_dislike():
    user = SessionHolder.current_login()
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    comment_id = request.form.get("comment_id", type=int)
    if not comment_id:
        return jsonify({"success": False, "message": "Missing comment_id"}), 400

    result = toggle_like_dislike(user.user_id, "comment", comment_id, is_like=False)

    return jsonify({
        "success": True,
        "disliked": result["action"] != "removed",
        "like_count": result["like_count"],
        "dislike_count": result["dislike_count"]
    }), 200

##################################
@page.get("/helpdesk")
def helpdesk() -> str:
    """
    Helpdesk main page route.
    - traveller: can only view their own requests
    - admin/editor/itadmin: can view all requests, status summary, and list of assignable users
    """
    user = SessionHolder.current_login()
    user_id = user.user_id
    user_role = user.user_role

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # List of helpers for assign modal (only active admins and editors)
    cur.execute("""
        SELECT user_id, user_name
        FROM USERS
        WHERE user_role in ('editor', 'admin', 'itadmin') AND user_status = 'active'
    """)
    assignable_users = cur.fetchall()

    # List of helpers for assign modal (only active admins and editors)
    cur.execute("""
        SELECT * FROM HELPDESK
        where request_take_candidate_id =%s and  request_take_pending ='1'
     """, (user_id,))

    Pending_assigns = cur.fetchall()

    
    # Status summary (for displaying status cards)
    cur.execute("SELECT * FROM HELPDESK_STATUS_SUMMARY")
    rows = cur.fetchall()
    status_summary = {
        row['request_status'].lower(): row['total_count']
        for row in rows
    }

    # Query request list based on user role
    if user_role == "traveller":
        cur.execute("""
        SELECT request_id, request_user_id, request_user_name, request_email, request_type, request_category,
               request_title, request_description, request_status, request_priority, request_assigned_name, 
               created_at, updated_at, request_take_pending, request_take_candidate_id
        FROM HELPDESK
        WHERE request_user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    elif user_role == "admin":
        cur.execute("""
            SELECT 
                h.request_id, h.request_user_id, h.request_user_name, h.request_email, h.request_type,
                h.request_category, h.request_title, h.request_description, h.request_status,
                h.request_priority, h.request_assigned_to, h.request_assigned_name, h.created_at, h.updated_at,
                h.request_take_pending, h.request_take_candidate_id,
                CASE 
                    WHEN p.user_id IS NOT NULL THEN 1
                    ELSE 0
                END AS is_premier
            FROM HELPDESK h
            LEFT JOIN PREMIER_USERS p
            ON h.request_user_id = p.user_id
            AND p.premier_start_at <= NOW()
            AND p.premier_end_at >= NOW()
            ORDER BY 
            FIELD(h.request_priority, 'high', 'medium', 'low'),
            h.created_at DESC
        """)

    else:  # editor or others
        cur.execute("""
            SELECT 
                h.request_id, h.request_user_id, h.request_user_name, h.request_email, h.request_type,
                h.request_category, h.request_title, h.request_description, h.request_status,
                h.request_priority, h.request_assigned_to, h.request_assigned_name, h.created_at, h.updated_at,
                h.request_take_pending, h.request_take_candidate_id,
                CASE 
                    WHEN p.user_id IS NOT NULL THEN 1
                    ELSE 0
                END AS is_premier
            FROM HELPDESK h
            LEFT JOIN PREMIER_USERS p
            ON h.request_user_id = p.user_id
            AND p.premier_start_at <= NOW()
            AND p.premier_end_at >= NOW()
            WHERE h.request_assigned_to = %s
            ORDER BY 
             FIELD(h.request_priority, 'high', 'medium', 'low'),
            h.created_at DESC
        """, (user_id,))


    requests = cur.fetchall()

    # Render admin template for admin/editor
    if user_role in ("admin", "editor" ,"itadmin"):
        return render_template(
            "helpdesk_management.html",
            requests=requests,
            status_summary=status_summary,
            assignable_users=assignable_users,  # Used in assign modal
            Pending_assigns = Pending_assigns
        )

    # Render default list template for traveller or other users
    return render_template("helpdesk_list.html", requests=requests)



@page.get("/helpdesk/status")
def helpdesk_status() -> str:
    """
    Public index page showing public journeys for non-logged-in users.
    """
    user_id = SessionHolder.current_login().user_id
    status = request.args.get('status')

    cur = get_connection().cursor(dictionary=True)    
    
    if status == "all":
        cur.execute("""   
            SELECT  request_id, request_user_id, request_user_name, request_email, request_type, request_category,
                    request_title, request_description, request_status, request_priority, request_assigned_name, 
                    created_at,  updated_at
                FROM HELPDESK where request_user_id = %s
                ORDER BY created_at DESC; 
                """,  (user_id,),
                )
        requests = cur.fetchall()

    else :
        cur.execute("""   
            SELECT  request_id, request_user_id, request_user_name, request_email, request_type, request_category,
                    request_title, request_description, request_status, request_priority, request_assigned_name, 
                    created_at,  updated_at
                FROM HELPDESK where request_user_id = %s and request_status=%s
                ORDER BY created_at DESC; 
                """,  (user_id, status,),
                )
        requests = cur.fetchall()
    
    return render_template("helpdesk_list.html", requests=requests)

@page.get("/helpdesk/status_staff")
def helpdesk_status_staff() -> str:
    """
    Public index page showing public journeys for non-logged-in users.
    """
    status = request.args.get("status", "all")
    premium_only = request.args.get("premium_only", False)
    user_role = session.get("user_role")

    cur = get_connection().cursor(dictionary=True)    

    cur.execute("""
                SELECT * FROM HELPDESK_STATUS_SUMMARY;
             """
            )

    rows = cur.fetchall()
    status_summary = {
    row['request_status'].lower(): row['total_count']
    for row in rows } 
    
    query = """
                SELECT h.request_id, h.request_user_id, h.request_user_name, h.request_email, h.request_type, 
                h.request_category, h.request_title, h.request_description, h.request_status, 
                h.request_priority,  h.request_assigned_name, h.created_at, h.updated_at,
            CASE 
                WHEN p.user_id IS NOT NULL THEN 1
                ELSE 0
            END AS is_premier
            FROM   HELPDESK h
            LEFT JOIN 
                PREMIER_USERS p
                ON h.request_user_id = p.user_id
                AND p.premier_start_at <= NOW()
                AND p.premier_end_at >= NOW()
            """
    filters = []
    params = []

    if status.lower() != "all":
                filters.append("request_status = %s")
                params.append(status)
    if premium_only:
                filters.append("p.user_id IS NOT NULL")
    if filters:
                query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY FIELD(h.request_priority, 'high', 'medium', 'low'), created_at DESC"
  
    cur.execute(query, params) 
    requests = cur.fetchall()
    
    return render_template("helpdesk_management.html", requests=requests ,status=status ,status_summary=status_summary)

@page.get("/api/helpdesk/by_status")
def get_requests_by_status():
    status = request.args.get("status", "new")
    cur = get_connection().cursor(dictionary=True)    
    cur.execute("""
        SELECT request_type, request_category, request_title, request_description, request_assigned_name
        FROM HELPDESK
        WHERE request_status = %s
        ORDER BY created_at DESC
    """, (status,))
    rows = cur.fetchall()
    return jsonify(requests=rows)




@page.post('/helpdesk/create_request')
def create_request():

    user = SessionHolder.current_login()

    form = request.form
    create_helpdesk_request(
        user_id=user.user_id,
        user_name=form['request_user_name'],
        email=form['request_email'],
        help_type=form['request_type'],
        category=form['request_category'],
        title=form['request_title'],
        description=form['request_description']
    )
    return redirect('/helpdesk')

@page.post('/helpdesk/edit_request')
def edit_request():
    user = SessionHolder.current_login()
    form = request.form

    request_id = form['request_id']  # 

    edit_helpdesk_request(
        request_id=request_id,
        request_description=form['request_description']
    )

    return redirect(f'/helpdesk/detail?request_id={request_id}')


@page.get("/helpdesk/detail")
def help_detail():
    
    user = SessionHolder.current_login()
    user_role = SessionHolder.current_login().user_role

    if not user:
        return redirect("/login")

    request_id = request.args.get('request_id')

    cur = get_connection().cursor(dictionary=True)


    cur.execute("""
        SELECT  request_id, request_user_id, request_user_name, request_email, request_type, request_category,
                request_title, request_description, request_status, request_priority, request_assigned_name, 
                created_at,  updated_at
            FROM HELPDESK where request_id= %s
            ORDER BY created_at DESC; 
             """,  (request_id,),
            )

    detail = cur.fetchone()
 
    cur.execute("""
        SELECT  comment_id, request_id, user_id, comment_user, comment_text, created_at, request_status
            FROM HELPDESK_COMMENTS where request_id= %s
            ORDER BY created_at DESC; 
             """,  (request_id,),
            )

    comments = cur.fetchall()
   
    cur.execute("""
        SELECT user_id, user_name, user_fname, user_lname, user_role
         FROM USERS 
        WHERE user_role != 'traveller';
             """
            )

    user_roles = cur.fetchall()

    cur.close()

    if user_role in ("admin", "editor", "itadmin"):
        return render_template("helpdesk_detail_management.html", detail=detail, user=user, comments=comments, user_roles=user_roles)
    return render_template("helpdesk_detail.html", detail=detail, user=user, comments=comments, user_role=user_role)


@page.post("/helpdesk/add_comment")
def add_comment():
    user = SessionHolder.current_login()
    if not user:
        return {"error": "Unauthorized"}, 403

    form = request.form
    request_id = form.get("request_id")
    comment_text = form.get("comment_text")
    request_status = form.get("request_status")

    if not request_id or not comment_text:
        return {"error": "Missing required fields"}, 400

    add_helpdesk_comment(
        request_id=request_id,
        comment_user=user.user_name,
        comment_text=comment_text,
        request_status = request_status
    )

    return redirect(f"/helpdesk/detail?request_id={request_id}")

@page.get("/helpdesk/history")
def history_data():
    request_id = request.args.get("request_id")

    if not request_id:
        return jsonify({"error": "Missing request_id"}), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT 
                history_id, request_id, request_user_id, request_user_name,  
                request_email, request_type, request_category, request_title,  
                request_description, request_status, request_priority,  
                request_assigned_to, request_assigned_name, 
                request_created_at, request_updated_at, history_created_at
            FROM HELPDESK_HISTORY 
            WHERE request_id = %s
            ORDER BY history_created_at DESC;
        """, (request_id,))

        history = cur.fetchall()
        return jsonify({"history": history})
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch history: {e}")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        cur.close()


@page.post("/helpdesk/assign")
def assign_request():

    request_id = request.form.get("request_id", type=int)
    assign_to = request.form.get("assign_to", type=int)

    cur = get_connection().cursor()
    cur.execute("SELECT user_name FROM USERS WHERE user_id = %s", (assign_to,))
    result = cur.fetchone()
    assigned_name = result[0] if result else None

    cur.execute("""
        UPDATE HELPDESK
        SET request_take_pending = 1,
            request_take_candidate_id = %s
        WHERE request_id = %s
    """, (assign_to, request_id))

    get_connection().commit()
    return redirect("/helpdesk")


@page.post("/helpdesk/respond_take")
def respond_take():
    user = SessionHolder.current_login()
    data = request.get_json()
    request_id = data.get("request_id")
    action = data.get("action")  # "accept" or "decline"

    cur = get_connection().cursor(dictionary=True)

    if action == "accept":
        # GET
        cur.execute("SELECT user_name FROM USERS WHERE user_id = %s", (user.user_id,))
        assigned_name = cur.fetchone()['user_name']

        cur.execute("""
            UPDATE HELPDESK
            SET request_assigned_to = %s,
                request_assigned_name = %s,
                request_take_pending = 0,
                request_take_candidate_id = NULL,
                request_status = 'open'
            WHERE request_id = %s
        """, (user.user_id, assigned_name, request_id))

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


    elif action == "decline":
        # DECLINE
        cur.execute("""
            UPDATE HELPDESK
            SET request_take_pending = 0,
                request_take_candidate_id = NULL
            WHERE request_id = %s
        """, (request_id,))

    get_connection().commit()
    return jsonify(success=True)


@page.get('/helpdesk/status/<status>')
def helpdesk_status_modal(status):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
    SELECT 
        h.request_user_name, h.request_title, h.created_at, h.request_assigned_to,
        h.request_status, h.request_assigned_name, h.request_take_pending,
        h.request_take_candidate_id, u.user_name AS candidate_name
    FROM HELPDESK h
    LEFT JOIN USERS u
        ON h.request_take_candidate_id = u.user_id
    WHERE h.request_status = %s
    ORDER BY h.created_at DESC
    """, (status,))

    rows = cur.fetchall()
    return render_template("helpdesk_status.html", summary_search=rows, status=status)

@page.post('/helpdesk/update_priority/<int:request_id>')
def update_priority(request_id):
    new_priority = request.form['request_priority']
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("UPDATE HELPDESK SET request_priority = %s WHERE request_id = %s", (new_priority, request_id))
    conn.commit()
    return redirect('/helpdesk')


@page.route("/profile/settings", methods=["GET", "POST"])
def profile_settings_page():
    """
    Renders and processes the Profile Settings page.
    Allows the user to:
    - Update the public visibility of their profile (is_public)
    - Choose which profile blocks (like liked events, comments, etc.) are visible to others
    """

    # Get the current logged-in user
    user = SessionHolder.current_login()
    if not user:
        return redirect(url_for("page.access_denied_page"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        # Handle the form submission

        # 1. Update the 'is_public' flag for the user
        is_public = request.form.get("is_public") == "on"
        cur.execute("UPDATE USERS SET is_public = %s WHERE user_id = %s", (is_public, user.user_id))

        # 2. Update visibility settings for each profile block
        # Get all block IDs from PROFILE_BLOCKS table
        cur.execute("SELECT block_id FROM PROFILE_BLOCKS")
        all_block_ids = [row["block_id"] for row in cur.fetchall()]

        # For each block, check if it is checked in the form and update its visibility
        for block_id in all_block_ids:
            checkbox_name = f"block_{block_id}"
            is_checked = checkbox_name in request.form
            cur.execute("""
                UPDATE PROFILE_VISIBILITY_SETTINGS
                SET is_visible = %s
                WHERE user_id = %s AND block_id = %s
            """, (is_checked, user.user_id, block_id))

        conn.commit()

        # Refresh the session with updated user data
        from app.dao import user_repo
        SessionHolder.session_evict(session, user)
        updated_user = user_repo.find_by_user_id(user.user_id)
        SessionHolder.session_hold(session, updated_user)

        cur.close()
        return redirect(url_for("page.profile_settings_page", success=True))

    # GET request: load block visibility settings
    cur.execute("""
        SELECT b.block_id, b.block_name, b.block_description, v.is_visible
        FROM PROFILE_BLOCKS b
        JOIN PROFILE_VISIBILITY_SETTINGS v ON b.block_id = v.block_id
        WHERE v.user_id = %s
    """, (user.user_id,))
    visibility_blocks = cur.fetchall()
    cur.close()

    # Render the page with user data and block visibility options
    return render_template("profile_settings.html", user=user, visibility_blocks=visibility_blocks)
