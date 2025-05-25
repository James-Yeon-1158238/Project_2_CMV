from contextlib import contextmanager
import dataclasses
from datetime import date
import datetime
from doctest import Example
import re
from typing import Any, Callable, Dict, Generic, Optional, Tuple, TypeVar, Type, List, Union
from dataclasses import Field, dataclass, asdict, field, fields
from mysql.connector import pooling, cursor

from app.dao.fluent_query import FluentQuery
from app.dao.query_example import QueryExample
from app.dao.transaction import get_tx_conn, get_tx_cursor


E = TypeVar("E")
T = TypeVar('T')
    

class BaseRepository(Generic[E]):

    def __init__(self, table_name: str, entity_class: Type[E], connection_pool: pooling.MySQLConnectionPool):
        self.conn_pool: pooling.MySQLConnectionPool = connection_pool
        self.table_name: str = table_name
        self.entity_class: Type[E] = entity_class

    @contextmanager
    def _connection(self):
        cur: cursor.MySQLCursor = get_tx_cursor()
        conn: pooling.PooledMySQLConnection = get_tx_conn()
        
        if cur and conn:
            yield cur
        else:
            conn = self.conn_pool.get_connection()
            cur = conn.cursor(dictionary = True)
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cur.close()
                conn.close()
    
    def get_entity_class(self) -> Type[E]:
        return self.entity_class
    
    
    def get_primary_key_field(self) -> str:
        for field in fields(self.get_entity_class()):
            if getattr(field, "metadata", {}).get("primary_key", False):
                return field.name
        return "id"
    
    
    def __getattr__(self, name):
        if name.startswith("findBy"):
            return self._generate_query(name[6:], "select_list")
        elif name.startswith("findOneBy"):
            return self._generate_query(name[9:], "select_one")
        elif name.startswith("countBy"):
            return self._generate_query(name[7:], "count")
        elif name.startswith("deleteBy"):
            return self._generate_query(name[8:], "delete")
        elif name.startswith("updateBy"):
            return self._generate_update(name[8:]) 
        raise AttributeError(f"Method {name} not found")
    
    
    def _generate_update(self, fields_str):
        where_fields, _, _, _ = self._parse_query(fields_str)

        def method(*args, **kwargs):
            set_fields = {k: v for k, v in kwargs.items() if k not in [f[0] for f in where_fields]}
            if not set_fields:
                raise ValueError("No fields to update")

            set_clause = ", ".join([f"{k} = %s" for k in set_fields])
            set_values = list(set_fields.values())

            where_clause_parts = []
            where_values = []
            value_index = 0

            for i, (field, op, connector) in enumerate(where_fields):
                value = args[value_index]

                if op == "IN":
                    if not isinstance(value, list):
                        raise ValueError(f"IN 操作必须提供 list，但收到: {type(value).__name__}")
                    placeholders = ", ".join(["%s"] * len(value))
                    clause = f"{field} IN ({placeholders})"
                    where_values.extend(value)
                else:
                    clause = f"{field} {op} %s"
                    where_values.append(value)

                if where_clause_parts:
                    clause = f" {connector} {clause}"
                where_clause_parts.append(clause)

                value_index += 1

            where_clause = "WHERE " + "".join(where_clause_parts)
            query = f"UPDATE {self.table_name} SET {set_clause} {where_clause}"
            print(query)

            with self._connection() as cur:
                cur.execute(query, set_values + where_values)
                return cur.rowcount

        return method

    
    def _generate_query(self, fields_str, op_type):
        fields, order_by, limit, offset = self._parse_query(fields_str)

        def method(*values):
            with self._connection() as cur:
                base = f"SELECT * FROM {self.table_name}" if op_type in ("select_one", "select_list") else \
                       f"DELETE FROM {self.table_name}" if op_type == "delete" else \
                       f"SELECT COUNT(*) as cnt FROM {self.table_name}"

                where_clauses = []
                flat_values = []
                value_index = 0

                for idx, (field, op, connector) in enumerate(fields):
                    value = values[value_index]

                    if op == "IN":
                        placeholders = ','.join(['%s'] * len(value))
                        clause = f"{field} IN ({placeholders})"
                        flat_values.extend(value)
                    else:
                        clause = f"{field} {op} %s"
                        flat_values.append(value)

                    if where_clauses:
                        clause = f" {connector} {clause}"
                    where_clauses.append(clause)

                    value_index += 1

                where = f" WHERE {''.join(where_clauses)}" if where_clauses else ""

                order_clause = ""
                if order_by:
                    order_parts = [f"{field} {direction}" for field, direction in order_by]
                    order_clause = " ORDER BY " + ", ".join(order_parts)

                limit_clause = " LIMIT 1" if op_type == "select_one" else f" LIMIT {limit}" if limit else ""
                offset_clause = f" OFFSET {offset}" if offset else ""

                query = base + where + order_clause + limit_clause + offset_clause
                print(query)
                cur.execute(query, flat_values)
                if op_type == "select_list":
                    results = cur.fetchall()
                    return [self._deserialize_entity(row) for row in results]
                elif op_type == "select_one":
                    result = cur.fetchone()
                    return self._deserialize_entity(result) if result else None
                elif op_type == "count":
                    return cur.fetchone()["cnt"]
                elif op_type == "delete":
                    return cur.rowcount

        return method


    def _parse_query(self, fields_str):
        order_by_idx = fields_str.find('OrderBy')
        limit_idx = fields_str.find('Limit')
        offset_idx = fields_str.find('Offset')

        end_idx = min(
            [i for i in [order_by_idx, limit_idx, offset_idx] if i != -1] or [len(fields_str)]
        )
        where_part = fields_str[:end_idx]

        raw_parts = re.split(r'(And|Or)', where_part)
        fields = []
        i = 0
        while i < len(raw_parts):
            part = raw_parts[i]
            connector = 'AND'
            if part in ('And', 'Or'):
                connector = 'OR' if part == 'Or' else 'AND'
                i += 1
                part = raw_parts[i] if i < len(raw_parts) else ''
            
            # 提取操作符
            match = re.match(r'^(.+?)(In|Like)?$', part)
            if match:
                field_raw, op_suffix = match.groups()
                field = self._camel_to_snake(field_raw)
                op = "IN" if op_suffix == "In" else ("LIKE" if op_suffix == "Like" else "=")
                fields.append((field, op, connector))
            i += 1

        # 解析 order_by
        order_by = []
        if order_by_idx != -1:
            ob_start = order_by_idx + len('OrderBy')
            ob_end = min([i for i in [limit_idx, offset_idx] if i != -1] or [len(fields_str)])
            ob_part = fields_str[ob_start:ob_end]
            ob_fields = ob_part.split('And')
            for ob_field in ob_fields:
                match = re.match(r'(.+)(Asc|Desc)$', ob_field)
                if match:
                    field, direction = match.group(1), match.group(2).upper()
                    order_by.append((self._camel_to_snake(field), direction))
                else:
                    order_by.append((self._camel_to_snake(ob_field), "ASC"))

        # 解析 limit
        limit = None
        if limit_idx != -1:
            limit_val = re.findall(r'\d+', fields_str[limit_idx + len('Limit'):])
            if limit_val:
                limit = int(limit_val[0])

        # 解析 offset
        offset = None
        if offset_idx != -1:
            offset_val = re.findall(r'\d+', fields_str[offset_idx + len('Offset'):])
            if offset_val:
                offset = int(offset_val[0])

        return fields, order_by, limit, offset
    
    def find_all_by_example(self, example: QueryExample, projection: Optional[Callable[[E], T]] = None) -> List[E]:
        where_clause, params = self._build_where(example.conditions)
        with self._connection() as cur:
            select_clause = ", ".join(example.fields) if example.fields else "*"
            query_sql = f"SELECT {select_clause} FROM {self.table_name} WHERE {where_clause}"

            if example.order_by:
                query_sql += f" ORDER BY {example.order_by}"
            if example.limit:
                query_sql += f" LIMIT {example.limit}"
            if example.offset:
                query_sql += f" OFFSET {example.offset}"

            cur.execute(query_sql, params)
            rows = cur.fetchall()
            entities = [self._deserialize_entity(row) for row in rows]
            return list(map(projection, entities)) if projection else entities

    
    def find_by(self, example: Example, query_fn: Callable[[FluentQuery], Any]):
        fq: FluentQuery = FluentQuery(example)
        return query_fn(fq).execute(self)

    
    def find_one_by_example(self, example: QueryExample) -> Optional[E]:
        where_clause, params = self._build_where(example.conditions)
        with self._connection() as cur:
            select_clause = ", ".join(example.fields) if example.fields else "*"
            query_sql = f"SELECT {select_clause} FROM {self.table_name} WHERE {where_clause} LIMIT 1"

            if example.order_by:
                query_sql += f" ORDER BY {example.order_by}"

            cur.execute(query_sql, params)
            result = cur.fetchone()
            return self._deserialize_entity(result) if result else None


    def _deserialize_entity(self, data: Dict[str, Any]) -> E:
        entity_init_data = {}
        for field in fields(self.entity_class):
            if field.name in data:
                entity_init_data[field.name] = data[field.name]
            elif field.default != dataclasses.MISSING or field.default_factory != dataclasses.MISSING:
                pass
            else:
                entity_init_data[field.name] = None
        return self.get_entity_class()(**entity_init_data)
    
    
    def _build_where(self, conditions: Dict[str, Any]) -> Tuple[str, List[Any]]:
        sql_parts = []
        params = []
        op_map = {
            "eq": "=",
            "gt": ">",
            "lt": "<",
            "gte": ">=",
            "lte": "<=",
            "like": "LIKE",
            "in": "IN"
        }

        and_clauses = []
        or_clauses = []

        for key, value in conditions.items():
            logic = "AND"
            if "__or__" in key:
                logic = "OR"
                key = key.replace("__or__", "")

            if "__" in key:
                field, op = key.split("__")
                op_sql = op_map.get(op, "=")
            else:
                field, op_sql = key, "="

            field_snake = self._camel_to_snake(field)

            if op_sql == "IN" and isinstance(value, list):
                placeholders = ", ".join(["%s"] * len(value))
                clause = f"{field_snake} {op_sql} ({placeholders})"
                params.extend(value)
            else:
                clause = f"{field_snake} {op_sql} %s"
                params.append(value)

            if logic == "OR":
                or_clauses.append(clause)
            else:
                and_clauses.append(clause)

        final_clause_parts = []
        if and_clauses:
            final_clause_parts.append(" AND ".join(and_clauses))
        if or_clauses:
            final_clause_parts.append("(" + " OR ".join(or_clauses) + ")")

        where_clause = " AND ".join(final_clause_parts) if final_clause_parts else "1=1"
        return where_clause, params
    
    def _execute_page_query(self, example: QueryExample, projection: Optional[Callable[[E], Any]] = None) -> 'PageResult':
        where_clause, params = self._build_where(example.conditions)
        with self._connection() as cur:
            count_sql = f"SELECT COUNT(*) as cnt FROM {self.table_name} WHERE {where_clause}"
            cur.execute(count_sql, params)
            total = cur.fetchone()["cnt"]

            select_clause = ", ".join(example.fields) if example.fields else "*"
            query_sql = f"SELECT {select_clause} FROM {self.table_name} WHERE {where_clause}"

            if example.order_by:
                query_sql += f" ORDER BY {example.order_by}"

            offset = (example.page - 1) * example.size
            query_sql += f" LIMIT %s OFFSET %s"
            cur.execute(query_sql, params + [example.size, offset])
            rows = cur.fetchall()

            entities = [self._deserialize_entity(row) for row in rows]
            data = list(map(projection, entities)) if projection else entities

            from app.dao.page_result import PageResult
            return PageResult(data = data, total = total, page = example.page, size = example.size)
        

    def _format_value(self, value):
        if isinstance(value, (date, datetime.datetime)):
            return value.strftime('%Y-%m-%d %H:%M:%S') if isinstance(value, datetime.datetime) else value.strftime('%Y-%m-%d')
        return value

    def _is_auto_field(self, f: Field) -> bool:
        return f.metadata.get("auto_now", False) or f.metadata.get("auto_now_add", False)

    def save_or_update(self, entity: E):
        data = asdict(entity)
        primary_key_field = self.get_primary_key_field()
        primary_key_value = data.get(primary_key_field)

        if primary_key_value is None:
            return self.save(entity)
        else:
            return self.update(entity)

    def save(self, entity: E):
        entity_fields = fields(entity)
        data = asdict(entity)
        final_data = {}
        for f in entity_fields:
            if self._is_auto_field(f) and data[f.name] is None:
                continue 
            value = data[f.name]
            final_data[f.name] = self._format_value(value)
        columns = ", ".join(final_data.keys())
        placeholders = ", ".join(["%s"] * len(final_data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        with self._connection() as cur:
            cur.execute(query, list(final_data.values()))
            return cur.lastrowid

    def update(self, entity: E):
        entity_fields = fields(entity)
        data = asdict(entity)
        primary_key_field = self.get_primary_key_field()
        primary_key_value = data.pop(primary_key_field)
        final_data = {}
        for f in entity_fields:
            if f.name == primary_key_field:
                continue
            if f.metadata.get("auto_now", False):
                continue
            value = data[f.name]
            final_data[f.name] = self._format_value(value)

        set_clause = ", ".join([f"{k} = %s" for k in final_data])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {primary_key_field} = %s"
        with self._connection() as cur:
            cur.execute(query, list(final_data.values()) + [self._format_value(primary_key_value)])
            return cur.rowcount

    
    def _camel_to_snake(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()