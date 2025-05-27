import os
import json
import logging
import redis
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) )
import service_pb2
import service_pb2_grpc
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from datetime import datetime, timedelta
from test_data.sample_items import load_sample_items
import grpc

logger = logging.getLogger(__name__)

class UserProfile:
    def __init__(self):
        self.name = ""
        self.surname = ""
        self.org_info = []
        self.teams = []
        self.tournaments = []
        self.last_update = datetime.now()
        self.sports_preferences = {}  # Словарь предпочтений по видам спорта
    
    def update_from_proto(self, user_data):
        self.name = user_data.name
        self.surname = user_data.surname
        self.org_info = [
            {
                'name': org.name,
                'role': org.role,
                'is_ref': org.is_ref
            }
            for org in user_data.org_info
        ]
        self.teams = [
            {
                'name': team.name,
                'logo': team.logo,
                'sport': team.sport,
                'invitation_status': team.invitation_status
            }
            for team in user_data.teams
        ]
        self.tournaments = [
            {
                'name': t.name,
                'logo': t.logo,
                'organization_name': t.organization_name,
                'sport': t.sport,
                'city': t.city,
                'description': t.description
            }
            for t in user_data.tournaments
        ]
        
        # Обновляем предпочтения по видам спорта
        self._update_sports_preferences()
        self.last_update = datetime.now()
    
    def _update_sports_preferences(self):
        # Считаем количество участий в каждом виде спорта
        sports_count = {}
        for team in self.teams:
            sport = team['sport']
            sports_count[sport] = sports_count.get(sport, 0) + 1
        
        for tournament in self.tournaments:
            sport = tournament['sport']
            sports_count[sport] = sports_count.get(sport, 0) + 1
        
        # Нормализуем предпочтения
        total = sum(sports_count.values())
        if total > 0:
            self.sports_preferences = {
                sport: count / total
                for sport, count in sports_count.items()
            }
    
    def get_vector(self):
        # Создаем текстовое представление профиля для векторизации
        profile_text = f"{self.name} {self.surname} "
        
        # Добавляем информацию об организациях
        for org in self.org_info:
            profile_text += f"{org['name']} {org['role']} "
            if org['is_ref']:
                profile_text += "referee "
        
        # Добавляем информацию о командах с учетом роли
        for team in self.teams:
            profile_text += f"{team['name']} {team['sport']} "
            if team['invitation_status']:
                profile_text += f"{team['invitation_status']} "
        
        # Добавляем информацию о турнирах с учетом города
        for tournament in self.tournaments:
            profile_text += f"{tournament['name']} {tournament['sport']} {tournament['city']} "
        
        # Добавляем предпочтения по видам спорта
        for sport, preference in self.sports_preferences.items():
            profile_text += f"{sport} {preference} "
        
        return profile_text

# --- Функция для сериализации numpy.ndarray и других объектов ---
def to_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(x) for x in obj]
    return obj

class RecommenderServicer(service_pb2_grpc.RecommenderServiceServicer):
    def __init__(self):
        redis_password = os.getenv('REDIS_PASSWORD', None)
        if redis_password is None:
            logger.error('REDIS_PASSWORD не установлен!')
            raise ValueError('REDIS_PASSWORD не установлен')
            
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            password=redis_password
        )
        self.cache_ttl = int(os.getenv('REDIS_TTL', 3600))
        
        # Инициализация векторайзера с улучшенными параметрами
        self.vectorizer = TfidfVectorizer(
            max_features=2000,  # Увеличиваем количество признаков
            stop_words='english',
            ngram_range=(1, 2),  # Добавляем биграммы
            min_df=1,  # Исправлено: теперь работает даже с одним документом
            max_df=1.0  # Исправлено: допускает все слова
        )
        
        # Профили пользователей
        self.user_profiles = {}
        
        # Список поддерживаемых видов спорта
        self.supported_sports = [
            'football', 'basketball', 'hockey', 'volleyball',
            'tennis', 'table_tennis', 'badminton', 'chess',
            'darts', 'pool', 'bowling', 'curling'
        ]

        # Настройка gRPC клиента для Java-сервиса
        java_service_host = 'app'
        java_service_port = '9090'
        java_service_address = f"{java_service_host}:{java_service_port}"
        logger.info(f"Подключение к Java-сервису по адресу: {java_service_address}")
        
        # Создание канала для связи с Java-сервисом
        self.java_channel = grpc.insecure_channel(java_service_address)
        # Создание клиента для RecommenderService
        self.java_recommender_client = service_pb2_grpc.RecommenderServiceStub(self.java_channel)
        
        logger.info("RecommenderServicer инициализирован успешно")
    
    def GetRecommendations(self, request, context):
        user_id = request.user_id
        num_recommendations = request.num_recommendations
        logger.info(f"Получен запрос на рекомендации для пользователя {user_id}, количество: {num_recommendations}")
        
        try:
            # Проверяем наличие профиля в кэше
            cached_profile = self.redis_client.get(f'user_profile:{user_id}')
            if not cached_profile:
                logger.info(f"Профиль пользователя {user_id} не найден в кэше, запрашиваем данные из Java API")
                # Запрашиваем данные пользователя через Java API
                user_data_request = service_pb2.UserDataRequest(user_id=user_id)
                try:
                    user_data_response = self.java_recommender_client.UpdateUserData(user_data_request)
                    
                    if not user_data_response or not user_data_response.user_data:
                        logger.error(f"Не удалось получить данные пользователя {user_id} из Java API")
                        return service_pb2.RecommendationResponse(recommendations=[])
                    
                    # Создаем новый профиль пользователя
                    user_profile = UserProfile()
                    user_profile.update_from_proto(user_data_response.user_data)
                    self.user_profiles[user_id] = user_profile
                    
                    # Кэшируем профиль
                    self.redis_client.setex(
                        f'user_profile:{user_id}',
                        self.cache_ttl,
                        json.dumps({
                            'profile': user_profile.get_vector(),
                            'last_update': user_profile.last_update.isoformat()
                        })
                    )
                    
                except grpc.RpcError as e:
                    logger.error(f"Ошибка при получении данных пользователя {user_id}: {str(e)}")
                    return service_pb2.RecommendationResponse(recommendations=[])
            
            # Проверка кэша рекомендаций
            cached_recommendations = self._get_cached_recommendations(user_id)
            if cached_recommendations:
                logger.info(f"Найдены кэшированные рекомендации для пользователя {user_id}")
                return self._create_response(cached_recommendations)
            
            # Генерация рекомендаций
            logger.info(f"Генерация новых рекомендаций для пользователя {user_id}")
            recommendations = self._generate_recommendations(
                user_id,
                num_recommendations,
                request.context
            )
            
            # Кэширование результатов
            if recommendations:
                logger.info(f"Сгенерировано {len(recommendations)} рекомендаций для пользователя {user_id}")
                self._cache_recommendations(user_id, recommendations)
            else:
                logger.warning(f"Не удалось сгенерировать рекомендации для пользователя {user_id}")
            
            response = self._create_response(recommendations)
            logger.info(f"Отправка ответа с {len(response.recommendations)} рекомендациями")
            return response
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса на рекомендации: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Внутренняя ошибка сервера: {str(e)}")
            return service_pb2.RecommendationResponse(recommendations=[])
    
    def UpdateUserData(self, request, context):
        """
        Проксирует запрос на обновление данных пользователя в Java-сервис
        """
        logger.info(f"Получен запрос на обновление данных пользователя {request.user_id}")
        try:
            # Перенаправляем запрос в Java-сервис
            response = self.java_recommender_client.UpdateUserData(request)
            logger.info(f"Данные пользователя {request.user_id} успешно обновлены в Java-сервисе")
            return response
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных пользователя в Java-сервисе: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Ошибка при обновлении данных пользователя: {str(e)}")
            return service_pb2.UserDataResponse(user_id=request.user_id, user_data=None)
    
    def GetAvailableTournaments(self, request, context):
        """
        Проксирует запрос на получение доступных турниров в Java-сервис
        """
        logger.info("Получен запрос на получение доступных турниров")
        try:
            # Перенаправляем запрос в Java-сервис
            response = self.java_recommender_client.GetAvailableTournaments(request)
            logger.info(f"Получено {len(response.tournaments)} турниров от Java-сервиса")
            return response
        except Exception as e:
            logger.error(f"Ошибка при получении турниров из Java-сервиса: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Ошибка при получении турниров: {str(e)}")
            return service_pb2.TournamentsResponse(tournaments=[])
    
    def _get_cached_recommendations(self, user_id):
        cached_data = self.redis_client.get(f'recommendations:{user_id}')
        if cached_data:
            return json.loads(cached_data)
        return None
    
    def _cache_recommendations(self, user_id, recommendations):
        self.redis_client.setex(
            f'recommendations:{user_id}',
            self.cache_ttl,
            json.dumps(recommendations)
        )
    
    def _generate_recommendations(self, user_id, num_recommendations, context):
        if user_id not in self.user_profiles:
            logger.warning(f'Нет профиля пользователя для user_id={user_id}')
            return []

        # Получаем доступные турниры через Java API
        try:
            response = self.java_recommender_client.GetAvailableTournaments(service_pb2.Empty())
            available_tournaments = [
                {
                    'id': t.name,  # Используйте t.id, если есть, иначе t.name
                    'name': t.name,
                    'sport': t.sport,
                    'city': t.city,
                    'description': t.description
                }
                for t in response.tournaments
            ]
        except Exception as e:
            logger.error(f'Ошибка при получении турниров из Java API: {str(e)}')
            available_tournaments = []

        if not available_tournaments:
            logger.info('Нет доступных турниров для рекомендаций')
            return []

        try:
            profile = self.user_profiles[user_id]
            profile_vector = self.vectorizer.fit_transform([profile.get_vector()])

            # Фильтруем турниры по контексту
            if context and 'sport' in context:
                sport = context['sport']
                if sport in self.supported_sports:
                    available_tournaments = [
                        t for t in available_tournaments
                        if t.get('sport') == sport
                    ]
                else:
                    logger.info(f'Контекстный фильтр по спорту: {sport} не поддерживается')

            # Векторизация турниров
            tournament_vectors = self.vectorizer.transform([
                self._tournament_to_text(t) for t in available_tournaments
            ])

            # Расчет схожести
            similarities = cosine_similarity(profile_vector, tournament_vectors)[0]

            # Сортируем турниры по схожести
            tournament_scores = list(zip(available_tournaments, similarities))
            tournament_scores.sort(key=lambda x: x[1], reverse=True)

            # Возвращаем топ-N рекомендаций
            if not tournament_scores:
                logger.info(f'Нет подходящих турниров для пользователя {user_id}')
                return []

            return [
                {
                    'item_id': t[0]['id'],
                    'score': float(t[1]),
                    'metadata': {
                        'name': t[0]['name'],
                        'sport': t[0]['sport'],
                        'city': t[0].get('city', ''),
                        'description': t[0].get('description', '')
                    }
                }
                for t in tournament_scores[:num_recommendations]
            ]
        except Exception as e:
            logger.error(f'Ошибка при генерации рекомендаций: {str(e)}')
            return []
    
    def _tournament_to_text(self, tournament):
        # Улучшенное текстовое представление турнира
        text = f"{tournament['name']} {tournament['sport']} "
        if 'city' in tournament:
            text += f"{tournament['city']} "
        if 'description' in tournament:
            text += f"{tournament['description']} "
        if 'organization_name' in tournament:
            text += f"{tournament['organization_name']} "
        return text
    
    def _create_response(self, recommendations):
        print("I'm in response")
        return service_pb2.RecommendationResponse(
            recommendations=[
                service_pb2.Recommendation(
                    item_id=rec['item_id'],
                    score=rec['score'],
                    metadata={
                        k: str(v) for k, v in rec['metadata'].items()
                    }
                )
                for rec in recommendations
            ]
        )

    def _update_user_profile(self, user_id, user_data):
        """Обновляет профиль пользователя и сохраняет его в кэш"""
        try:
            # Создаем новый профиль
            profile = UserProfile()
            profile.update_from_proto(user_data)
            
            # Сохраняем профиль в памяти
            self.user_profiles[user_id] = profile
            
            # Кэшируем профиль в Redis
            profile_data = {
                'name': profile.name,
                'surname': profile.surname,
                'org_info': profile.org_info,
                'teams': profile.teams,
                'tournaments': profile.tournaments,
                'sports_preferences': profile.sports_preferences,
                'last_update': profile.last_update.isoformat()
            }
            
            self.redis_client.setex(
                f'user_profile:{user_id}',
                self.cache_ttl,
                json.dumps(profile_data)
            )
            
            logger.info(f"Профиль пользователя {user_id} успешно обновлен и закэширован")
        except Exception as e:
            logger.error(f"Ошибка при обновлении профиля пользователя {user_id}: {str(e)}")
            raise