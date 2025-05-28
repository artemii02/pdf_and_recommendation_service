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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable

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

# Словарь для перевода видов спорта на русский (только 4 вида)
SPORT_RU = {
    'football': 'Футбол',
    'basketball': 'Баскетбол',
    'hockey': 'Хоккей',
    'volleyball': 'Волейбол',
}

class ScoreBox(Flowable):
    def __init__(self, score_text, width=2.2*inch, height=0.85*inch, font_size=40):
        super().__init__()
        self.score_text = score_text
        self.width = width
        self.height = height
        self.font_size = font_size
        self.font_name = BOLD_FONT
        self.bg_color = colors.HexColor('#e6eaf5')
        self.border_color = colors.HexColor('#334488')
        self.text_color = colors.HexColor('#222')

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        # Фон
        c.setFillColor(self.bg_color)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        # Рамка
        c.setStrokeColor(self.border_color)
        c.setLineWidth(2)
        c.rect(0, 0, self.width, self.height, fill=0, stroke=1)
        # Текст счета
        c.setFont(self.font_name, self.font_size)
        c.setFillColor(self.text_color)
        text_width = c.stringWidth(self.score_text, self.font_name, self.font_size)
        x = (self.width - text_width) / 2
        y = (self.height - self.font_size) / 2 + 6  # +6 для лучшего визуального центрирования
        c.drawString(x, y, self.score_text)

class SportPDFGenerator:
    def __init__(self):
        self.generators = {
            'football': self._generate_football_pdf,
            'basketball': self._generate_basketball_pdf,
            'hockey': self._generate_hockey_pdf,
            'volleyball': self._generate_volleyball_pdf
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
        pass

    def _generate_table_tennis_pdf(self, data, c):
        pass

    def _generate_badminton_pdf(self, data, c):
        pass

    def _generate_chess_pdf(self, data, c):
        pass

    def _generate_darts_pdf(self, data, c):
        pass

    def _generate_pool_pdf(self, data, c):
        pass

    def _generate_bowling_pdf(self, data, c):
        pass

    def _generate_curling_pdf(self, data, c):
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
        # Стили
        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleN.fontName = MAIN_FONT
        styleN.fontSize = 12
        styleN.leading = 14
        styleB = styles['Heading1']
        styleB.fontName = BOLD_FONT
        styleB.fontSize = 22
        styleB.alignment = TA_CENTER
        styleTitle = ParagraphStyle('Title', fontName=BOLD_FONT, fontSize=22, alignment=TA_CENTER, textColor=colors.white, spaceAfter=12, leading=26)
        styleHeader = ParagraphStyle('Header', fontName=BOLD_FONT, fontSize=16, alignment=TA_LEFT, textColor=colors.HexColor('#334488'))
        styleTableHeader = ParagraphStyle('TableHeader', fontName=BOLD_FONT, fontSize=13, alignment=TA_CENTER, textColor=colors.whitesmoke)
        styleTableCell = ParagraphStyle('TableCell', fontName=MAIN_FONT, fontSize=12, alignment=TA_CENTER)
        styleScore = ParagraphStyle('Score', fontName=BOLD_FONT, fontSize=40, alignment=TA_CENTER, textColor=colors.HexColor('#222'))

        elements = []
        # Шапка с логотипами и названием
        logos = []
        for team in getattr(match_data, 'teams', []):
            if hasattr(team, 'logo') and team.logo:
                try:
                    img = Image(BytesIO(bytes(team.logo)), width=0.5*inch, height=0.5*inch)
                    logos.append(img)
                except Exception:
                    pass
        sport_en = getattr(match_data, 'sport', None)
        sport_ru = SPORT_RU.get(sport_en.lower(), sport_en.capitalize() if sport_en else '') if sport_en else ''
        title_text = f"{sport_ru}: {match_data.teams[0].name} vs {match_data.teams[1].name}" if match_data.teams and len(match_data.teams) >= 2 else "Данные о командах отсутствуют"
        title_paragraph = Paragraph(title_text, styleTitle)
        # Формируем шапку как таблицу с цветным фоном и увеличенной высотой
        if len(logos) == 2:
            data = [[logos[0], title_paragraph, logos[1]]]
            col_widths = [0.8*inch, 4.4*inch, 0.8*inch]
        elif len(logos) == 1:
            data = [[logos[0], title_paragraph, '']]
            col_widths = [0.8*inch, 5.2*inch, 0.0*inch]
        else:
            data = [[title_paragraph]]
            col_widths = [6*inch]
        table = Table(data, colWidths=col_widths, rowHeights=[0.9*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#334488')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.18*inch))
        # Основная информация (дата, место проведения)
        info = []
        if hasattr(match_data, 'date') and match_data.date:
            try:
                match_date = datetime.fromisoformat(match_data.date.replace('Z', '+00:00'))
                info.append(f"Дата: {match_date.strftime('%d.%m.%Y %H:%M')}")
            except Exception:
                info.append(f"Дата: {getattr(match_data, 'date', '-')}")
        if hasattr(match_data, 'location') and match_data.location:
            info.append(f"Место проведения: {getattr(match_data.location, 'name', '-')}, {getattr(match_data.location, 'address', '-')}, {getattr(match_data.location, 'city', '-')}")
        elements.append(Paragraph('<br/>'.join(info), styleN))
        elements.append(Spacer(1, 0.12*inch))
        # Счет — кастомный ScoreBox по центру страницы
        score = f"{getattr(match_data.score, 'team_1', 0) if hasattr(match_data, 'score') and match_data.score else 0} - {getattr(match_data.score, 'team_2', 0) if hasattr(match_data, 'score') and match_data.score else 0}"
        score_box = ScoreBox(score)
        score_table = Table([[score_box]], colWidths=[6*inch])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 0.18*inch))
        # Таблица голов
        elements.append(Paragraph("Голы:", styleHeader))
        data = [[Paragraph("Время", styleTableHeader), Paragraph("Команда", styleTableHeader), Paragraph("Игрок", styleTableHeader), Paragraph("Пенальти", styleTableHeader)]]
        if hasattr(match_data, 'goals') and match_data.goals:
            for goal in match_data.goals:
                team = next((t for t in match_data.teams if t.team_id == goal.team_id), None)
                team_name = team.name if team else 'Неизвестная команда'
                data.append([
                    Paragraph(str(getattr(goal, 'time', '-')), styleTableCell),
                    Paragraph(team_name, styleTableCell),
                    Paragraph(getattr(goal, 'user_id', '-'), styleTableCell),
                    Paragraph("Да" if getattr(goal, 'is_penalty', False) else "Нет", styleTableCell)
                ])
        else:
            data.append([Paragraph("-", styleTableCell)]*4)
        table = Table(data, colWidths=[0.9*inch, 1.7*inch, 1.5*inch, 0.9*inch], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('FONTSIZE', (0, 0), (-1, 0), 13),
            ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.15*inch))
        # Таблица пенальти
        elements.append(Paragraph("Пенальти:", styleHeader))
        data = [[Paragraph("Команда", styleTableHeader), Paragraph("Игрок", styleTableHeader), Paragraph("Результат", styleTableHeader)]]
        if hasattr(match_data, 'after_match_penalties') and match_data.after_match_penalties:
            for penalty in match_data.after_match_penalties:
                team = next((t for t in match_data.teams if t.team_id == penalty.team_id), None)
                team_name = team.name if team else 'Неизвестная команда'
                result = "Забит" if getattr(penalty, 'is_success', False) else "Не забит"
                data.append([
                    Paragraph(team_name, styleTableCell),
                    Paragraph(getattr(penalty, 'user_id', '-'), styleTableCell),
                    Paragraph(result, styleTableCell)
                ])
        else:
            data.append([Paragraph("-", styleTableCell)]*3)
        table = Table(data, colWidths=[1.7*inch, 1.5*inch, 1.1*inch], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('FONTSIZE', (0, 0), (-1, 0), 13),
            ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.15*inch))
        # Водяной знак (будет добавлен на каждую страницу через onPage)
        def add_watermark(canvas, doc):
            canvas.saveState()
            watermark_text = "Онлайн-платформа для поиска и управления любительскими спортивными соревнованиями"
            canvas.setFont(ITALIC_FONT, 12)
            canvas.setFillColorRGB(0.7, 0.7, 0.7, alpha=0.18)
            text_width = canvas.stringWidth(watermark_text, ITALIC_FONT, 12)
            x = max((letter[0] - text_width) / 2, 0)
            y = 25
            canvas.drawString(x, y, watermark_text)
            canvas.restoreState()
        doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)

    def _generate_tournament_pdf(self, tournament_data, output_path):
        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleN.fontName = MAIN_FONT
        styleN.fontSize = 12
        styleN.leading = 14
        styleB = styles['Heading1']
        styleB.fontName = BOLD_FONT
        styleB.fontSize = 22
        styleB.alignment = TA_CENTER
        styleTitle = ParagraphStyle('Title', fontName=BOLD_FONT, fontSize=22, alignment=TA_CENTER, textColor=colors.white, spaceAfter=12, leading=26)
        styleHeader = ParagraphStyle('Header', fontName=BOLD_FONT, fontSize=16, alignment=TA_LEFT, textColor=colors.HexColor('#334488'))
        styleTableHeader = ParagraphStyle('TableHeader', fontName=BOLD_FONT, fontSize=13, alignment=TA_CENTER, textColor=colors.whitesmoke)
        styleTableCell = ParagraphStyle('TableCell', fontName=MAIN_FONT, fontSize=12, alignment=TA_CENTER)
        elements = []
        # Логотип турнира (если есть)
        logo = getattr(tournament_data, 'logo', None)
        if logo:
            try:
                img = Image(BytesIO(bytes(logo)), width=0.7*inch, height=0.7*inch)
                logo_cell = img
            except Exception:
                logo_cell = ''
        else:
            logo_cell = ''
        title = getattr(tournament_data, 'name', 'Без названия')
        title_paragraph = Paragraph(title, styleTitle)
        # Шапка как таблица с цветным фоном и увеличенной высотой
        data = [[logo_cell, title_paragraph, '']]
        col_widths = [0.8*inch, 4.4*inch, 0.8*inch]
        table = Table(data, colWidths=col_widths, rowHeights=[0.9*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#334488')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.15*inch))
        # Основная информация
        sport_en = getattr(tournament_data, 'sport', '-')
        sport_display = SPORT_RU.get(sport_en.lower(), sport_en.capitalize())
        info = [
            f"Спорт: {sport_display}",
            f"Организация: {getattr(tournament_data, 'organization_name', '-')}" ,
            f"Город: {getattr(tournament_data, 'city', '-')}" ,
            f"Описание: {getattr(tournament_data, 'description', '-')}"
        ]
        elements.append(Paragraph('<br/>'.join(info), styleN))
        elements.append(Spacer(1, 0.15*inch))
        # Этапы турнира
        elements.append(Paragraph("Этапы турнира:", styleHeader))
        if hasattr(tournament_data, 'stages') and tournament_data.stages:
            for stage in tournament_data.stages:
                elements.append(Paragraph(getattr(stage, 'name', 'Без названия этапа'), styleB))
                data = [[Paragraph("Матч", styleTableHeader), Paragraph("Счёт", styleTableHeader), Paragraph("Дата", styleTableHeader)]]
                if hasattr(stage, 'matches') and stage.matches:
                    for match in stage.matches:
                        if hasattr(match, 'teams') and len(match.teams) >= 2:
                            match_text = f"{match.teams[0].name} vs {match.teams[1].name}"
                        else:
                            match_text = "-"
                        score_text = f"{getattr(match.score, 'team_1', 0)} - {getattr(match.score, 'team_2', 0)}" if hasattr(match, 'score') and match.score else "-"
                        date_text = getattr(match, 'date', '-')
                        data.append([
                            Paragraph(match_text, styleTableCell),
                            Paragraph(score_text, styleTableCell),
                            Paragraph(date_text, styleTableCell)
                        ])
                else:
                    data.append([Paragraph("-", styleTableCell)]*3)
                table = Table(data, colWidths=[2.5*inch, 1*inch, 1.5*inch], repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
                    ('FONTSIZE', (0, 0), (-1, 0), 13),
                    ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("Нет данных об этапах", styleN))
        elements.append(Spacer(1, 0.15*inch))
        # Группы
        elements.append(Paragraph("Группы:", styleHeader))
        if hasattr(tournament_data, 'groups') and tournament_data.groups:
            for group in tournament_data.groups:
                elements.append(Paragraph(getattr(group, 'name', 'Без названия группы'), styleB))
                data = [[Paragraph("Команда", styleTableHeader), Paragraph("Вид спорта", styleTableHeader)]]
                if hasattr(group, 'teams') and group.teams:
                    for team in group.teams:
                        sport_disp = SPORT_RU.get(getattr(team, 'sport', '-').lower(), getattr(team, 'sport', '-').capitalize())
                        data.append([
                            Paragraph(getattr(team, 'name', '-'), styleTableCell),
                            Paragraph(sport_disp, styleTableCell)
                        ])
                else:
                    data.append([Paragraph("-", styleTableCell)]*2)
                table = Table(data, colWidths=[2.5*inch, 2*inch], repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
                    ('FONTSIZE', (0, 0), (-1, 0), 13),
                    ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("Нет данных о группах", styleN))
        # Водяной знак (будет добавлен на каждую страницу через onPage)
        def add_watermark(canvas, doc):
            canvas.saveState()
            watermark_text = "Онлайн-платформа для поиска и управления любительскими спортивными соревнованиями"
            canvas.setFont(ITALIC_FONT, 12)
            canvas.setFillColorRGB(0.7, 0.7, 0.7, alpha=0.18)
            text_width = canvas.stringWidth(watermark_text, ITALIC_FONT, 12)
            x = max((letter[0] - text_width) / 2, 0)
            y = 25
            canvas.drawString(x, y, watermark_text)
            canvas.restoreState()
        doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark) 