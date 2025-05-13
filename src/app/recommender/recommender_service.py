import os
import json
import logging
import redis
from app.proto import service_pb2, service_pb2_grpc
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from datetime import datetime, timedelta
from test_data.sample_items import load_sample_items
import sys

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
                'is_cap': team.is_cap,
                'invitation_status': team.invitation_status
            }
            for team in user_data.teams
        ]
        self.tournaments = [
            {
                'name': t.name,
                'logo': t.logo,
                'team_name': t.team_name,
                'sport': t.sport,
                'city': t.city
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
            if team['is_cap']:
                profile_text += "captain "
            if team['invitation_status']:
                profile_text += f"{team['invitation_status']} "
        
        # Добавляем информацию о турнирах с учетом города
        for tournament in self.tournaments:
            profile_text += f"{tournament['name']} {tournament['sport']} {tournament['city']} "
        
        # Добавляем предпочтения по видам спорта
        for sport, preference in self.sports_preferences.items():
            profile_text += f"{sport} {preference} "
        
        return profile_text

# --- Класс-заглушка для интеграции с Java API ---
# В будущем замените методы на реальные запросы к Java API
class JavaAPIClient:
    def get_user_participation(self, user_id):
        # TODO: реализовать получение истории участия пользователя через Java API
        return []
    def get_user_teams(self, user_id):
        # TODO: реализовать получение команд пользователя через Java API
        return []
    def get_user_search_history(self, user_id):
        # TODO: реализовать получение истории поиска пользователя через Java API
        return []

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
    
    def GetRecommendations(self, request, context):
        user_id = request.user_id
        num_recommendations = request.num_recommendations
        
        # Проверка кэша
        cached_recommendations = self._get_cached_recommendations(user_id)
        if cached_recommendations:
            return self._create_response(cached_recommendations)
        
        # Генерация рекомендаций
        recommendations = self._generate_recommendations(
            user_id,
            num_recommendations,
            request.context
        )
        
        # Кэширование результатов
        self._cache_recommendations(user_id, recommendations)
        
        return self._create_response(recommendations)
    
    def UpdateUserData(self, request, context):
        user_id = request.user_id
        user_data = request.user_data
        try:
            # Проверка на обязательные поля
            if not user_data.name or not user_data.surname:
                logger.warning(f'Пустое имя или фамилия пользователя user_id={user_id}')
            if not user_data.teams:
                logger.info(f'У пользователя {user_id} нет команд')
            if not user_data.tournaments:
                logger.info(f'У пользователя {user_id} нет турниров')
            if not user_data.org_info:
                logger.info(f'У пользователя {user_id} нет информации об организациях')
            # Создаем или обновляем профиль пользователя
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = UserProfile()
            profile = self.user_profiles[user_id]
            profile.update_from_proto(user_data)
            # Инвалидация кэша
            self.redis_client.delete(f'recommendations:{user_id}')
            return service_pb2.UserDataResponse(
                success=True,
                message='User data updated successfully'
            )
        except Exception as e:
            logger.error(f'Error updating user data: {str(e)}')
            return service_pb2.UserDataResponse(
                success=False,
                message=f'Error updating user data: {str(e)}'
            )
    
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
        profile = self.user_profiles[user_id]
        profile_vector = self.vectorizer.fit_transform([profile.get_vector()])
        # Получаем доступные турниры
        available_tournaments = self._get_available_tournaments()
        if not available_tournaments:
            logger.info('Нет доступных турниров для рекомендаций')
            return []
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
    
    def _get_available_tournaments(self):
        # В реальном приложении это будет запрос к Java API
        # Здесь возвращаем тестовые данные для всех видов спорта
        return [
            {
                'id': 't1',
                'name': 'Champions League 2025',
                'sport': 'football',
                'city': 'Москва',
                'description': 'Крупнейший футбольный турнир Европы'
            },
            {
                'id': 't2',
                'name': 'National Cup 2025',
                'sport': 'football',
                'city': 'Санкт-Петербург',
                'description': 'Национальный кубок по футболу'
            },
            {
                'id': 't3',
                'name': 'Basketball Supercup',
                'sport': 'basketball',
                'city': 'Казань',
                'description': 'Суперкубок по баскетболу среди любителей'
            },
            {
                'id': 't4',
                'name': 'Hockey Winter Classic',
                'sport': 'hockey',
                'city': 'Екатеринбург',
                'description': 'Зимний хоккейный турнир'
            },
            {
                'id': 't5',
                'name': 'Volleyball Open',
                'sport': 'volleyball',
                'city': 'Новосибирск',
                'description': 'Открытый турнир по волейболу'
            },
            {
                'id': 't6',
                'name': 'Tennis Masters',
                'sport': 'tennis',
                'city': 'Сочи',
                'description': 'Мастерс по теннису'
            },
            {
                'id': 't7',
                'name': 'Table Tennis Cup',
                'sport': 'table_tennis',
                'city': 'Калуга',
                'description': 'Кубок по настольному теннису'
            },
            {
                'id': 't8',
                'name': 'Badminton Challenge',
                'sport': 'badminton',
                'city': 'Томск',
                'description': 'Челлендж по бадминтону'
            },
            {
                'id': 't9',
                'name': 'Chess Grand Prix',
                'sport': 'chess',
                'city': 'Москва',
                'description': 'Гран-при по шахматам'
            },
            {
                'id': 't10',
                'name': 'Darts League',
                'sport': 'darts',
                'city': 'Тула',
                'description': 'Лига по дартсу'
            },
            {
                'id': 't11',
                'name': 'Pool Masters',
                'sport': 'pool',
                'city': 'Воронеж',
                'description': 'Мастерс по пулу'
            },
            {
                'id': 't12',
                'name': 'Bowling Cup',
                'sport': 'bowling',
                'city': 'Самара',
                'description': 'Кубок по боулингу'
            },
            {
                'id': 't13',
                'name': 'Curling Open',
                'sport': 'curling',
                'city': 'Красноярск',
                'description': 'Открытый турнир по кёрлингу'
            }
        ]
    
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
        return service_pb2.RecommendationResponse(
            recommendations=[
                service_pb2.Recommendation(
                    item_id=rec['item_id'],
                    score=rec['score'],
                    metadata=rec['metadata']
                )
                for rec in recommendations
            ]
        )

    # --- Для будущей интеграции с Java API ---
    def _get_user_profile_from_java(self, user_id):
        participation = self.java_api_client.get_user_participation(user_id)
        teams = self.java_api_client.get_user_teams(user_id)
        search_history = self.java_api_client.get_user_search_history(user_id)
        # Соберите профиль пользователя из этих данных
        # return UserProfile(...)
        return None  # Пока не используется 