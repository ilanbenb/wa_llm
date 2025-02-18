from typing import List
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


async def upsert(session: AsyncSession, entity: SQLModel):
    # Split fields into primary keys and values
    pkeys, vals = {}, {}
    for f in entity.__table__.columns:
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

    return await session.exec(stmt)


async def bulk_upsert(session: AsyncSession, entities: List[SQLModel]):
    if not entities:
        return None

    # Get the first entity to determine the model class and structure
    entity_class = entities[0].__class__

    # Extract all values for bulk insert
    values_list = []
    # Get structure from first entity
    first_entity = entities[0]
    pkeys = {f.name for f in first_entity.__table__.columns if f.primary_key}

    for entity in entities:
        row_data = {}
        for f in entity.__table__.columns:
            row_data[f.name] = getattr(entity, f.name)
        values_list.append(row_data)

    # Create bulk insert statement
    stmt = insert(entity_class).values(values_list)

    # Create on_conflict_do_update statement
    stmt = stmt.on_conflict_do_update(
        index_elements=list(pkeys),
        set_={
            col.name: stmt.excluded[col.name]
            for col in entity_class.__table__.columns
            if not col.primary_key
        },
    )

    return await session.exec(stmt)
