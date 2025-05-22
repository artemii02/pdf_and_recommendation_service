import uuid
import json
import os
import logging
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) )
import service_pb2
import service_pb2_grpc
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics.shapes import String
from reportlab.lib.units import inch
from reportlab.platypus import Image
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

# Директория для вывода PDF (можно переопределить через переменную окружения)
PDF_OUTPUT_DIR = os.environ.get('PDF_OUTPUT_DIR', '/app/temp')

# Регистрация всех стилей шрифтов DejaVuSans
FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(FONTS_DIR, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(FONTS_DIR, 'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Oblique', os.path.join(FONTS_DIR, 'DejaVuSans-Oblique.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-BoldOblique', os.path.join(FONTS_DIR, 'DejaVuSans-BoldOblique.ttf')))
MAIN_FONT = 'DejaVuSans'
BOLD_FONT = 'DejaVuSans-Bold'
ITALIC_FONT = 'DejaVuSans-Oblique'
BOLD_ITALIC_FONT = 'DejaVuSans-BoldOblique'

class SportPDFGenerator:
    def __init__(self):
        self.generators = {
            'football': self._generate_football_pdf,
            'basketball': self._generate_basketball_pdf,
            'hockey': self._generate_hockey_pdf,
            'volleyball': self._generate_volleyball_pdf,
            'tennis': self._generate_tennis_pdf,
            'table_tennis': self._generate_table_tennis_pdf,
            'badminton': self._generate_badminton_pdf,
            'chess': self._generate_chess_pdf,
            'darts': self._generate_darts_pdf,
            'pool': self._generate_pool_pdf,
            'bowling': self._generate_bowling_pdf,
            'curling': self._generate_curling_pdf
        }
    
    def generate(self, template_id, data, canvas):
        logger.info(f'Generating PDF for template_id: {template_id}')
        logger.info(f'Data: {data}')
        if template_id not in self.generators:
            raise ValueError(f'Unsupported template_id: {template_id}')
        return self.generators[template_id](data, canvas)
    
    def _generate_football_pdf(self, data, c):
        match_info = json.loads(data.get('match_info', '{}'))
        stats = json.loads(data.get('stats', '{}'))
        ratings = json.loads(data.get('ratings', '{}'))
        form = json.loads(data.get('form', '[]'))
        # Фон
        c.setFillColorRGB(0.95, 0.97, 1)
        c.rect(0, 0, 612, 792, fill=1, stroke=0)
        y = 760
        # Заголовок
        c.setFont(BOLD_FONT, 28)
        c.setFillColorRGB(0.2, 0.3, 0.7)
        sport = match_info.get('sport', 'Футбол')
        teams = match_info.get('teams', '')
        c.drawString(60, y, f"{sport}: {teams}")
        y -= 40
        # Подзаголовки
        c.setFont(ITALIC_FONT, 16)
        c.setFillColorRGB(0, 0, 0)
        date = match_info.get('date', '')
        tournament = match_info.get('tournament', '')
        stadium = match_info.get('stadium', '')
        city = match_info.get('city', '')
        if date:
            c.drawString(60, y, f"Дата: {date}")
            y -= 22
        if tournament:
            c.drawString(60, y, f"Турнир: {tournament}")
            y -= 22
        if stadium:
            c.drawString(60, y, f"Стадион: {stadium}")
            y -= 22
        if city:
            c.drawString(60, y, f"Город: {city}")
            y -= 28
        # Основная статистика (без эмодзи)
        c.setFont(MAIN_FONT, 14)
        for key, value in stats.items():
            c.drawString(60, y, f'{key}: {value}')
            y -= 18
        y -= 8
        # Рейтинговая таблица
        if ratings:
            self._draw_rating_table(c, ratings, 60, y-10)
            y -= 90 + 20 * len(ratings)
        # График формы команды
        if form:
            self._draw_form_chart(c, form, 60, y-220)
        # Водяной знак
        self._draw_watermark(c)
    
    def _generate_basketball_pdf(self, data, c):
        match_info = json.loads(data.get('match_info', '{}'))
        stats = json.loads(data.get('stats', '{}'))
        ratings = json.loads(data.get('ratings', '{}'))
        form = json.loads(data.get('form', '[]'))
        
        # Фон
        c.setFillColorRGB(0.95, 0.97, 1)
        c.rect(0, 0, 612, 792, fill=1, stroke=0)
        y = 760
        
        # Заголовок
        c.setFont(BOLD_FONT, 28)
        c.setFillColorRGB(0.2, 0.3, 0.7)
        sport = match_info.get('sport', 'Баскетбол')
        teams = match_info.get('teams', '')
        c.drawString(60, y, f"{sport}: {teams}")
        y -= 40
        
        # Подзаголовки
        c.setFont(ITALIC_FONT, 16)
        c.setFillColorRGB(0, 0, 0)
        date = match_info.get('date', '')
        tournament = match_info.get('tournament', '')
        stadium = match_info.get('stadium', '')
        city = match_info.get('city', '')
        
        if date:
            c.drawString(60, y, f"Дата: {date}")
            y -= 22
        if tournament:
            c.drawString(60, y, f"Турнир: {tournament}")
            y -= 22
        if stadium:
            c.drawString(60, y, f"Стадион: {stadium}")
            y -= 22
        if city:
            c.drawString(60, y, f"Город: {city}")
            y -= 28
        
        # Основная статистика
        c.setFont(MAIN_FONT, 14)
        for key, value in stats.items():
            c.drawString(60, y, f'{key}: {value}')
            y -= 18
        y -= 8
        
        # Рейтинговая таблица
        if ratings:
            self._draw_rating_table(c, ratings, 60, y-10)
            y -= 90 + 20 * len(ratings)
        
        # График формы команды
        if form:
            self._draw_form_chart(c, form, 60, y-220)
        
        # Водяной знак
        self._draw_watermark(c)
    
    def _generate_hockey_pdf(self, data, c):
        # Аналогичная реализация для хоккея
        match_info = json.loads(data.get('match_info', '{}'))
        stats = json.loads(data.get('stats', '{}'))
        ratings = json.loads(data.get('ratings', '{}'))
        form = json.loads(data.get('form', '[]'))
        
        # Фон
        c.setFillColorRGB(0.95, 0.97, 1)
        c.rect(0, 0, 612, 792, fill=1, stroke=0)
        y = 760
        
        # Заголовок
        c.setFont(BOLD_FONT, 28)
        c.setFillColorRGB(0.2, 0.3, 0.7)
        sport = match_info.get('sport', 'Хоккей')
        teams = match_info.get('teams', '')
        c.drawString(60, y, f"{sport}: {teams}")
        y -= 40
        
        # Подзаголовки
        c.setFont(ITALIC_FONT, 16)
        c.setFillColorRGB(0, 0, 0)
        date = match_info.get('date', '')
        tournament = match_info.get('tournament', '')
        stadium = match_info.get('stadium', '')
        city = match_info.get('city', '')
        
        if date:
            c.drawString(60, y, f"Дата: {date}")
            y -= 22
        if tournament:
            c.drawString(60, y, f"Турнир: {tournament}")
            y -= 22
        if stadium:
            c.drawString(60, y, f"Стадион: {stadium}")
            y -= 22
        if city:
            c.drawString(60, y, f"Город: {city}")
            y -= 28
        
        # Основная статистика
        c.setFont(MAIN_FONT, 14)
        for key, value in stats.items():
            c.drawString(60, y, f'{key}: {value}')
            y -= 18
        y -= 8
        
        # Рейтинговая таблица
        if ratings:
            self._draw_rating_table(c, ratings, 60, y-10)
            y -= 90 + 20 * len(ratings)
        
        # График формы команды
        if form:
            self._draw_form_chart(c, form, 60, y-220)
        
        # Водяной знак
        self._draw_watermark(c)
    
    def _generate_volleyball_pdf(self, data, c):
        # Аналогичная реализация для волейбола
        match_info = json.loads(data.get('match_info', '{}'))
        stats = json.loads(data.get('stats', '{}'))
        ratings = json.loads(data.get('ratings', '{}'))
        form = json.loads(data.get('form', '[]'))
        
        # Фон
        c.setFillColorRGB(0.95, 0.97, 1)
        c.rect(0, 0, 612, 792, fill=1, stroke=0)
        y = 760
        
        # Заголовок
        c.setFont(BOLD_FONT, 28)
        c.setFillColorRGB(0.2, 0.3, 0.7)
        sport = match_info.get('sport', 'Волейбол')
        teams = match_info.get('teams', '')
        c.drawString(60, y, f"{sport}: {teams}")
        y -= 40
        
        # Подзаголовки
        c.setFont(ITALIC_FONT, 16)
        c.setFillColorRGB(0, 0, 0)
        date = match_info.get('date', '')
        tournament = match_info.get('tournament', '')
        stadium = match_info.get('stadium', '')
        city = match_info.get('city', '')
        
        if date:
            c.drawString(60, y, f"Дата: {date}")
            y -= 22
        if tournament:
            c.drawString(60, y, f"Турнир: {tournament}")
            y -= 22
        if stadium:
            c.drawString(60, y, f"Стадион: {stadium}")
            y -= 22
        if city:
            c.drawString(60, y, f"Город: {city}")
            y -= 28
        
        # Основная статистика
        c.setFont(MAIN_FONT, 14)
        for key, value in stats.items():
            c.drawString(60, y, f'{key}: {value}')
            y -= 18
        y -= 8
        
        # Рейтинговая таблица
        if ratings:
            self._draw_rating_table(c, ratings, 60, y-10)
            y -= 90 + 20 * len(ratings)
        
        # График формы команды
        if form:
            self._draw_form_chart(c, form, 60, y-220)
        
        # Водяной знак
        self._draw_watermark(c)
    
    def _generate_tennis_pdf(self, data, c):
        # Реализация для тенниса
        pass

    def _generate_table_tennis_pdf(self, data, c):
        # Реализация для настольного тенниса
        pass

    def _generate_badminton_pdf(self, data, c):
        # Реализация для бадминтона
        pass

    def _generate_chess_pdf(self, data, c):
        # Реализация для шахмат
        pass

    def _generate_darts_pdf(self, data, c):
        # Реализация для дартса
        pass

    def _generate_pool_pdf(self, data, c):
        # Реализация для пула
        pass

    def _generate_bowling_pdf(self, data, c):
        # Реализация для боулинга
        pass

    def _generate_curling_pdf(self, data, c):
        # Реализация для кёрлинга
        pass
    
    def _draw_rating_table(self, c, ratings, x, y):
        data = [['Место', 'Команда', 'Очки']]
        for i, (team, points) in enumerate(ratings.items()):
            data.append([str(i+1), team, str(points)])
        table = Table(data, colWidths=[50, 180, 60])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('FONTSIZE', (0, 0), (-1, 0), 15),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 13),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ])
        # Чередование цветов строк
        for row in range(1, len(data)):
            bg_color = colors.whitesmoke if row % 2 == 1 else colors.beige
            style.add('BACKGROUND', (0, row), (-1, row), bg_color)
        table.setStyle(style)
        table.wrapOn(c, 0, 0)
        table.drawOn(c, x, y)
    
    def _draw_form_chart(self, c, form_data, x, y):
        # Крупный информативный график формы
        legend_text = "Форма команды: 1 — победа, 0 — поражение"
        # Легенда над графиком
        c.setFont(ITALIC_FONT, 12)
        c.setFillColor(colors.grey)
        c.drawString(x, y + 170, legend_text)
        drawing = Drawing(420, 150)
        data = [(i+1, float(val)) for i, val in enumerate(form_data)]
        lp = LinePlot()
        lp.x = 60
        lp.y = 30
        lp.height = 90
        lp.width = 320
        lp.data = [data]
        lp.lines[0].strokeColor = colors.green
        lp.lines[0].strokeWidth = 2
        lp.lines[0].symbol = makeMarker('Circle')
        lp.lineLabelFormat = '%2.0f'
        lp.xValueAxis.valueMin = 1
        lp.xValueAxis.valueMax = len(form_data)
        lp.xValueAxis.valueStep = 1
        lp.xValueAxis.labelTextFormat = '%d'
        lp.xValueAxis.labels.fontName = MAIN_FONT
        lp.xValueAxis.labels.fontSize = 11
        lp.yValueAxis.valueMin = 0
        lp.yValueAxis.valueMax = 1
        lp.yValueAxis.valueStep = 1
        lp.yValueAxis.labelTextFormat = lambda v: 'Победа' if v == 1 else 'Поражение'
        lp.yValueAxis.labels.fontName = MAIN_FONT
        lp.yValueAxis.labels.fontSize = 11
        drawing.add(lp)
        drawing.drawOn(c, x, y)

    def _draw_watermark(self, c):
        c.saveState()
        watermark_text = "Онлайн-платформа для поиска и управления любительскими спортивными соревнованиями"
        c.setFont(ITALIC_FONT, 12)
        c.setFillColorRGB(0.7, 0.7, 0.7, alpha=0.18)
        # Центрируем по ширине страницы (612pt)
        text_width = c.stringWidth(watermark_text, ITALIC_FONT, 12)
        x = max((612 - text_width) / 2, 0)
        y = 25  # 25pt от нижнего края
        c.drawString(x, y, watermark_text)
        c.restoreState()

class PDFServicer(service_pb2_grpc.PDFServiceServicer):
    def __init__(self):
        self.tasks = {}
        self.pdf_generator = SportPDFGenerator()
        
        # Создаем директорию temp, если её нет
        os.makedirs('temp', exist_ok=True)
        logger.info('Created temp directory')
        
    def CreateMatchPDF(self, request, context):
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {'status': 'PROCESSING'}
        try:
            pdf_path = os.path.join(PDF_OUTPUT_DIR, f'{task_id}.pdf')
            self._generate_match_pdf(request, pdf_path)
            self.tasks[task_id] = {
                'status': 'COMPLETED',
                'pdf_url': f'temp/{task_id}.pdf'
            }
            # Читаем PDF в bytes
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            return service_pb2.PDFResponse(
                task_id=task_id,
                file_name=f'{task_id}.pdf',
                file_data=pdf_bytes,
                mime_type='application/pdf',
                status='COMPLETED'
            )
        except Exception as e:
            logger.error(f'Error creating match PDF: {str(e)}')
            self.tasks[task_id] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return service_pb2.PDFResponse(
                task_id=task_id,
                file_name='',
                file_data=b'',
                mime_type='',
                status='ERROR'
            )
    
    def CreateTournamentPDF(self, request, context):
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {'status': 'PROCESSING'}
        try:
            pdf_path = os.path.join(PDF_OUTPUT_DIR, f'{task_id}.pdf')
            self._generate_tournament_pdf(request, pdf_path)
            self.tasks[task_id] = {
                'status': 'COMPLETED',
                'pdf_url': f'temp/{task_id}.pdf'
            }
            # Читаем PDF в bytes
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            return service_pb2.PDFResponse(
                task_id=task_id,
                file_name=f'{task_id}.pdf',
                file_data=pdf_bytes,
                mime_type='application/pdf',
                status='COMPLETED'
            )
        except Exception as e:
            logger.error(f'Error creating tournament PDF: {str(e)}')
            self.tasks[task_id] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return service_pb2.PDFResponse(
                task_id=task_id,
                file_name='',
                file_data=b'',
                mime_type='',
                status='ERROR'
            )
    
    def GetPDFStatus(self, request, context):
        task_id = request.task_id
        task_info = self.tasks.get(task_id, {
            'status': 'NOT_FOUND',
            'error': 'Task not found'
        })
        
        logger.info(f'Getting status for task_id: {task_id}')
        logger.info(f'Task info: {task_info}')
        
        return service_pb2.PDFStatusResponse(
            status=task_info['status'],
            pdf_url=task_info.get('pdf_url', ''),
            error_message=task_info.get('error', '')
        )
    
    @staticmethod
    def _draw_watermark(c):
        watermark_text = "Онлайн-платформа для поиска и управления любительскими спортивными соревнованиями"
        c.saveState()
        c.setFont(ITALIC_FONT, 12)
        c.setFillColorRGB(0.7, 0.7, 0.7, alpha=0.18)
        text_width = c.stringWidth(watermark_text, ITALIC_FONT, 12)
        x = max((612 - text_width) / 2, 0)
        y = 25
        c.drawString(x, y, watermark_text)
        c.restoreState()

    def _generate_match_pdf(self, match_data, output_path):
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        # Цветной фон заголовка
        c.setFillColorRGB(0.2, 0.3, 0.7)
        c.rect(0, height-80, width, 80, fill=1, stroke=0)
        # Заголовок
        c.setFont(BOLD_FONT, 28)
        c.setFillColorRGB(1, 1, 1)
        title = f"Матч: {match_data.teams[0].name} vs {match_data.teams[1].name}" if match_data.teams and len(match_data.teams) >= 2 else "Данные о командах отсутствуют"
        c.drawString(50, height-60, title)
        # Счет
        c.setFont(BOLD_FONT, 40)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawCentredString(width/2, height-120, f"{getattr(match_data.score, 'team_1', 0) if hasattr(match_data, 'score') and match_data.score else 0} - {getattr(match_data.score, 'team_2', 0) if hasattr(match_data, 'score') and match_data.score else 0}")
        y = height-170
        # Разделитель
        c.setStrokeColorRGB(0.2, 0.3, 0.7)
        c.setLineWidth(2)
        c.line(40, y, width-40, y)
        y -= 25
        # Таблица голов
        c.setFont(BOLD_FONT, 16)
        c.drawString(50, y, "Голы:")
        y -= 20
        c.setFont(MAIN_FONT, 12)
        if hasattr(match_data, 'goals') and match_data.goals:
            data = [["Время", "Команда", "Игрок", "Пенальти"]]
            for goal in match_data.goals:
                team = next((t for t in match_data.teams if t.team_id == goal.team_id), None)
                team_name = team.name if team else 'Неизвестная команда'
                data.append([
                    getattr(goal, 'time', '-'),
                    team_name,
                    getattr(goal, 'user_id', '-'),
                    "Да" if getattr(goal, 'is_penalty', False) else "Нет"
                ])
            table = Table(data, colWidths=[60, 120, 100, 60])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 13),
                ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ])
            table.setStyle(style)
            table.wrapOn(c, 0, 0)
            table.drawOn(c, 50, y-table._height)
            y -= table._height + 18  # увеличенный отступ
        else:
            c.drawString(70, y, "Нет данных о голах")
            y -= 20
        # Таблица пенальти
        c.setFont(BOLD_FONT, 16)
        c.drawString(50, y, "Пенальти:")
        y -= 20
        c.setFont(MAIN_FONT, 12)
        if hasattr(match_data, 'after_match_penalties') and match_data.after_match_penalties:
            data = [["Команда", "Игрок", "Результат"]]
            for penalty in match_data.after_match_penalties:
                team = next((t for t in match_data.teams if t.team_id == penalty.team_id), None)
                team_name = team.name if team else 'Неизвестная команда'
                result = "Забит" if getattr(penalty, 'is_success', False) else "Не забит"
                data.append([team_name, getattr(penalty, 'user_id', '-'), result])
            table = Table(data, colWidths=[120, 100, 80])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 13),
                ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ])
            table.setStyle(style)
            table.wrapOn(c, 0, 0)
            table.drawOn(c, 50, y-table._height)
            y -= table._height + 18  # увеличенный отступ
        else:
            c.drawString(70, y, "Нет информации о пенальти")
            y -= 20
        # Место проведения
        c.setFont(BOLD_FONT, 14)
        c.drawString(50, y, "Место проведения:")
        y -= 18
        c.setFont(MAIN_FONT, 12)
        if hasattr(match_data, 'location') and match_data.location:
            c.drawString(70, y, f"{getattr(match_data.location, 'name', '-')}")
            y -= 15
            c.drawString(70, y, f"{getattr(match_data.location, 'address', '-')}")
            y -= 15
            c.drawString(70, y, f"{getattr(match_data.location, 'city', '-')}")
            y -= 15
        else:
            c.drawString(70, y, "Нет данных о месте проведения")
            y -= 15
        # Дата
        y -= 10
        c.setFont(MAIN_FONT, 12)
        if hasattr(match_data, 'date') and match_data.date:
            try:
                match_date = datetime.fromisoformat(match_data.date.replace('Z', '+00:00'))
                c.drawString(50, y, f"Дата: {match_date.strftime('%d.%m.%Y %H:%M')}")
            except Exception as e:
                c.drawString(50, y, f"Дата: {getattr(match_data, 'date', '-')}")
        else:
            c.drawString(50, y, "Дата: -")
        # Водяной знак
        PDFServicer._draw_watermark(c)
        c.save()
    
    def _generate_tournament_pdf(self, tournament_data, output_path):
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        # Словарь для перевода видов спорта
        sport_ru = {
            'football': 'Футбол',
            'basketball': 'Баскетбол',
            'hockey': 'Хоккей',
            'volleyball': 'Волейбол',
            'tennis': 'Теннис',
            'table_tennis': 'Настольный теннис',
            'badminton': 'Бадминтон',
            'chess': 'Шахматы',
            'darts': 'Дартс',
            'pool': 'Пул',
            'bowling': 'Боулинг',
            'curling': 'Кёрлинг'
        }
        # Цветная шапка
        c.setFillColorRGB(0.2, 0.3, 0.7)
        c.rect(0, height-80, width, 80, fill=1, stroke=0)
        # Заголовок
        c.setFont(BOLD_FONT, 28)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(50, height-60, getattr(tournament_data, 'name', 'Без названия'))
        # Основная информация
        c.setFont(MAIN_FONT, 14)
        c.setFillColorRGB(0, 0, 0)
        y = height-110
        sport = getattr(tournament_data, 'sport', '-')
        sport_display = sport_ru.get(sport, sport.capitalize())
        c.drawString(50, y, f"Спорт: {sport_display}")
        y -= 20
        c.drawString(50, y, f"Организация: {getattr(tournament_data, 'organization_name', '-')}")
        y -= 20
        c.drawString(50, y, f"Город: {getattr(tournament_data, 'city', '-')}")
        y -= 20
        c.drawString(50, y, f"Описание: {getattr(tournament_data, 'description', '-')}")
        y -= 30
        # Этапы турнира
        c.setFont(BOLD_FONT, 18)
        c.drawString(50, y, "Этапы турнира:")
        y -= 22
        c.setFont(MAIN_FONT, 13)
        if hasattr(tournament_data, 'stages') and tournament_data.stages:
            for stage in tournament_data.stages:
                c.setFont(BOLD_FONT, 14)
                c.drawString(70, y, getattr(stage, 'name', 'Без названия этапа'))
                y -= 18
                if hasattr(stage, 'matches') and stage.matches:
                    c.setFont(MAIN_FONT, 12)
                    data = [["Матч", "Счёт", "Дата"]]
                    for match in stage.matches:
                        if hasattr(match, 'teams') and len(match.teams) >= 2:
                            match_text = f"{match.teams[0].name} vs {match.teams[1].name}"
                        else:
                            match_text = "-"
                        score_text = f"{getattr(match.score, 'team_1', 0)} - {getattr(match.score, 'team_2', 0)}" if hasattr(match, 'score') and match.score else "-"
                        date_text = getattr(match, 'date', '-')
                        data.append([match_text, score_text, date_text])
                    table = Table(data, colWidths=[180, 60, 100])
                    style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
                        ('FONTSIZE', (0, 1), (-1, -1), 11),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                    ])
                    table.setStyle(style)
                    table.wrapOn(c, 0, 0)
                    table.drawOn(c, 90, y-18*len(data))
                    y -= 18*len(data) + 10
                else:
                    c.setFont(ITALIC_FONT, 12)
                    c.drawString(90, y, "Нет матчей в этом этапе")
                    y -= 15
        else:
            c.setFont(ITALIC_FONT, 13)
            c.drawString(70, y, "Нет данных об этапах")
            y -= 15
        y -= 20
        # Группы
        c.setFont(BOLD_FONT, 18)
        c.drawString(50, y, "Группы:")
        y -= 22
        c.setFont(MAIN_FONT, 13)
        if hasattr(tournament_data, 'groups') and tournament_data.groups:
            for group in tournament_data.groups:
                c.setFont(BOLD_FONT, 14)
                c.drawString(70, y, getattr(group, 'name', 'Без названия группы'))
                y -= 18
                c.setFont(MAIN_FONT, 12)
                if hasattr(group, 'teams') and group.teams:
                    data = [["Команда", "Вид спорта"]]
                    for team in group.teams:
                        data.append([getattr(team, 'name', '-'), sport_ru.get(getattr(team, 'sport', '-'), getattr(team, 'sport', '-').capitalize())])
                    table = Table(data, colWidths=[180, 100])
                    style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
                        ('FONTSIZE', (0, 1), (-1, -1), 11),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                    ])
                    table.setStyle(style)
                    table.wrapOn(c, 0, 0)
                    table.drawOn(c, 90, y-18*len(data))
                    y -= 18*len(data) + 10
                else:
                    c.drawString(90, y, "Нет данных о командах в группе")
                    y -= 15
        else:
            c.setFont(ITALIC_FONT, 13)
            c.drawString(70, y, "Нет данных о группах")
            y -= 15
        # Водяной знак
        PDFServicer._draw_watermark(c)
        c.save() 