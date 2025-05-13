import os
from typing import Dict, Any

class Config:
    # Redis configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    REDIS_TTL = int(os.getenv('REDIS_TTL', 3600))
    
    # Java API configuration
    JAVA_API_URL = os.getenv('JAVA_API_URL', 'http://localhost:8080')
    
    # gRPC server configuration
    GRPC_HOST = os.getenv('GRPC_HOST', '[::]')
    GRPC_PORT = int(os.getenv('GRPC_PORT', 50051))
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        return {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB,
            'password': cls.REDIS_PASSWORD
        }
    
    @classmethod
    def get_grpc_config(cls) -> Dict[str, Any]:
        return {
            'host': cls.GRPC_HOST,
            'port': cls.GRPC_PORT
        } 