from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore
from app import get_connection
from decimal import Decimal

def to_date(value):
    return value.date() if isinstance(value, datetime) else value

def update_or_create_premier_period(cur, user_id, new_start, new_end):
    """
    Updates or creates the user's premium period in PREMIER_USERS table using cumulative logic.
    """
    cur.execute("SELECT premier_id, premier_end_at FROM PREMIER_USERS WHERE user_id = %s", (user_id,))
    existing = cur.fetchone()

    if existing:
        current_end = to_date(existing["premier_end_at"])
        if new_start >= current_end:
            updated_end = new_end
        else:
            updated_end = max(current_end, new_end)

        cur.execute("""
            UPDATE PREMIER_USERS
            SET premier_end_at = %s
            WHERE premier_id = %s
        """, (updated_end, existing["premier_id"]))
    else:
        cur.execute("""
            INSERT INTO PREMIER_USERS (user_id, premier_start_at, premier_end_at)
            VALUES (%s, %s, %s)
        """, (user_id, new_start, new_end))

def create_subscription(user, plan_id, billing_country, card_number=None, is_gifted=False):
    """
    Creates a new subscription for the user, and updates the premium access if applicable.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True, buffered=True)

    # Get plan details
    cur.execute("SELECT plan_duration, plan_price, plan_name FROM PLANS WHERE plan_id = %s", (plan_id,))
    plan = cur.fetchone()
    if not plan:
        cur.close()
        raise ValueError("Plan not found.")

    plan_duration = plan["plan_duration"]
    plan_price = plan["plan_price"]
    plan_name = plan["plan_name"]

    # Prevent multiple free trials
    cur.execute("""
        SELECT plan_id FROM SUBSCRIPTIONS
        WHERE user_id = %s AND plan_id = %s
    """, (user.user_id, plan_id))
    existing_trial = cur.fetchone()

    if plan_name.lower() == "free trial" and existing_trial:
        cur.close()
        raise ValueError("Free trial already used.")

    # Get latest end date from subscriptions
    cur.execute("""
        SELECT MAX(end_date) AS latest_end
        FROM SUBSCRIPTIONS
        WHERE user_id = %s
    """, (user.user_id,))
    row = cur.fetchone()
    latest_end = to_date(row["latest_end"]) if row["latest_end"] else None

    today = datetime.today().date()
    start_date = latest_end if latest_end and latest_end > today else today
    end_date = start_date + relativedelta(months=plan_duration) if plan_duration > 0 else None

    # Insert into SUBSCRIPTIONS
    cur.execute("""
        INSERT INTO SUBSCRIPTIONS (user_id, plan_id, start_date, end_date, is_gifted)
        VALUES (%s, %s, %s, %s, %s)
    """, (user.user_id, plan_id, start_date, end_date, is_gifted))
    subscription_id = cur.lastrowid

    # Insert into PAYMENTS if needed
    if not is_gifted and Decimal(plan_price) > 0:
        last4 = card_number.strip()[-4:] if card_number else None
        is_nz = billing_country.strip().lower() in ["nz", "new zealand"]
        plan_price_dec = Decimal(str(plan_price))
        gst_amount = (plan_price_dec * Decimal("0.15")).quantize(Decimal("0.01")) if is_nz else Decimal("0.00")
        total = (plan_price_dec + gst_amount).quantize(Decimal("0.01"))

        cur.execute("""
            INSERT INTO PAYMENTS (subscription_id, billing_country, card_number_last4, gst_amount, payment_total)
            VALUES (%s, %s, %s, %s, %s)
        """, (subscription_id, billing_country, last4, gst_amount, total))

    # Update PREMIER_USERS table
    update_or_create_premier_period(cur, user.user_id, start_date, end_date)

    conn.commit()
    cur.close()


def get_current_subscription_status(user_id: int) -> str:
    """
    Determines the user's current subscription status.
    Staff roles (admin, editor) always get 'premium'.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True, buffered=True)

    # Get user role
    cur.execute("SELECT user_role FROM USERS WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    if not user:
        cur.close()
        return "free (user not found)"
    
    role = user["user_role"].strip().lower()
    if role in ["admin", "editor"]:
        cur.close()
        return "premium"

    # Check active subscription for normal users
    today = datetime.today().date()
    cur.execute("""
        SELECT PLANS.plan_price
        FROM SUBSCRIPTIONS
        JOIN PLANS ON SUBSCRIPTIONS.plan_id = PLANS.plan_id
        WHERE SUBSCRIPTIONS.user_id = %s
          AND (SUBSCRIPTIONS.start_date IS NULL OR SUBSCRIPTIONS.start_date <= %s)
          AND (SUBSCRIPTIONS.end_date IS NULL OR SUBSCRIPTIONS.end_date >= %s)
        ORDER BY SUBSCRIPTIONS.end_date DESC
        LIMIT 1
    """, (user_id, today, today))

    sub = cur.fetchone()
    cur.close()

    if not sub:
        return "free"
    return "trial premium" if float(sub["plan_price"]) == 0 else "premium"


def is_subscription_expiring_soon(user_id: int) -> bool:
    """
    Checks if the user's cumulative premium access is expiring within 7 days.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True, buffered=True)

    cur.execute("""
        SELECT premier_end_at
        FROM PREMIER_USERS
        WHERE user_id = %s
    """, (user_id,))
    
    row = cur.fetchone()
    cur.close()

    if not row or not row["premier_end_at"]:
        return False

    end_date = to_date(row["premier_end_at"]) 
    today = datetime.today().date()

    return today <= end_date <= today + timedelta(days=7)

def days_until_subscription_ends(user_id: int):
    """
    Returns the number of days until the user's cumulative premium access ends.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True, buffered=True)

    cur.execute("""
        SELECT premier_end_at
        FROM PREMIER_USERS
        WHERE user_id = %s
    """, (user_id,))
    
    row = cur.fetchone()
    cur.close()

    if not row or not row["premier_end_at"]:
        return None

    end_date = to_date(row["premier_end_at"])
    today = datetime.today().date()
    days_remaining = (end_date - today).days

    return days_remaining if days_remaining >= 0 else None