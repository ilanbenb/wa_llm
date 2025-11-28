from typing import List, TypeVar, cast
from sqlalchemy import inspect

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import SQLModel, select
from sqlmodel.sql.expression import SelectOfScalar
from sqlmodel.ext.asyncio.session import AsyncSession


T = TypeVar("T", bound=SQLModel)


async def upsert(session: AsyncSession, entity: T) -> T:
    # Split fields into primary keys and values
    pkeys, vals = {}, {}
    mapper = inspect(entity.__class__)
    for f in mapper.columns:
        (pkeys if f.primary_key else vals)[f.name] = getattr(entity, f.name)

    # Create insert statement
    stmt = insert(entity.__class__).values(**{**pkeys, **vals})

    # Create on_conflict_do_update statement
    stmt = stmt.on_conflict_do_update(
        index_elements=list(pkeys.keys()),  # Convert keys to list
        set_={
            k: stmt.excluded[k]  # Use excluded to reference values from INSERT
            for k in vals.keys()  # Only update non-primary key columns
        },
    )

    await session.execute(stmt)

    # Query for the updated instance
    select_stmt = select(entity.__class__).where(
        *[getattr(entity.__class__, k) == v for k, v in pkeys.items()]
    )
    db_instance = await session.exec(select_stmt)
    result = db_instance.first()

    # Merge the instance into the session
    if result is None:
        # Should not happen after upsert, but for type safety
        return entity
    return result


async def bulk_upsert(session: AsyncSession, entities: List[SQLModel]):
    if not entities:
        return None

    # Get the first entity to determine the model class and structure
    entity_class = entities[0].__class__

    # Extract all values for bulk insert
    values_list = []
    # Get structure from first entity
    first_entity = entities[0]
    mapper = inspect(first_entity.__class__)
    pkeys = {f.name for f in mapper.columns if f.primary_key}

    for entity in entities:
        row_data = {}
        for f in mapper.columns:
            row_data[f.name] = getattr(entity, f.name)
        values_list.append(row_data)

    # Create bulk insert statement
    stmt = insert(entity_class).values(values_list)

    # Create on_conflict_do_update statement
    stmt = stmt.on_conflict_do_update(
        index_elements=list(pkeys),
        set_={
            col.name: stmt.excluded[col.name]
            for col in mapper.columns
            if not col.primary_key
        },
    )

    return await session.exec(cast(SelectOfScalar[SQLModel], stmt))
