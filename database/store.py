import datetime
import logging
from pymongo.errors import DuplicateKeyError
from settings import DB_URL, DB_NAME, RATE_LIMIT_TIMEOUT, MAX_FILES

logger = logging.getLogger(__name__)

_client = None
_db = None


def _get_db():
    global _client, _db
    if _db is not None:
        return _db

    import motor.motor_asyncio
    _client = motor.motor_asyncio.AsyncIOMotorClient(
        DB_URL,
        maxPoolSize=100,
        minPoolSize=10,
        retryWrites=True,
        serverSelectionTimeoutMS=30000,
    )
    _db = _client[DB_NAME]
    logger.info("Connected to MongoDB database '%s'.", DB_NAME)
    return _db


class UserStore:
    def __init__(self):
        pass

    @property
    def _database(self):
        return _get_db()

    @property
    def users(self):
        return self._database.users

    @property
    def blocked_users(self):
        return self._database.blocked_users

    @property
    def blocked_channels(self):
        return self._database.blocked_channels

    @property
    def files(self):
        return self._database.files

    @property
    def rate_windows(self):
        return self._database.rate_windows

    @property
    def file_meta_cache(self):
        return self._database.file_meta_cache

    async def ensure_indexes(self):
        try:
            await self.users.create_index("id", unique=True)
            await self.blocked_users.create_index("user_id", unique=True)
            await self.blocked_channels.create_index("channel_id", unique=True)
            await self.files.create_index("user_id")
            await self.files.create_index("file_id", unique=True)
            await self.files.create_index(
                "timestamp",
                expireAfterSeconds=2592000,
                partialFilterExpression={"timestamp": {"$exists": True}}
            )
            await self.rate_windows.create_index(
                [("user_id", 1), ("window", 1)], unique=True
            )
            await self.rate_windows.create_index(
                "window",
                expireAfterSeconds=RATE_LIMIT_TIMEOUT + 60
            )
            await self.file_meta_cache.create_index("msg_id", unique=True)
            await self.file_meta_cache.create_index(
                "ts",
                expireAfterSeconds=86400
            )
            logger.info("UserStore indexes ensured.")
        except Exception as e:
            logger.warning("Index creation skipped (non-fatal): %s", e)

    def new_user(self, id, name):
        return {
            "id": int(id),
            "name": name,
            }

    async def add_user(self, id, name):
        if not await self.is_user_exist(id):
            user = self.new_user(id, name)
            await self.users.insert_one(user)

    async def is_user_exist(self, id):
        return bool(await self.users.find_one({'id': int(id)}))

    async def total_users_count(self):
        return await self.users.count_documents({})

    async def get_all_users(self):
        return self.users.find({})

    async def delete_user(self, user_id):
        await self.users.delete_many({'id': int(user_id)})

    async def rate_limit_ok(self, user_id: int) -> tuple[bool, int]:
        import time
        now = time.time()
        window_start = now - (now % RATE_LIMIT_TIMEOUT)
        key = {"user_id": int(user_id), "window": window_start}

        try:
            result = await self.rate_windows.find_one_and_update(
                {**key, "count": {"$lt": MAX_FILES}},
                {"$inc": {"count": 1}},
                upsert=True,
                return_document=True,
            )
        except DuplicateKeyError:
            result = None

        if result is None:
            ttl = max(0, int(RATE_LIMIT_TIMEOUT - (now - window_start)))
            return False, ttl
        return True, 0

    async def get_cached_file_meta(self, msg_id: int):
        return await self.file_meta_cache.find_one({"msg_id": int(msg_id)})

    async def set_cached_file_meta(self, msg_id: int, meta: dict):
        meta["msg_id"] = int(msg_id)
        meta["ts"] = datetime.datetime.utcnow()
        await self.file_meta_cache.update_one(
            {"msg_id": int(msg_id)},
            {"$set": meta},
            upsert=True,
        )

    async def is_user_blocked(self, user_id: int) -> bool:
        return await self.blocked_users.find_one({"user_id": int(user_id)}) is not None

    async def block_user(self, user_id: int, reason: str = "No reason provided."):
        await self.blocked_users.update_one(
            {"user_id": int(user_id)},
            {
                "$set": {
                    "user_id": int(user_id),
                    "reason": reason,
                    "blocked_at": datetime.datetime.utcnow()
                }
            },
            upsert=True
        )

    async def unblock_user(self, user_id: int):
        await self.blocked_users.delete_one({"user_id": int(user_id)})
        
    async def get_all_blocked_users(self):
        return self.blocked_users.find({})

    async def total_blocked_count(self):
        return await self.blocked_users.count_documents({})
        
    async def is_channel_blocked(self, channel_id: int) -> bool:
        return await self.blocked_channels.find_one({"channel_id": int(channel_id)}) is not None

    async def block_channel(self, channel_id: int, reason: str = "No reason provided."):
        await self.blocked_channels.update_one(
            {"channel_id": int(channel_id)},
            {
                "$set": {
                    "channel_id": int(channel_id),
                    "reason": reason,
                    "blocked_at": datetime.datetime.utcnow()
                }
            },
            upsert=True
        )

    async def unblock_channel(self, channel_id: int):
        await self.blocked_channels.delete_one({"channel_id": int(channel_id)})

    async def get_all_blocked_channels(self):
        return self.blocked_channels.find({})

    async def total_blocked_channels_count(self):
        return await self.blocked_channels.count_documents({})

store = UserStore()
            
