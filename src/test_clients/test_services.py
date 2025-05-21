import grpc
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import service_pb2
import service_pb2_grpc
from datetime import datetime, timedelta
from src.test_data.full_sample import get_test_match, get_test_tournaments, get_test_teams

def test_recommender_service():
    # Подключение к сервису рекомендаций
    channel = grpc.insecure_channel('localhost:50051')
    recommender_stub = service_pb2_grpc.RecommenderServiceStub(channel)
    
    # Тестовые данные пользователя
    user_data = {
        'name': 'Иван',
        'surname': 'Петров',
        'org_info': [
            {
                'name': 'СпортКлуб',
                'role': 'Игрок',
                'is_ref': False
            }
        ],
        'teams': [
            {
                'name': 'Спартак',
                'logo': b'spartak.png',
                'sport': 'football',
                'invitation_status': 'accepted'
            }
        ],
        'tournaments': [
            {
                'name': 'Кубок Москвы 2024',
                'logo': b'cup.png',
                'organization_name': 'СпортКлуб',
                'sport': 'football',
                'city': 'Москва',
                'description': 'Ежегодный турнир'
            }
        ]
    }
    
    try:
        # Обновление данных пользователя
        update_request = service_pb2.UserDataRequest(
            user_id='test_user_1',
            user_data=service_pb2.UserData(**user_data)
        )
        
        update_response = recommender_stub.UpdateUserData(update_request)
        print(f'Обновление данных пользователя: {"успешно" if update_response.user_data else "ошибка"}')
        
        # Получение рекомендаций
        rec_request = service_pb2.RecommendationRequest(
            user_id='test_user_1',
            num_recommendations=5,
            context={'page': 'home'}
        )
        
        rec_response = recommender_stub.GetRecommendations(rec_request)
        print('\nПолученные рекомендации:')
        for i, rec in enumerate(rec_response.recommendations, 1):
            print(f'\n{i}. Событие {rec.item_id} (релевантность: {rec.score:.2f})')
            print('Метаданные:')
            for key, value in rec.metadata.items():
                print(f'   {key}: {value}')
        
    except grpc.RpcError as e:
        print(f'Ошибка при работе с сервисом рекомендаций: {str(e)}')

def test_pdf_service():
    channel = grpc.insecure_channel('localhost:50051')
    pdf_stub = service_pb2_grpc.PDFServiceStub(channel)

    # Тест: генерация PDF для матча по всем видам спорта
    print('=== Тестирование PDF для матчей по всем видам спорта ===')
    sports = [
        'football', 'basketball', 'hockey', 'volleyball',
        'tennis', 'table_tennis', 'badminton', 'chess',
        'darts', 'pool', 'bowling', 'curling'
    ]
    for sport in sports:
        match_data = get_test_match().copy()
        match_data['sport'] = sport
        match_data['teams'][0]['sport'] = sport
        match_data['teams'][1]['sport'] = sport
        # Симуляция отсутствия голов и пенальти для некоторых видов спорта
        if sport in ['chess', 'darts', 'pool', 'bowling', 'curling']:
            match_data['goals'] = []
            match_data['after_match_penalties'] = []
        request = service_pb2.MatchPDFRequest(
            match_id=match_data['match_id'],
            stage_id=match_data['stage_id'],
            tournament_id=match_data['tournament_id'],
            sport=match_data['sport'],
            teams=[service_pb2.TeamInfo(
                team_id=t['team_id'], name=t['name'], logo=t['logo'], sport=t['sport']
            ) for t in match_data['teams']],
            score=service_pb2.ScoreInfo(
                team_1=match_data['score']['team_1'],
                team_2=match_data['score']['team_2']
            ),
            goals=[service_pb2.GoalInfo(
                team_id=g['team_id'], user_name=g['user_name'], user_surname=g['user_surname'],
                set_number=g['set_number'], time=g['time'], is_penalty=g['is_penalty']
            ) for g in match_data['goals']],
            after_match_penalties=[service_pb2.AfterMatchPenaltyInfo(
                team_id=p['team_id'], user_name=p['user_name'], user_surname=p['user_surname'],
                is_success=p['is_success']
            ) for p in match_data['after_match_penalties']],
            location=service_pb2.LocationInfo(
                name=match_data['location']['name'],
                address=match_data['location']['address'],
                city=match_data['location']['city']
            ),
            date=match_data['date'],
            is_finished=match_data['is_finished']
        )
        response = pdf_stub.CreateMatchPDF(request)
        print(f'PDF для матча по {sport}: task_id={response.task_id}, status={response.status}')

    # Тест: генерация PDF для турнира по всем видам спорта
    print('\n=== Тестирование PDF для турниров по всем видам спорта ===')
    tournaments = get_test_tournaments()
    for t in tournaments:
        request = service_pb2.TournamentPDFRequest(
            tournament_id=t['tournament_id'],
            name=t['name'],
            sport=t['sport'],
            organization_name=t['organization_name'],
            logo=t['logo'],
            description=t['description'],
            city=t['city'],
            registration_deadline=t['registration_deadline'],
            is_stopped=t['is_stopped'],
            stages=[],
            teams=[],
            slots=[],
            groups=[]
        )
        response = pdf_stub.CreateTournamentPDF(request)
        print(f'PDF для турнира по {t["sport"]}: task_id={response.task_id}, status={response.status}')

if __name__ == '__main__':
    print('Тестирование сервиса рекомендаций:')
    test_recommender_service()
    
    print('\nТестирование PDF сервиса:')
    test_pdf_service() 