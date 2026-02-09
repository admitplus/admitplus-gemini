import logging
from typing import Optional, List, Dict, Any, Union

from pymilvus import MilvusClient

from admitplus.config import settings


class MilvusManager:
    def __init__(self):
        self.client: Optional[MilvusClient] = None

    def init(self):
        self.client = MilvusClient(
            uri=settings.MILVUS_URI, token=settings.MILVUS_API_KEY, db_name="default"
        )

    def close(self):
        if self.client is None:
            raise Exception("MilvusManager is not initialized")
        self.client.close()
        self.client = None


milvusmanager = MilvusManager()


class MilvusConnection:
    _instance: Optional["MilvusConnection"] = None

    def __init__(self):
        logging.info("[Milvus Service] [Init] Initializing Milvus connection...")
        self.milvus_uri = settings.MILVUS_URI
        self.milvus_api_key = settings.MILVUS_API_KEY
        self.client: Optional[MilvusClient] = None
        self._initialized = False

    @classmethod
    async def get_instance(cls) -> "MilvusConnection":
        if cls._instance is None:
            logging.info(
                "[Milvus Service] [Init] Creating new Milvus connection instance"
            )
            cls._instance = MilvusConnection()

        instance = cls._instance
        if not instance._initialized:
            await instance._connect()
            instance._initialized = True

        logging.info("[Milvus Service] [Init] Returning Milvus connection instance")
        return instance

    async def _connect(self):
        if self.client is not None:
            logging.info(
                "[Milvus Service] [Connection] Milvus client already initialized."
            )
            return

        try:
            if not self.milvus_uri:
                raise ValueError("MILVUS_URI environment variable is not set")
            if not self.milvus_api_key:
                raise ValueError("MILVUS_API_KEY environment variable is not set")

            self.client = MilvusClient(
                uri=self.milvus_uri, token=self.milvus_api_key, db_name="default"
            )
            logging.info(
                "[Milvus Service] [Connection] Successfully connected to Milvus"
            )

        except Exception as e:
            logging.error(
                f"[Milvus Service] [Connection] Milvus connection failed: {e}"
            )
            raise

    async def get_client(self) -> MilvusClient:
        """
        Get Milvus client instance
        """
        if self.client is None:
            logging.error(
                "[Milvus Service] [Client] get_client failed: No Milvus connection."
            )
            raise ConnectionError("[MilvusConnection] Milvus is not connected.")
        return self.client

    def close(self):
        """
        Close Milvus connection
        """
        if self.client is not None:
            self.client.close()
            self.client = None
            self._initialized = False
            logging.info("[Milvus Service] [Connection] Milvus connection closed.")

    @classmethod
    def close_all(cls):
        """
        Close all Milvus connections
        """
        if cls._instance:
            cls._instance.close()
            cls._instance = None
        logging.info("[Milvus Service] [Connection] All Milvus connections closed.")


class BaseMilvusCRUD:
    async def insert(
        self,
        data: List[Dict[str, Any]],
        collection_name: str,
    ) -> Any:
        if not milvusmanager.client:
            raise RuntimeError("Milvus connection is not initialized")

        if not collection_name:
            raise ValueError("collection_name is required")

        try:
            res = milvusmanager.client.insert(
                collection_name=collection_name, data=data
            )
            logging.info(
                f"[MilvusRepository] Inserted data into collection: {collection_name}"
            )
            return res
        except Exception as e:
            logging.error(f"[MilvusRepository] Insert Exception: {e}")
            raise

    async def upsert(
        self,
        data: List[Dict[str, Any]],
        collection_name: str,
        partition_name: Optional[str] = None,
    ) -> Any:
        if not milvusmanager.client:
            raise RuntimeError("Milvus connection is not initialized")

        if not collection_name:
            raise ValueError("collection_name is required")

        try:
            kwargs = {
                "collection_name": collection_name,
                "data": data,
            }
            if partition_name:
                kwargs["partition_name"] = partition_name

            res = milvusmanager.client.upsert(**kwargs)
            logging.info(
                f"[MilvusRepository] Upserted data into collection: {collection_name}"
            )
            return res
        except Exception as e:
            logging.error(f"[MilvusRepository] Upsert Exception: {e}")
            raise

    async def search(
        self,
        query_vectors: List[List[float]],
        collection_name: str,
        filter: Optional[str] = None,
        limit: int = 3,
        **kwargs,
    ) -> Any:
        if not milvusmanager.client:
            raise RuntimeError("Milvus connection is not initialized")

        if not collection_name:
            raise ValueError("collection_name is required")

        try:
            search_kwargs = {
                "collection_name": collection_name,
                "data": query_vectors,
                "limit": limit,
                **kwargs,
            }
            if filter:
                search_kwargs["filter"] = filter

            res = milvusmanager.client.search(**search_kwargs)
            logging.info(f"[MilvusRepository] Searched collection: {collection_name}")
            return res
        except Exception as e:
            logging.error(f"[MilvusRepository] Search Exception: {e}")
            raise

    async def delete(
        self,
        collection_name: str,
        filter: str = None,
        ids: Optional[List[Union[int, str]]] = None,
    ) -> Any:
        if not milvusmanager.client:
            raise RuntimeError("Milvus connection is not initialized")

        if not collection_name:
            raise ValueError("collection_name is required")

        if not filter and not ids:
            raise ValueError(
                "Either 'filter' or 'ids' must be provided for delete operation"
            )

        try:
            delete_kwargs = {"collection_name": collection_name}

            if filter:
                delete_kwargs["filter"] = filter
            if ids:
                delete_kwargs["ids"] = ids

            res = milvusmanager.client.delete(**delete_kwargs)
            logging.info(
                f"[MilvusRepository] Deleted from collection: {collection_name}"
            )
            return res
        except Exception as e:
            logging.error(f"[MilvusRepository] Delete Exception: {e}")
            raise
