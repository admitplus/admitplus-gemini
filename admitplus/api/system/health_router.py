import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

from admitplus.database.mongo import MongoConnector
from admitplus.database.mysql import MySQLConnector
from admitplus.database.redis import RedisConnector
from admitplus.config import settings

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


async def check_mongodb() -> Dict[str, Any]:
    """
    Check MongoDB connection health
    """
    try:
        # Use one of the configured database names for health check
        db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME or "admin"
        mongo_client = await MongoConnector.get_instance(db_name)

        # Ensure client is initialized
        if mongo_client.client is None:
            return {"status": "error", "message": "MongoDB client not initialized"}

        # Ping the database
        await mongo_client.client.admin.command("ping")

        return {"status": "ok", "message": "MongoDB is healthy"}
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        return {"status": "error", "message": str(e)}


async def check_mysql() -> Dict[str, Any]:
    """
    Check MySQL connection health
    """
    try:
        mysql_connector = MySQLConnector.get_instance()

        # Run synchronous MySQL operations in thread pool
        loop = asyncio.get_event_loop()
        conn = await loop.run_in_executor(None, mysql_connector.get_connection)

        if conn and conn.is_connected():

            def _execute_query():
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                mysql_connector.close_connection(conn)
                return result

            await loop.run_in_executor(None, _execute_query)
            return {"status": "ok", "message": "MySQL is healthy"}
        else:
            return {"status": "error", "message": "MySQL connection failed"}
    except Exception as e:
        logger.error(f"MySQL health check failed: {e}")
        return {"status": "error", "message": str(e)}


async def check_redis() -> Dict[str, Any]:
    """
    Check Redis connection health
    """
    try:
        redis_connector = await RedisConnector.get_instance()
        is_healthy = await redis_connector.ping()

        if is_healthy:
            return {"status": "ok", "message": "Redis is healthy"}
        else:
            return {"status": "error", "message": "Redis ping failed"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "error", "message": str(e)}


async def check_database_with_timeout(
    check_func, timeout: float = 2.0
) -> Dict[str, Any]:
    """
    Run database check with timeout
    """
    try:
        return await asyncio.wait_for(check_func(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Database check timed out after {timeout}s")
        return {"status": "error", "message": f"Check timed out after {timeout}s"}
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def health():
    """
    Basic health check endpoint
    """
    return {
        "status": "ok",
        "service": "admitplus-api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
    }


@router.get("/readiness")
async def readiness():
    """
    Readiness check endpoint - verifies all dependencies are available
    """
    # Run all checks concurrently with timeout
    mongo_result, mysql_result, redis_result = await asyncio.gather(
        check_database_with_timeout(check_mongodb),
        check_database_with_timeout(check_mysql),
        check_database_with_timeout(check_redis),
        return_exceptions=True,
    )

    # Handle exceptions from gather
    if isinstance(mongo_result, Exception):
        mongo_result = {"status": "error", "message": str(mongo_result)}
    if isinstance(mysql_result, Exception):
        mysql_result = {"status": "error", "message": str(mysql_result)}
    if isinstance(redis_result, Exception):
        redis_result = {"status": "error", "message": str(redis_result)}

    # Determine overall readiness
    all_healthy = all(
        result.get("status") == "ok"
        for result in [mongo_result, mysql_result, redis_result]
    )

    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "mongodb": mongo_result,
            "mysql": mysql_result,
            "redis": redis_result,
        },
    }


@router.get("/liveness")
async def liveness():
    """
    Liveness check endpoint - indicates if the service is alive
    """
    return {
        "status": "alive",
        "service": "admitplus-api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
