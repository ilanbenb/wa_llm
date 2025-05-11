from typing import Dict, List, Type, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import inspect, Select
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


class AsyncQueryMock:
    def __init__(self, storage):
        self._storage = storage
        self._filter_conditions = []
        self._model = None
        self._offset_val = None
        self._limit_val = None
        self._order_by = []

    def filter(self, *conditions):
        self._filter_conditions.extend(conditions)
        return self

    def offset(self, offset):
        self._offset_val = offset
        return self

    def limit(self, limit):
        self._limit_val = limit
        return self

    def order_by(self, *criteria):
        self._order_by.extend(criteria)
        return self

    def _apply_filters(self, results: List[Any]) -> List[Any]:
        filtered_results = results
        for condition in self._filter_conditions:
            filtered_results = [
                item
                for item in filtered_results
                if self._evaluate_condition(item, condition)
            ]
        return filtered_results

    def _evaluate_condition(self, item: Any, condition: Any) -> bool:
        # Basic condition evaluation - can be extended based on needs
        try:
            return condition.__clause_element__().compare(
                getattr(item, condition.left.key), condition.right.value
            )
        except Exception:
            return True  # Default to True if we can't evaluate

    def all(self):
        if not self._model:
            return []

        results = [
            item for item in self._storage.values() if isinstance(item, self._model)
        ]

        results = self._apply_filters(results)

        if self._offset_val:
            results = results[self._offset_val :]
        if self._limit_val:
            results = results[: self._limit_val]

        return results

    def first(self):
        results = self.all()
        return results[0] if results else None


class AsyncCompoundQueryMock:
    def __init__(self, storage):
        self._storage = storage
        self._model = None
        self._results = []

    async def all(self):
        return self._results

    async def first(self):
        results = await self.all()
        return results[0] if results else None


class AsyncSessionMock(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._storage: Dict[tuple, Any] = {}

        # Set up async methods
        self.get = AsyncMock(side_effect=self._get)
        self.add = AsyncMock(side_effect=self._add)
        self.flush = AsyncMock(side_effect=self._flush)
        self.commit = AsyncMock(side_effect=self._commit)
        self.execute = AsyncMock(side_effect=self._execute)
        self.exec = AsyncMock(side_effect=self._exec)

    async def _get(self, model_class: Type[SQLModel], key: Any):
        model_key = (model_class.__name__, key)
        return self._storage.get(model_key)

    async def _add(self, instance: SQLModel):
        if not isinstance(instance, SQLModel):
            raise TypeError("Instance must be a SQLModel")

        mapper = inspect(instance.__class__)
        pk = tuple(getattr(instance, key.name) for key in mapper.primary_key)
        model_key = (instance.__class__.__name__, pk)
        self._storage[model_key] = instance

    async def _flush(self):
        pass

    async def _commit(self):
        pass

    async def _execute(self, statement):
        # Handle different statement types (insert, update, delete)
        if hasattr(statement, "is_insert") and statement.is_insert:
            return MagicMock()
        return MagicMock()

    async def _exec(self, statement):
        # Convert the statement into a result
        if isinstance(statement, Select):  # Changed from select to Select
            query = AsyncQueryMock(self._storage)
            try:
                query._model = statement._raw_columns[0].entity_namespace
            except (AttributeError, IndexError):
                # Fallback for when we can't get the model from raw columns
                pass
            return query
        return AsyncCompoundQueryMock(self._storage)

    def begin_nested(self):
        return NestedTransaction(self)


class NestedTransaction:
    def __init__(self, session):
        self.session = session
        self._storage_snapshot = None

    async def __aenter__(self):
        self._storage_snapshot = self.session._storage.copy()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session._storage = self._storage_snapshot


@pytest.fixture
def mock_session():
    return AsyncSessionMock(spec=AsyncSession)
