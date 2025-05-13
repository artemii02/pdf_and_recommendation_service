# Универсальные тестовые данные для всех сервисов

def get_all_sports():
    return [
        'football', 'basketball', 'hockey', 'volleyball',
        'tennis', 'table_tennis', 'badminton', 'chess',
        'darts', 'pool', 'bowling', 'curling'
    ]

def get_test_teams():
    sports = get_all_sports()
    return [
        {
            'team_id': f'team_{i+1}',
            'name': f'Команда {i+1} ({sport})',
            'logo': f'logo_{i+1}.png',
            'sport': sport
        }
        for i, sport in enumerate(sports)
    ]

def get_test_tournaments():
    sports = get_all_sports()
    return [
        {
            'tournament_id': f'tour_{i+1}',
            'name': f'Турнир по {sport}',
            'sport': sport,
            'organization_name': f'Оргкомитет {i+1}',
            'logo': f'logo_tour_{i+1}.png',
            'description': f'Описание турнира по {sport}. Лучшие команды города сразятся за кубок!',
            'city': 'Москва',
            'registration_deadline': '2024-12-31T23:59:59Z',
            'is_stopped': False,
            'stages': [
                {
                    'stage_id': 'stage_1',
                    'name': 'Групповой этап',
                    'is_published': True,
                    'best_place': 1,
                    'worst_place': 4,
                    'matches': [get_test_match()]
                },
                {
                    'stage_id': 'stage_2',
                    'name': 'Плей-офф',
                    'is_published': False,
                    'best_place': 1,
                    'worst_place': 2,
                    'matches': []
                }
            ],
            'teams': get_test_teams(),
            'slots': [],
            'groups': [
                {
                    'group_id': 'group_1',
                    'name': 'Группа A',
                    'index': 'A',
                    'count_teams': 2,
                    'teams': get_test_teams()[:2]
                },
                {
                    'group_id': 'group_2',
                    'name': 'Группа B',
                    'index': 'B',
                    'count_teams': 2,
                    'teams': get_test_teams()[2:4]
                }
            ]
        }
        for i, sport in enumerate(sports)
    ]

def get_test_match():
    return {
        'match_id': 'match_1',
        'stage_id': 'stage_1',
        'tournament_id': 'tour_1',
        'sport': 'football',
        'teams': [
            {'team_id': 'team_1', 'name': 'Команда 1', 'logo': '', 'sport': 'football'},
            {'team_id': 'team_2', 'name': 'Команда 2', 'logo': '', 'sport': 'football'}
        ],
        'score': {'team_1': 3, 'team_2': 2},
        'goals': [
            {'team_id': 'team_1', 'user_id': 'user_1', 'ser_number': 1, 'time': '12:00', 'is_penalty': False},
            {'team_id': 'team_2', 'user_id': 'user_2', 'ser_number': 2, 'time': '34:00', 'is_penalty': False},
            {'team_id': 'team_1', 'user_id': 'user_3', 'ser_number': 3, 'time': '45:00', 'is_penalty': False},
            {'team_id': 'team_2', 'user_id': 'user_4', 'ser_number': 4, 'time': '60:00', 'is_penalty': True},
            {'team_id': 'team_1', 'user_id': 'user_5', 'ser_number': 5, 'time': '78:00', 'is_penalty': False}
        ],
        'after_match_penalties': [
            {'user_id': 'user_1', 'team_id': 'team_1', 'is_success': True},
            {'user_id': 'user_2', 'team_id': 'team_2', 'is_success': False},
            {'user_id': 'user_3', 'team_id': 'team_1', 'is_success': True},
            {'user_id': 'user_4', 'team_id': 'team_2', 'is_success': True}
        ],
        'location': {'name': 'Стадион Центральный', 'address': 'ул. Спортивная, 1', 'city': 'Москва'},
        'date': '2024-06-01T15:00:00Z',
        'is_finished': True
    }

def get_test_user():
    return {
        'name': 'Тестовый',
        'surname': 'Пользователь',
        'org_info': [
            {'name': 'Оргкомитет 1', 'role': 'Организатор', 'is_ref': True},
            {'name': 'Федерация футбола', 'role': 'Судья', 'is_ref': True},
            {'name': 'Клуб любителей спорта', 'role': 'Участник', 'is_ref': False}
        ],
        'teams': [
            {'team_id': 'team_1', 'name': 'Команда 1 (football)', 'logo': 'logo_1.png', 'sport': 'football'},
            {'team_id': 'team_2', 'name': 'Команда 2 (basketball)', 'logo': 'logo_2.png', 'sport': 'basketball'},
            {'team_id': 'team_3', 'name': 'Команда 3 (hockey)', 'logo': 'logo_3.png', 'sport': 'hockey'},
            {'team_id': 'team_4', 'name': 'Команда 4 (volleyball)', 'logo': 'logo_4.png', 'sport': 'volleyball'}
        ],
        'tournaments': [
            {'name': 'Турнир по футболу', 'logo': '', 'team_name': 'Команда 1', 'sport': 'football', 'city': 'Москва'},
            {'name': 'Турнир по баскетболу', 'logo': '', 'team_name': 'Команда 2', 'sport': 'basketball', 'city': 'Санкт-Петербург'},
            {'name': 'Турнир по хоккею', 'logo': '', 'team_name': 'Команда 3', 'sport': 'hockey', 'city': 'Казань'},
            {'name': 'Турнир по волейболу', 'logo': '', 'team_name': 'Команда 4', 'sport': 'volleyball', 'city': 'Екатеринбург'}
        ]
    } 