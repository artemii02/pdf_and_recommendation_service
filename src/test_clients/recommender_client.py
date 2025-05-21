import grpc
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import service_pb2
import service_pb2_grpc

def test_recommender_service():
    channel = grpc.insecure_channel('localhost:50051')
    stub = service_pb2_grpc.RecommenderServiceStub(channel)

    # Тестовые пользователи для всех видов спорта и с разными вариантами заполнения
    test_users = [
        {
            'user_id': 'user_football',
            'user_data': {
                'name': 'Иван',
                'surname': 'Петров',
                'org_info': [
                    {'name': 'Футбольный клуб', 'role': 'Игрок', 'is_ref': False}
                ],
                'teams': [
                    {'name': 'Спартак', 'logo': 'spartak.png', 'sport': 'football', 'is_cap': True, 'invitation_status': 'accepted'}
                ],
                'tournaments': [
                    {'name': 'Кубок Москвы', 'logo': 'cup.png', 'team_name': 'Спартак', 'sport': 'football', 'city': 'Москва'}
                ]
            }
        },
        {
            'user_id': 'user_basketball',
            'user_data': {
                'name': 'Петр',
                'surname': 'Сидоров',
                'org_info': [],
                'teams': [
                    {'name': 'Зенит', 'logo': 'zenit.png', 'sport': 'basketball', 'is_cap': False, 'invitation_status': ''}
                ],
                'tournaments': [
                    {'name': 'Чемпионат СПб', 'logo': 'bball.png', 'team_name': 'Зенит', 'sport': 'basketball', 'city': 'Санкт-Петербург'}
                ]
            }
        },
        {
            'user_id': 'user_empty',
            'user_data': {
                'name': '',
                'surname': '',
                'org_info': [],
                'teams': [],
                'tournaments': []
            }
        },
        {
            'user_id': 'user_all_sports',
            'user_data': {
                'name': 'Алексей',
                'surname': 'Миронов',
                'org_info': [
                    {'name': 'Клуб любителей спорта', 'role': 'Организатор', 'is_ref': True}
                ],
                'teams': [
                    {'name': 'Теннисисты', 'logo': '', 'sport': 'tennis', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Настольный теннис', 'logo': '', 'sport': 'table_tennis', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Бадминтон', 'logo': '', 'sport': 'badminton', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Шахматисты', 'logo': '', 'sport': 'chess', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Дартс', 'logo': '', 'sport': 'darts', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Пул', 'logo': '', 'sport': 'pool', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Боулинг', 'logo': '', 'sport': 'bowling', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Кёрлинг', 'logo': '', 'sport': 'curling', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Волейбол', 'logo': '', 'sport': 'volleyball', 'is_cap': False, 'invitation_status': ''},
                    {'name': 'Хоккей', 'logo': '', 'sport': 'hockey', 'is_cap': False, 'invitation_status': ''}
                ],
                'tournaments': [
                    {'name': 'Турнир по теннису', 'logo': '', 'team_name': 'Теннисисты', 'sport': 'tennis', 'city': 'Казань'},
                    {'name': 'Турнир по настольному теннису', 'logo': '', 'team_name': 'Настольный теннис', 'sport': 'table_tennis', 'city': 'Казань'},
                    {'name': 'Турнир по бадминтону', 'logo': '', 'team_name': 'Бадминтон', 'sport': 'badminton', 'city': 'Казань'},
                    {'name': 'Турнир по шахматам', 'logo': '', 'team_name': 'Шахматисты', 'sport': 'chess', 'city': 'Казань'},
                    {'name': 'Турнир по дартсу', 'logo': '', 'team_name': 'Дартс', 'sport': 'darts', 'city': 'Казань'},
                    {'name': 'Турнир по пулу', 'logo': '', 'team_name': 'Пул', 'sport': 'pool', 'city': 'Казань'},
                    {'name': 'Турнир по боулингу', 'logo': '', 'team_name': 'Боулинг', 'sport': 'bowling', 'city': 'Казань'},
                    {'name': 'Турнир по кёрлингу', 'logo': '', 'team_name': 'Кёрлинг', 'sport': 'curling', 'city': 'Казань'},
                    {'name': 'Турнир по волейболу', 'logo': '', 'team_name': 'Волейбол', 'sport': 'volleyball', 'city': 'Казань'},
                    {'name': 'Турнир по хоккею', 'logo': '', 'team_name': 'Хоккей', 'sport': 'hockey', 'city': 'Казань'}
                ]
            }
        }
    ]

    for user in test_users:
        print(f"\n=== Тест пользователя: {user['user_id']} ===")
        # Обновление данных пользователя
        update_request = service_pb2.UserDataRequest(
            user_id=user['user_id'],
            user_data=service_pb2.UserData(
                name=user['user_data']['name'],
                surname=user['user_data']['surname'],
                org_info=[service_pb2.OrgInfo(**org) for org in user['user_data']['org_info']],
                teams=[service_pb2.Team(
                    name=team['name'], logo=team['logo'], sport=team['sport'],
                    is_cap=team['is_cap'], invitation_status=team['invitation_status']
                ) for team in user['user_data']['teams']],
                tournaments=[service_pb2.Tournament(
                    name=t['name'], logo=t['logo'], team_name=t['team_name'], sport=t['sport'], city=t['city']
                ) for t in user['user_data']['tournaments']]
            )
        )
        update_response = stub.UpdateUserData(update_request)
        print(f'Обновление данных: {"успешно" if update_response.user_data else "ошибка"}')

        # Получение рекомендаций
        rec_request = service_pb2.RecommendationRequest(
            user_id=user['user_id'],
            num_recommendations=5
        )
        rec_response = stub.GetRecommendations(rec_request)
        print('Рекомендации:')
        if not rec_response.recommendations:
            print('  Нет рекомендаций (проверьте логи сервиса)')
        for i, rec in enumerate(rec_response.recommendations, 1):
            print(f'  {i}. Событие {rec.item_id} (релевантность: {rec.score:.2f})')
            for key, value in rec.metadata.items():
                print(f'     {key}: {value}')

if __name__ == '__main__':
    test_recommender_service() 