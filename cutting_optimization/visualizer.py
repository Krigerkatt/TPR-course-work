"""
Модуль визуализации карт раскроя
Использует Matplotlib для построения графиков
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
from typing import List
from cutting_algorithm import Sheet, PlacedPart
import numpy as np


class CuttingVisualizer:
    """Класс для визуализации карт раскроя"""
    
    def __init__(self, dpi: int = 150):
        self.dpi = dpi
        self.colors = plt.cm.tab20.colors
    
    def _get_color(self, part_id: int) -> tuple:
        """Возвращает цвет для детали по её ID"""
        return self.colors[part_id % len(self.colors)]
    
    def visualize_sheet(self, sheet: Sheet, output_path: str = None,
                       show: bool = False):
        """
        Визуализирует один лист раскроя
        """
        fig, ax = plt.subplots(1, figsize=(10, 8), dpi=self.dpi)
        
        # Рисуем границы листа
        sheet_rect = Rectangle((0, 0), sheet.width, sheet.height,
                              linewidth=2, edgecolor='black', 
                              facecolor='lightgray', alpha=0.3)
        ax.add_patch(sheet_rect)
        
        # Рисуем размещённые детали
        for part in sheet.placed_parts:
            color = self._get_color(part.part_id)
            rect = Rectangle((part.x, part.y), part.width, part.height,
                           linewidth=1.5, edgecolor='black',
                           facecolor=color, alpha=0.7)
            ax.add_patch(rect)
            
            # Добавляем номер детали
            center_x = part.x + part.width / 2
            center_y = part.y + part.height / 2
            ax.text(center_x, center_y, f'{part.part_id}',
                   ha='center', va='center', fontsize=8, 
                   color='black', fontweight='bold')
        
        # Настройка осей
        ax.set_xlim(-sheet.width * 0.05, sheet.width * 1.05)
        ax.set_ylim(-sheet.height * 0.05, sheet.height * 1.05)
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # Заголовки
        utilization = sheet.get_utilization()
        ax.set_title(f'Лист #{sheet.id} | Использование: {utilization:.1f}%',
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Ширина (мм)', fontsize=12)
        ax.set_ylabel('Высота (мм)', fontsize=12)
        
        # Добавляем легенду
        ax.text(0.02, 0.98, f'Деталей: {len(sheet.placed_parts)}',
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
            print(f"Изображение сохранено: {output_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def visualize_all_sheets(self, sheets: List[Sheet], output_dir: str = 'output',
                            show: bool = False):
        """
        Визуализирует все листы раскроя
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for sheet in sheets:
            output_path = os.path.join(output_dir, f'sheet_{sheet.id:03d}.png')
            self.visualize_sheet(sheet, output_path=output_path, show=show)
        
        # Создаём сводную визуализацию
        self.create_summary_visualization(sheets, 
                                         os.path.join(output_dir, 'summary.png'),
                                         show=show)
    
    def create_summary_visualization(self, sheets: List[Sheet], 
                                    output_path: str, show: bool = False):
        """
        Создаёт сводную визуализацию всех листов
        """
        n_sheets = len(sheets)
        if n_sheets == 0:
            return
        
        # Определяем компоновку подграфиков
        cols = min(3, n_sheets)
        rows = (n_sheets + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows), 
                                dpi=self.dpi)
        
        # Преобразуем axes в список для удобной обработки
        if n_sheets == 1:
            axes_list = [[axes]]
        elif n_sheets <= cols:
            axes_list = [axes] if hasattr(axes, '__len__') else [[axes]]
            if not isinstance(axes_list[0], (list, np.ndarray)):
                axes_list = [[axes_list[0]]]
        else:
            axes_list = axes
        
        total_utilization = 0
        
        for idx, sheet in enumerate(sheets):
            row = idx // cols
            col = idx % cols
            
            # Получаем правильный ax в зависимости от структуры
            if n_sheets == 1:
                ax = axes
            elif rows == 1:
                ax = axes[col]
            else:
                ax = axes[row, col]
            
            # Рисуем лист
            ax.add_patch(Rectangle((0, 0), sheet.width, sheet.height,
                                  linewidth=2, edgecolor='black',
                                  facecolor='lightgray', alpha=0.3))
            
            # Рисуем детали
            for part in sheet.placed_parts:
                color = self._get_color(part.part_id)
                rect = Rectangle((part.x, part.y), part.width, part.height,
                               linewidth=1, edgecolor='black',
                               facecolor=color, alpha=0.7)
                ax.add_patch(rect)
            
            ax.set_xlim(0, sheet.width)
            ax.set_ylim(0, sheet.height)
            ax.set_aspect('equal')
            ax.set_title(f'Лист #{sheet.id}\n{sheet.get_utilization():.1f}%',
                        fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.3)
            
            total_utilization += sheet.get_utilization()
        
        # Скрываем пустые подграфики
        for idx in range(n_sheets, rows * cols):
            row = idx // cols
            col = idx % cols
            if rows > 1:
                axes[row, col].axis('off')
            else:
                axes[col].axis('off')
        
        avg_utilization = total_utilization / n_sheets if n_sheets > 0 else 0
        fig.suptitle(f'Сводная карта раскроя | Листов: {n_sheets} | '
                    f'Среднее использование: {avg_utilization:.1f}%',
                    fontsize=14, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"Сводное изображение сохранено: {output_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
