import os
import grpc
import time
from concurrent import futures
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import service_pb2
import service_pb2_grpc
from app.pdf_service.pdf_service import PDFServicer
from app.recommender.recommender_service import RecommenderServicer

def serve():
    # Создаем gRPC сервер
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Регистрируем сервисы
    service_pb2_grpc.add_PDFServiceServicer_to_server(
        PDFServicer(), server
    )
    service_pb2_grpc.add_RecommenderServiceServicer_to_server(
        RecommenderServicer(), server
    )
    
    # Создаем директорию для временных файлов
    os.makedirs('temp', exist_ok=True)
    
    # Запускаем сервер
    server.add_insecure_port('[::]:50051')
    server.start()
    
    print('Сервисы запущены:')
    print('PDF сервис: localhost:50051')
    print('Рекомендательный сервис: localhost:50051')
    
    try:
        while True:
            time.sleep(86400)  # 24 часа
    except KeyboardInterrupt:
        server.stop(0)
        print('\nСервисы остановлены')

if __name__ == '__main__':
    serve() 