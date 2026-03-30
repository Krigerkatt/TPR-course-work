"""
Модуль алгоритма двумерного раскроя материалов
Реализует эвристический алгоритм с гильотинным типом раскроя
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from copy import deepcopy


@dataclass
class Part:
    """Класс представляющий деталь для раскроя"""
    id: int
    width: float
    height: float
    quantity: int
    can_rotate: bool = True
    
    def get_dimensions(self, rotated: bool = False) -> Tuple[float, float]:
        """Возвращает размеры детали с учётом возможного поворота"""
        if rotated and self.can_rotate:
            return (self.height, self.width)
        return (self.width, self.height)


@dataclass
class PlacedPart:
    """Класс представляющий размещённую деталь на листе"""
    part_id: int
    x: float
    y: float
    width: float
    height: float
    rotated: bool = False


@dataclass
class Sheet:
    """Класс представляющий лист материала"""
    id: int
    width: float
    height: float
    placed_parts: List[PlacedPart]
    used_area: float = 0.0
    
    def get_utilization(self) -> float:
        """Возвращает процент использования материала"""
        total_area = self.width * self.height
        if total_area == 0:
            return 0.0
        return (self.used_area / total_area) * 100


class GuillotineCuttingAlgorithm:
    """
    Алгоритм гильотинного раскроя с эвристической оптимизацией
    """
    
    def __init__(self, sheet_width: float, sheet_height: float, 
                 allow_rotation: bool = True):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.allow_rotation = allow_rotation
        self.sheets: List[Sheet] = []
        self.free_rectangles: List[Tuple[float, float, float, float]] = []
        
    def _initialize_sheet(self, sheet_id: int) -> Sheet:
        """Инициализирует новый лист для раскроя"""
        sheet = Sheet(
            id=sheet_id,
            width=self.sheet_width,
            height=self.sheet_height,
            placed_parts=[]
        )
        self.free_rectangles = [(0, 0, self.sheet_width, self.sheet_height)]
        return sheet
    
    def _find_best_position(self, width: float, height: float, 
                           rotated: bool = False) -> Optional[Tuple[int, float, float]]:
        """
        Находит наилучшую позицию для размещения детали
        Возвращает индекс свободного прямоугольника и координаты размещения
        """
        if rotated:
            w, h = height, width
        else:
            w, h = width, height
        
        best_idx = -1
        best_score = float('inf')
        best_x, best_y = 0, 0
        
        for idx, (x, y, rect_w, rect_h) in enumerate(self.free_rectangles):
            if rect_w >= w and rect_h >= h:
                # Оценка качества размещения (минимизация отходов)
                score = (rect_w - w) + (rect_h - h)
                if score < best_score:
                    best_score = score
                    best_idx = idx
                    best_x, best_y = x, y
        
        if best_idx >= 0:
            return (best_idx, best_x, best_y)
        return None
    
    def _split_free_rectangle(self, rect_idx: int, x: float, y: float, 
                             width: float, height: float):
        """
        Разделяет свободный прямоугольник после размещения детали
        Реализует гильотинный тип раскроя
        """
        rect = self.free_rectangles[rect_idx]
        rect_x, rect_y, rect_w, rect_h = rect
        
        # Удаляем исходный прямоугольник
        self.free_rectangles.pop(rect_idx)
        
        # Создаём новые свободные области (гильотинный разрез)
        # Вариант 1: разрез по горизонтали
        if rect_w - width > 0:
            self.free_rectangles.append((x + width, y, rect_w - width, height))
        if rect_h - height > 0:
            self.free_rectangles.append((x, y + height, rect_w, rect_h - height))
        
        # Сортируем свободные прямоугольники для улучшения упаковки
        self.free_rectangles.sort(key=lambda r: (r[2] * r[3]), reverse=True)
    
    def _check_overlap(self, x: float, y: float, width: float, height: float,
                      placed_parts: List[PlacedPart]) -> bool:
        """Проверяет наличие пересечений с уже размещёнными деталями"""
        for part in placed_parts:
            # Проверка пересечения прямоугольников
            if not (x >= part.x + part.width or 
                    x + width <= part.x or
                    y >= part.y + part.height or 
                    y + height <= part.y):
                return True
        return False
    
    def _check_bounds(self, x: float, y: float, width: float, height: float) -> bool:
        """Проверяет выход за границы листа"""
        return (x >= 0 and y >= 0 and 
                x + width <= self.sheet_width and 
                y + height <= self.sheet_height)
    
    def place_parts(self, parts: List[Part]) -> List[Sheet]:
        """
        Основной метод размещения всех деталей на листах
        """
        self.sheets = []
        sheet_id = 0
        
        # Создаём список всех деталей с учётом количества
        all_parts = []
        for part in parts:
            for i in range(part.quantity):
                all_parts.append({
                    'part': part,
                    'original_id': part.id
                })
        
        # Сортируем детали по площади (убывание) для лучшей упаковки
        all_parts.sort(key=lambda p: p['part'].width * p['part'].height, 
                      reverse=True)
        
        unplaced_parts = []
        
        for item in all_parts:
            part = item['part']
            placed = False
            
            # Пробуем разместить на существующих листах
            for sheet in self.sheets:
                self.free_rectangles = self._calculate_free_rectangles(sheet)
                
                # Пробуем без поворота
                position = self._find_best_position(part.width, part.height)
                if position:
                    rect_idx, x, y = position
                    if (self._check_bounds(x, y, part.width, part.height) and
                        not self._check_overlap(x, y, part.width, part.height, 
                                               sheet.placed_parts)):
                        
                        self._split_free_rectangle(rect_idx, x, y, 
                                                  part.width, part.height)
                        
                        placed_part = PlacedPart(
                            part_id=item['original_id'],
                            x=x, y=y,
                            width=part.width, height=part.height,
                            rotated=False
                        )
                        sheet.placed_parts.append(placed_part)
                        sheet.used_area += part.width * part.height
                        placed = True
                        break
                
                # Пробуем с поворотом на 90 градусов
                if not placed and part.can_rotate and self.allow_rotation:
                    position = self._find_best_position(part.height, part.width)
                    if position:
                        rect_idx, x, y = position
                        if (self._check_bounds(x, y, part.height, part.width) and
                            not self._check_overlap(x, y, part.height, part.width,
                                                   sheet.placed_parts)):
                            
                            self._split_free_rectangle(rect_idx, x, y,
                                                      part.height, part.width)
                            
                            placed_part = PlacedPart(
                                part_id=item['original_id'],
                                x=x, y=y,
                                width=part.height, height=part.width,
                                rotated=True
                            )
                            sheet.placed_parts.append(placed_part)
                            sheet.used_area += part.width * part.height
                            placed = True
                            break
            
            # Если не разместили, создаём новый лист
            if not placed:
                sheet_id += 1
                new_sheet = self._initialize_sheet(sheet_id)
                
                # Пробуем разместить на новом листе
                position = self._find_best_position(part.width, part.height)
                if position:
                    rect_idx, x, y = position
                    placed_part = PlacedPart(
                        part_id=item['original_id'],
                        x=x, y=y,
                        width=part.width, height=part.height,
                        rotated=False
                    )
                    new_sheet.placed_parts.append(placed_part)
                    new_sheet.used_area += part.width * part.height
                    self._split_free_rectangle(rect_idx, x, y,
                                              part.width, part.height)
                    self.sheets.append(new_sheet)
                    placed = True
                
                # Пробуем с поворотом
                if not placed and part.can_rotate and self.allow_rotation:
                    self.free_rectangles = [(0, 0, self.sheet_width, 
                                            self.sheet_height)]
                    position = self._find_best_position(part.height, part.width)
                    if position:
                        rect_idx, x, y = position
                        placed_part = PlacedPart(
                            part_id=item['original_id'],
                            x=x, y=y,
                            width=part.height, height=part.width,
                            rotated=True
                        )
                        new_sheet.placed_parts.append(placed_part)
                        new_sheet.used_area += part.width * part.height
                        self._split_free_rectangle(rect_idx, x, y,
                                                  part.height, part.width)
                        self.sheets.append(new_sheet)
                        placed = True
                
                if not placed:
                    unplaced_parts.append(item)
        
        return self.sheets
    
    def _calculate_free_rectangles(self, sheet: Sheet) -> List[Tuple[float, float, float, float]]:
        """
        Вычисляет свободные прямоугольники на основе размещённых деталей
        Использует алгоритм maximal rectangles для нахождения всех свободных областей
        """
        if not sheet.placed_parts:
            return [(0, 0, self.sheet_width, self.sheet_height)]
        
        # Начинаем с одного большого прямоугольника
        free_rects = [(0, 0, self.sheet_width, self.sheet_height)]
        
        # Для каждой размещённой детали разделяем свободные прямоугольники
        for part in sheet.placed_parts:
            new_free_rects = []
            for rect in free_rects:
                rx, ry, rw, rh = rect
                px, py, pw, ph = part.x, part.y, part.width, part.height
                
                # Проверяем пересечение
                if not (px >= rx + rw or px + pw <= rx or py >= ry + rh or py + ph <= ry):
                    # Есть пересечение - разделяем прямоугольник
                    # Левая часть
                    if px > rx:
                        new_free_rects.append((rx, ry, px - rx, rh))
                    # Правая часть
                    if px + pw < rx + rw:
                        new_free_rects.append((px + pw, ry, rx + rw - (px + pw), rh))
                    # Нижняя часть (под деталью)
                    if py > ry:
                        new_free_rects.append((rx, ry, rw, py - ry))
                    # Верхняя часть (над деталью)
                    if py + ph < ry + rh:
                        new_free_rects.append((rx, py + ph, rw, ry + rh - (py + ph)))
                else:
                    # Нет пересечения - сохраняем прямоугольник
                    new_free_rects.append(rect)
            
            free_rects = new_free_rects
        
        # Удаляем дубликаты и очень маленькие прямоугольники
        min_size = 1.0
        unique_rects = []
        seen = set()
        for rect in free_rects:
            if rect[2] >= min_size and rect[3] >= min_size:
                key = (round(rect[0], 1), round(rect[1], 1), 
                       round(rect[2], 1), round(rect[3], 1))
                if key not in seen:
                    seen.add(key)
                    unique_rects.append(rect)
        
        # Сортируем по площади (убывание)
        unique_rects.sort(key=lambda r: r[2] * r[3], reverse=True)
        
        return unique_rects
    
    def get_report(self) -> dict:
        """Формирует отчёт о раскрое"""
        if not self.sheets:
            return {
                'total_sheets': 0,
                'total_utilization': 0.0,
                'sheets': []
            }
        
        total_area = len(self.sheets) * self.sheet_width * self.sheet_height
        used_area = sum(sheet.used_area for sheet in self.sheets)
        
        sheets_info = []
        for sheet in self.sheets:
            sheets_info.append({
                'sheet_id': sheet.id,
                'utilization': sheet.get_utilization(),
                'parts_count': len(sheet.placed_parts)
            })
        
        # Считаем средневзвешенный коэффициент использования
        # (общая полезная площадь / общая площадь всех листов)
        overall_utilization = (used_area / total_area * 100) if total_area > 0 else 0
        
        return {
            'total_sheets': len(self.sheets),
            'total_utilization': overall_utilization,
            'total_used_area': used_area,
            'total_available_area': total_area,
            'waste_percentage': 100 - overall_utilization if total_area > 0 else 100,
            'sheets': sheets_info
        }
