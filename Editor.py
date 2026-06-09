import sys
import json

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QFileDialog,
    QToolBar
)

LANE_COUNT = 6
CELL_WIDTH = 80
CELL_HEIGHT = 20

TOTAL_MEASURES = 69
SUBDIVISION = 128  # 4/4 + 32분할 기준


class NoteItem(QGraphicsRectItem):
    def __init__(self, lane, measure, step):
        x = lane * CELL_WIDTH
        y = (measure - 1) * SUBDIVISION * CELL_HEIGHT + step * CELL_HEIGHT

        super().__init__(x, y, CELL_WIDTH, CELL_HEIGHT)

        self.lane = lane
        self.measure = measure
        self.step = step

        self.setBrush(QBrush(QColor(50, 150, 255)))
        self.setPen(QPen(Qt.GlobalColor.black))


class ChartEditor(QGraphicsView):
    def __init__(self):
        self.scene = QGraphicsScene()
        super().__init__(self.scene)

        self.notes = {}

        self.draw_grid()

    def draw_grid(self):
        total_height = TOTAL_MEASURES * SUBDIVISION * CELL_HEIGHT

        # 레인선
        for lane in range(LANE_COUNT + 1):
            x = lane * CELL_WIDTH
            self.scene.addLine(x, 0, x, total_height)

        # 마디선
        for measure in range(TOTAL_MEASURES + 1):
            y = measure * SUBDIVISION * CELL_HEIGHT

            line = self.scene.addLine(
                0,
                y,
                LANE_COUNT * CELL_WIDTH,
                y,
                QPen(QColor(255, 0, 0), 2)
            )

        # 세부 격자
        for measure in range(TOTAL_MEASURES):
            base_y = measure * SUBDIVISION * CELL_HEIGHT

            for step in range(SUBDIVISION):
                y = base_y + step * CELL_HEIGHT

                self.scene.addLine(
                    0,
                    y,
                    LANE_COUNT * CELL_WIDTH,
                    y,
                    QPen(QColor(220, 220, 220))
                )

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())

        lane = int(pos.x() // CELL_WIDTH)

        if lane < 0 or lane >= LANE_COUNT:
            return

        global_step = int(pos.y() // CELL_HEIGHT)

        measure = global_step // SUBDIVISION + 1
        step = global_step % SUBDIVISION

        key = (measure, step, lane)

        if event.button() == Qt.MouseButton.LeftButton:

            if key not in self.notes:
                note = NoteItem(lane, measure, step)

                self.scene.addItem(note)
                self.notes[key] = note

        elif event.button() == Qt.MouseButton.RightButton:

            if key in self.notes:
                self.scene.removeItem(self.notes[key])
                del self.notes[key]

        super().mousePressEvent(event)

    def save_chart(self, path):
        chart = {}

        for measure, step, lane in self.notes.keys():

            key = (measure, step)

            if key not in chart:
                chart[key] = []

            chart[key].append(lane)

        result = []

        for (measure, step), lanes in sorted(chart.items()):
            result.append({
                "m": measure,
                "s": step,
                "lane": sorted(lanes)
            })

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    def load_chart(self, path):

        for note in list(self.notes.values()):
            self.scene.removeItem(note)

        self.notes.clear()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:

            measure = entry["m"]
            step = entry["s"]

            for lane in entry["lane"]:

                note = NoteItem(
                    lane,
                    measure,
                    step
                )

                self.scene.addItem(note)

                self.notes[(measure, step, lane)] = note


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rhythm Chart Editor")

        self.editor = ChartEditor()

        self.setCentralWidget(self.editor)

        toolbar = QToolBar()

        self.addToolBar(toolbar)

        save_action = toolbar.addAction("Save")
        load_action = toolbar.addAction("Load")

        save_action.triggered.connect(self.save_file)
        load_action.triggered.connect(self.load_file)

    def save_file(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save",
            "",
            "JSON (*.json)"
        )

        if path:
            self.editor.save_chart(path)

    def load_file(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load",
            "",
            "JSON (*.json)"
        )

        if path:
            self.editor.load_chart(path)


app = QApplication(sys.argv)

window = MainWindow()
window.resize(900, 700)
window.show()

sys.exit(app.exec())