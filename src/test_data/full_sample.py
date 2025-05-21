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
            'sport': sport,
            'invitation_status': 'accepted'
        }
        for i, sport in enumerate(sports)
    ]

def get_test_tournaments():
    sports = get_all_sports()
    return [
        {
            'tournament_id': 'tournament_1',
            'name': 'Кубок Москвы 2024',
            'sport': 'football',
            'organization_name': 'СпортКлуб',
            'logo': b'cup.png',
            'description': 'Ежегодный турнир по футболу',
            'city': 'Москва',
            'registration_deadline': '2024-03-01T00:00:00Z',
            'is_stopped': False
        },
        {
            'tournament_id': 'tournament_2',
            'name': 'Чемпионат России 2024',
            'sport': 'basketball',
            'organization_name': 'Баскетбол РФ',
            'logo': b'basketball.png',
            'description': 'Чемпионат России по баскетболу',
            'city': 'Москва',
            'registration_deadline': '2024-02-15T00:00:00Z',
            'is_stopped': False
        }
    ]

def get_test_match():
    return {
        'match_id': 'match_1',
        'stage_id': 'stage_1',
        'tournament_id': 'tournament_1',
        'sport': 'football',
        'teams': [
            {
                'team_id': 'team_1',
                'name': 'Спартак',
                'logo': b'spartak.png',
                'sport': 'football'
            },
            {
                'team_id': 'team_2',
                'name': 'ЦСКА',
                'logo': b'cska.png',
                'sport': 'football'
            }
        ],
        'score': {
            'team_1': 2,
            'team_2': 1
        },
        'goals': [
            {
                'team_id': 'team_1',
                'user_name': 'Иван',
                'user_surname': 'Петров',
                'set_number': 1,
                'time': '15:00',
                'is_penalty': False
            },
            {
                'team_id': 'team_1',
                'user_name': 'Алексей',
                'user_surname': 'Иванов',
                'set_number': 1,
                'time': '35:00',
                'is_penalty': False
            },
            {
                'team_id': 'team_2',
                'user_name': 'Дмитрий',
                'user_surname': 'Смирнов',
                'set_number': 2,
                'time': '60:00',
                'is_penalty': True
            }
        ],
        'after_match_penalties': [
            {
                'team_id': 'team_1',
                'user_name': 'Иван',
                'user_surname': 'Петров',
                'is_success': True
            },
            {
                'team_id': 'team_2',
                'user_name': 'Дмитрий',
                'user_surname': 'Смирнов',
                'is_success': False
            }
        ],
        'location': {
            'name': 'Стадион Лужники',
            'address': 'ул. Лужники, 24',
            'city': 'Москва'
        },
        'date': '2024-03-15T15:00:00Z',
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