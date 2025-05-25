import threading
from app import connection_pool

_transaction_ctx = threading.local()

def get_tx_conn():
    return getattr(_transaction_ctx, 'conn', None)

def get_tx_cursor():
    return getattr(_transaction_ctx, 'cursor', None)

def get_tx_depth():
    return getattr(_transaction_ctx, 'depth', 0)

def transactional(func):
    def wrapper(*args, **kwargs):
        is_outermost = False

        if get_tx_depth() == 0:
            conn = connection_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            _transaction_ctx.conn = conn
            _transaction_ctx.cursor = cursor
            _transaction_ctx.depth = 1
            is_outermost = True
        else:
            _transaction_ctx.depth += 1

        try:
            result = func(*args, **kwargs)
            if is_outermost:
                get_tx_conn().commit()
            return result
        except Exception as e:
            if is_outermost:
                get_tx_conn().rollback()
            raise e
        finally:
            _transaction_ctx.depth -= 1
            if is_outermost:
                get_tx_cursor().close()
                get_tx_conn().close()
                _transaction_ctx.conn = None
                _transaction_ctx.cursor = None
                _transaction_ctx.depth = 0
    return wrapper