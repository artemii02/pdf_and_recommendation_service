import os
from dotenv import load_dotenv
load_dotenv()
import logging
import grpc
from concurrent import futures
from app.proto import service_pb2_grpc
from app.pdf_service.pdf_service import PDFServicer
from app.recommender.recommender_service import RecommenderServicer
from app.config import Config

def serve():
    # Настройка логирования
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT
    )
    logger = logging.getLogger(__name__)
    
    # Создаем gRPC сервер
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Регистрируем сервисы
    service_pb2_grpc.add_PDFServiceServicer_to_server(
        PDFServicer(), server
    )
    service_pb2_grpc.add_RecommenderServiceServicer_to_server(
        RecommenderServicer(), server
    )
    
    # Получаем конфигурацию gRPC сервера
    grpc_config = Config.get_grpc_config()
    server_address = f'{grpc_config["host"]}:{grpc_config["port"]}'
    
    # Запускаем сервер
    server.add_insecure_port(server_address)
    server.start()
    logger.info(f'Server started on {server_address}')
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info('Server stopped by user')
    except Exception as e:
        logger.error(f'Server error: {str(e)}')
        raise

if __name__ == '__main__':
    serve() 