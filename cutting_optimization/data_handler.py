"""
Модуль обработки входных и выходных данных
Поддерживает форматы JSON и CSV
"""

import json
import csv
from typing import List, Dict
from cutting_algorithm import Part


class DataHandler:
    """Класс для работы с файлами данных"""
    
    @staticmethod
    def load_from_json(filepath: str) -> Dict:
        """Загружает данные из JSON файла"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def save_to_json(data: Dict, filepath: str):
        """Сохраняет данные в JSON файл"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_from_csv(filepath: str) -> List[Dict]:
        """Загружает данные из CSV файла"""
        parts = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                parts.append({
                    'id': int(row['id']),
                    'width': float(row['width']),
                    'height': float(row['height']),
                    'quantity': int(row['quantity']),
                    'can_rotate': row.get('can_rotate', 'True').lower() == 'true'
                })
        return parts
    
    @staticmethod
    def save_to_csv(parts: List[Dict], filepath: str):
        """Сохраняет данные в CSV файл"""
        if not parts:
            return
        
        fieldnames = ['id', 'width', 'height', 'quantity', 'can_rotate']
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(parts)
    
    @staticmethod
    def parse_parts(data: Dict) -> List[Part]:
        """Преобразует данные в объекты Part"""
        parts = []
        for item in data.get('parts', []):
            part = Part(
                id=item['id'],
                width=item['width'],
                height=item['height'],
                quantity=item['quantity'],
                can_rotate=item.get('can_rotate', True)
            )
            parts.append(part)
        return parts
    
    @staticmethod
    def save_report(report: Dict, filepath: str):
        """Сохраняет отчёт в файл"""
        DataHandler.save_to_json(report, filepath)
