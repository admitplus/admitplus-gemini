import logging
from typing import Optional, Dict, Any, List

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from admitplus.config import settings


class MongoPoolManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None

    def init(self, mongo_dsn: str):
        self.client = AsyncIOMotorClient(mongo_dsn, maxPoolSize=10, minPoolSize=5)

    def close(self):
        if self.client is None:
            raise Exception("MongoPoolManager is not initialized")
        self.client.close()
        self.client = None


mongomanager = MongoPoolManager()


class MongoConnector:
    _instances = {}

    def __init__(self, db_name: str):
        logging.info("[Mongo Service] [Init] Initializing MongoDB connection...")
        self.uri = settings.MONGO_URI
        self.db_name = db_name
        self.client = None
        self.db = None
        self._initialized = False

    @classmethod
    async def get_instance(cls, db_name: str) -> "MongoConnector":
        if db_name not in cls._instances:
            logging.info(
                f"[Mongo Service] [Init] Creating new instance for database: {db_name}"
            )
            cls._instances[db_name] = MongoConnector(db_name)

        instance = cls._instances[db_name]
        if not instance._initialized:
            await instance._connect()
            instance._initialized = True

        logging.info(
            f"[Mongo Service] [Init] Returning instance for database: {db_name}"
        )
        return instance

    async def _connect(self):
        if self.client is not None:
            logging.info(
                "[Mongo Service] [Connection] MongoDB client already initialized."
            )
            return
        try:
            if not self.uri:
                raise ValueError("MONGO_URI environment variable is not set")

            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client.get_database(self.db_name)
            logging.info(
                f"[Mongo Service] [Connection] Successfully connected to MongoDB database: {self.db_name}"
            )

        except Exception as e:
            logging.error(
                f"[Mongo Service] [Connection] MongoDB connection failed: {e}"
            )
            raise

    async def get_collection(
        self, collection_name: str, check_exists: bool = False
    ) -> AsyncIOMotorCollection:
        if self.db is None:
            logging.error(
                "[Mongo Service] [Collection] get_collection failed: No database connection."
            )
            raise ConnectionError("[MongoConnector] MongoDB is not connected.")

        if check_exists:
            logging.debug(
                f"[Mongo Service] [Collection] Checking if collection '{collection_name}' exists..."
            )
            collection_names = await self.db.list_collection_names()
            if collection_name not in collection_names:
                logging.error(
                    f"[Mongo Service] [Collection] Collection '{collection_name}' not found."
                )
                raise ValueError(
                    f"[MongoConnector] Collection '{collection_name}' does not exist."
                )

        logging.info(
            f"[Mongo Service] [Collection] Retrieved collection '{collection_name}' from database '{self.db_name}'."
        )
        return self.db[collection_name]

    def close(self):
        if self.client is not None:
            self.client.close()
            logging.info(
                f"[Mongo Service] [Connection] MongoDB connection closed for database: {self.db_name}"
            )

    @classmethod
    def close_all(cls):
        """Close all database connections"""
        for db_name, instance in cls._instances.items():
            instance.close()
        cls._instances.clear()
        logging.info("[Mongo Service] [Connection] All MongoDB connections closed.")


class BaseMongoCRUD:
    def __init__(
        self,
        db_name: str,
        collection_name: Optional[str] = None,
        check_collection_exists: bool = False,
    ):
        self.db_name = db_name
        self.collection_name = collection_name
        self.check_collection_exists = check_collection_exists
        self.collection: Optional[AsyncIOMotorCollection] = None
        self._initialized = False

        if collection_name:
            logging.info(
                f"[MongoRepository] Initialized with db: {db_name}, collection: {collection_name}"
            )
        else:
            logging.info(
                f"[MongoRepository] Initialized with db: {db_name} (no collection specified)"
            )

    async def _ensure_initialized(self, collection_name: Optional[str] = None) -> None:
        target_collection = collection_name or self.collection_name

        if not target_collection:
            raise ValueError(
                "No collection name specified. Use set_collection() or pass collection_name to method."
            )

        if (
            self._initialized
            and self.collection is not None
            and self.collection_name == target_collection
        ):
            return

        if mongomanager.client is None:
            raise Exception("MongoPoolManager is not initialized")
            # self.mongo_client = await MongoConnector.get_instance(self.db_name)

        if self.check_collection_exists:
            existing_collections = await mongomanager.client[
                self.db_name
            ].list_collection_names()
            if target_collection not in existing_collections:
                raise ValueError(
                    f"[MongoConnector] Collection '{target_collection}' does not exist."
                )

        self.collection = mongomanager.client[self.db_name][target_collection]
        self.collection_name = target_collection
        self._initialized = True
        logging.info(f"[MongoRepository] Initialized collection: {target_collection}")

    def set_collection(self, collection_name: str) -> None:
        self.collection_name = collection_name
        self._initialized = False  # Force reinitialization with new collection
        logging.info(f"[MongoRepository] Collection set to: {collection_name}")

    async def find_one(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        await self._ensure_initialized(collection_name)
        logging.info(f"[MongoRepository] collection name {collection_name}")
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")

        try:
            # Default to exclude _id if projection is None or doesn't explicitly include _id
            # Only exclude _id if it's not explicitly set to 1 (included)
            if projection is None:
                projection = {"_id": 0}
            elif "_id" not in projection or projection.get("_id") != 1:
                projection = {**projection, "_id": 0}
            return await self.collection.find_one(query, projection)
        except Exception as e:
            logging.error(f"[MongoRepository] Exception: {e}")
            raise

    async def find_many(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")

        try:
            # Default to exclude _id if projection is None or doesn't explicitly include _id
            # Only exclude _id if it's not explicitly set to 1 (included)
            if projection is None:
                projection = {"_id": 0}
            elif "_id" not in projection or projection.get("_id") != 1:
                projection = {**projection, "_id": 0}
            cursor = self.collection.find(query, projection)
            if sort:
                cursor = cursor.sort(sort)
            return await cursor.to_list(length=None)
        except Exception as e:
            logging.error(f"[MongoRepository] Exception: {e}")
            raise

    async def find_many_paginated(
        self,
        query: Dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
        include_count: bool = True,
    ) -> tuple[List[Dict[str, Any]], int]:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")

        try:
            # Default to exclude _id if projection is None or doesn't explicitly include _id
            # Only exclude _id if it's not explicitly set to 1 (included)
            if projection is None:
                projection = {"_id": 0}
            elif "_id" not in projection or projection.get("_id") != 1:
                projection = {**projection, "_id": 0}
            skip = (page - 1) * page_size
            total_count = 0
            if include_count:
                total_count = await self.collection.count_documents(query)
            cursor = self.collection.find(query, projection)
            if sort:
                cursor = cursor.sort(sort)
            cursor = cursor.skip(skip).limit(page_size)
            documents = await cursor.to_list(length=None)
            return documents, total_count
        except Exception as e:
            logging.error(f"[MongoRepository] Pagination exception: {e}")
            raise

    async def insert_one(
        self, document: Dict[str, Any], collection_name: Optional[str] = None
    ) -> str:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")

        try:
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"[MongoRepository] Insert Exception: {e}")
            raise

    async def insert_many(
        self, documents: List[Dict[str, Any]], collection_name: Optional[str] = None
    ) -> List[str]:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")
        try:
            result = await self.collection.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logging.error(f"[MongoRepository] Insert Many Exception: {e}")
            raise

    async def update_one(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        collection_name: Optional[str] = None,
    ) -> int:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")
        try:
            result = await self.collection.update_one(query, update)
            logging.info(
                f"[MongoRepository] Updated {result.modified_count} document(s) with query: {query}"
            )
            return result.modified_count
        except Exception as e:
            logging.error(f"[MongoRepository] Update Exception: {e}")
            raise

    async def update_many(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        collection_name: Optional[str] = None,
    ) -> int:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")
        try:
            result = await self.collection.update_many(query, update)
            logging.info(
                f"[MongoRepository] Updated {result.modified_count} document(s) with query: {query}"
            )
            return result.modified_count
        except Exception as e:
            logging.error(f"[MongoRepository] Update Many Exception: {e}")
            raise

    async def upsert_one(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        collection_name: Optional[str] = None,
    ) -> Optional[str]:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")
        try:
            result = await self.collection.update_one(
                query, {"$set": update}, upsert=True
            )
            logging.info(f"[MongoRepository] Upserted document with query: {query}")
            return str(result.upserted_id) if result.upserted_id else None
        except Exception as e:
            logging.error(f"[MongoRepository] Upsert Exception: {e}")
            raise

    async def replace_one(
        self,
        query: Dict[str, Any],
        replacement: Dict[str, Any],
        collection_name: Optional[str] = None,
    ) -> Optional[str]:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")
        try:
            result = await self.collection.replace_one(query, replacement)
            logging.info(
                f"[MongoRepository] Replaced {result.modified_count} document(s) with query: {query}"
            )
            return str(result.upserted_id) if result.upserted_id else None
        except Exception as e:
            logging.error(f"[MongoRepository] Replace One Exception: {e}")
            raise

    async def delete_one(
        self, query: Dict[str, Any], collection_name: Optional[str] = None
    ) -> int:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")
        try:
            result = await self.collection.delete_one(query)
            logging.info(
                f"[MongoRepository] Deleted {result.deleted_count} document(s) with query: {query}"
            )
            return result.deleted_count
        except Exception as e:
            logging.error(f"[MongoRepository] Delete Exception: {e}")
            raise

    async def delete_many(
        self, query: Dict[str, Any], collection_name: Optional[str] = None
    ) -> int:
        await self._ensure_initialized(collection_name)
        if self.collection is None:
            raise RuntimeError("Collection is not initialized")
        try:
            result = await self.collection.delete_many(query)
            logging.info(
                f"[MongoRepository] Deleted {result.deleted_count} document(s) with query: {query}"
            )
            return result.deleted_count
        except Exception as e:
            logging.error(f"[MongoRepository] Delete Many Exception: {e}")
            raise
