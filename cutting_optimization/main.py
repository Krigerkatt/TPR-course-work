"""
Основной модуль программы раскроя материалов
Точка входа приложения
"""

import argparse
import os
import sys
from datetime import datetime

from cutting_algorithm import GuillotineCuttingAlgorithm, Part
from data_handler import DataHandler
from visualizer import CuttingVisualizer


def print_report(report: dict):
    """Выводит отчёт в консоль"""
    print("\n" + "=" * 60)
    print("ОТЧЁТ О РАСКРОЕ МАТЕРИАЛОВ")
    print("=" * 60)
    print(f"Дата выполнения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print(f"Всего листов использовано: {report['total_sheets']}")
    print(f"Общая площадь доступная: {report['total_available_area']:.2f} кв.ед.")
    print(f"Общая площадь использованная: {report['total_used_area']:.2f} кв.ед.")
    print(f"Коэффициент использования материала: {report['total_utilization']:.2f}%")
    print(f"Процент отходов: {report['waste_percentage']:.2f}%")
    print("-" * 60)
    
    if report['sheets']:
        print("\nДетализация по листам:")
        print("-" * 60)
        for sheet in report['sheets']:
            print(f"Лист #{sheet['sheet_id']:3d} | "
                  f"Использование: {sheet['utilization']:6.2f}% | "
                  f"Деталей: {sheet['parts_count']:3d}")
    
    print("=" * 60)
    
    # Проверка критериев
    if report['total_utilization'] >= 80:
        print("✓ КРИТЕРИЙ ЭФФЕКТИВНОСТИ ВЫПОЛНЕН (≥80%)")
    else:
        print("✗ КРИТЕРИЙ ЭФФЕКТИВНОСТИ НЕ ВЫПОЛНЕН (<80%)")
    
    print("=" * 60 + "\n")


def create_sample_data():
    """Создаёт пример входных данных"""
    sample_data = {
        "sheet": {
            "width": 2800,
            "height": 2070
        },
        "allow_rotation": True,
        "parts": [
            {"id": 1, "width": 600, "height": 400, "quantity": 4, "can_rotate": True},
            {"id": 2, "width": 800, "height": 500, "quantity": 3, "can_rotate": True},
            {"id": 3, "width": 400, "height": 300, "quantity": 6, "can_rotate": True},
            {"id": 4, "width": 500, "height": 350, "quantity": 5, "can_rotate": True},
            {"id": 5, "width": 700, "height": 450, "quantity": 2, "can_rotate": True},
            {"id": 6, "width": 300, "height": 250, "quantity": 8, "can_rotate": True},
            {"id": 7, "width": 550, "height": 400, "quantity": 3, "can_rotate": True},
            {"id": 8, "width": 450, "height": 300, "quantity": 4, "can_rotate": True}
        ]
    }
    return sample_data


def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(
        description='Программа автоматического раскроя листовых материалов'
    )
    parser.add_argument('--input', '-i', type=str, default='input_data.json',
                       help='Путь к файлу входных данных (JSON)')
    parser.add_argument('--output', '-o', type=str, default='output',
                       help='Папка для выходных файлов')
    parser.add_argument('--sheet-width', '-W', type=float, default=None,
                       help='Ширина листа (переопределяет данные из файла)')
    parser.add_argument('--sheet-height', '-H', type=float, default=None,
                       help='Высота листа (переопределяет данные из файла)')
    parser.add_argument('--no-rotation', action='store_true',
                       help='Запретить поворот деталей')
    parser.add_argument('--show', action='store_true',
                       help='Показать визуализацию')
    parser.add_argument('--sample', action='store_true',
                       help='Создать пример входных данных')
    
    args = parser.parse_args()
    
    # Создание примера данных
    if args.sample:
        sample_data = create_sample_data()
        DataHandler.save_to_json(sample_data, args.input)
        print(f"Пример данных создан: {args.input}")
        return
    
    # Загрузка данных
    print("Загрузка входных данных...")
    try:
        data = DataHandler.load_from_json(args.input)
    except FileNotFoundError:
        print(f"Файл {args.input} не найден. Создаю пример данных...")
        data = create_sample_data()
        DataHandler.save_to_json(data, args.input)
    
    # Параметры листа
    sheet_width = args.sheet_width or data['sheet']['width']
    sheet_height = args.sheet_height or data['sheet']['height']
    allow_rotation = not args.no_rotation and data.get('allow_rotation', True)
    
    print(f"Размер листа: {sheet_width} x {sheet_height} мм")
    print(f"Поворот деталей: {'разрешён' if allow_rotation else 'запрещён'}")
    
    # Парсинг деталей
    parts = DataHandler.parse_parts(data)
    total_parts = sum(p.quantity for p in parts)
    print(f"Всего деталей для раскроя: {total_parts}")
    
    # Инициализация алгоритма
    print("\nЗапуск алгоритма раскроя...")
    algorithm = GuillotineCuttingAlgorithm(
        sheet_width=sheet_width,
        sheet_height=sheet_height,
        allow_rotation=allow_rotation
    )
    
    # Выполнение раскроя
    sheets = algorithm.place_parts(parts)
    
    # Получение отчёта
    report = algorithm.get_report()
    
    # Вывод отчёта
    print_report(report)
    
    # Визуализация
    print("Генерация визуализации...")
    visualizer = CuttingVisualizer()
    visualizer.visualize_all_sheets(sheets, output_dir=args.output, show=args.show)
    
    # Сохранение отчёта
    report_path = os.path.join(args.output, 'report.json')
    DataHandler.save_report(report, report_path)
    print(f"Отчёт сохранён: {report_path}")
    
    # Сохранение размещённых деталей
    placed_parts_data = []
    for sheet in sheets:
        for part in sheet.placed_parts:
            placed_parts_data.append({
                'sheet_id': sheet.id,
                'part_id': part.part_id,
                'x': part.x,
                'y': part.y,
                'width': part.width,
                'height': part.height,
                'rotated': part.rotated
            })
    
    parts_path = os.path.join(args.output, 'placed_parts.json')
    DataHandler.save_to_json(placed_parts_data, parts_path)
    print(f"Данные о размещении сохранены: {parts_path}")
    
    print("\n✓ Работа завершена успешно!")
    
    # Возврат кода успеха/неудачи
    return 0 if report['total_utilization'] >= 80 else 1


if __name__ == '__main__':
    sys.exit(main())
