import sys
from typing import Callable, Tuple
#from time import sleep
from collections import deque

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    )

from PyQt6.QtCore import (
    Qt,
    QPointF,
    pyqtSignal,
    QProcess,
    QTimer,
)

from PyQt6.QtCharts import (
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
)

from PyQt6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
)


class ScriptRunner(QProcess):
    
    heartbeatSignal = pyqtSignal(float, float)

    def __init__(self,
                 cmd: str,
                 options: list[str],
                 logToFile = False,
                 parent = None):
        
        super().__init__(parent)
        self.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.cmd = cmd
        self.options: list[str]  = options
        self.logToFile: bool = logToFile

        self.sleepTime: float = 1 / 130
        self.timeSinceStart: float = 0.0

        self.dataQueue: deque = deque()

        self.timer = QTimer(self)
        self.timer.setInterval(
            int(self.sleepTime * 1_000)
        )
        self.timer.timeout.connect(
            self._processQueuePoint
        )


        if logToFile:
            self.setProcessChannelMode(
                QProcess
                .ProcessChannelMode
                .MergedChannels
            )

    def startScript(self,
                    callback: Callable):
        print("[ScriptRunner]: Starting Script...")
        
        (
            self.readyReadStandardOutput
            .connect(callback)
        )
        
        self.start(self.cmd,
                   self.options)
        self.timer.start()

    def getStdOut(self):
        rawData = (
            self.readAllStandardOutput()
            .data()
            .decode(errors="replace")
        )

        for line in rawData.splitlines():
            line = line.strip()

            if not line:
                continue
            
            for value in self.batchToTuple(line):
                self.dataQueue.append(float(value))
                #self.heartbeatSignal.emit(self.timeSinceStart, float(value))
                #print(f"({self.timeSinceStart} / {value})")
                #self.timeSinceStart += self.sleepTime

    def _processQueuePoint(self):
        if self.dataQueue:
            self.heartbeatSignal.emit(
                self.timeSinceStart, self.dataQueue.popleft()
            )
            self.timeSinceStart += self.sleepTime

    def printStdOut(self):
        rawOutput = (
            self.readAllStandardOutput()
            .data()
            .decode(errors="replace")
        )
        
        if self.logToFile:
            if rawOutput:
                with open(
                        "polarGraphDesktop.log",
                        "a",
                        newline="\n"
                ) as logFile:
                    logFile.write(rawOutput)
        else:
            for line in rawOutput.splitlines():
                if line:
                    print(self.batchToTuple(line))
        
    def cleanUp(self):
        print("[ScriptRunner]: Terminating Script...")
        self.isRunning = False

        self.timer.stop()
        self.terminate()
        
        if not self.waitForFinished(3000):
            
            print("[ScriptRunner]: Force killing script...")
            self.kill()

    def batchToTuple(self, batch: str) -> Tuple[int, ...]:
        return tuple(
            int(valStr) for valStr in batch.split(" ") if valStr.strip()
        )


class GraphView(QMainWindow):
    minY: float = -200.0
    maxY: float = 1000.0
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(800, 600)
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.setWindowTitle("Polar Live ECG")

        self._initChart()
        self._initLayout()
        
        
    def _initChart(self):
        axisX = QValueAxis()
        axisY = QValueAxis()
        
        gridPen = QPen(QColor("#00a6ff"), 1, Qt.PenStyle.DashLine)
        axisPen = QPen(QColor("#00a6ff"), 2, Qt.PenStyle.NoPen)

        for axis in (axisX, axisY):
            axis.setGridLinePen(gridPen)
            axis.setLinePen(axisPen)
            axis.setLabelsVisible(False)
            
        self.lineSeries = QLineSeries()
        linePen = QPen(QColor("#3fb950"), 2, Qt.PenStyle.SolidLine)
        self.lineSeries.setPen(linePen)
        
        chart = QChart()
        chart.addSeries(self.lineSeries)
        chart.addAxis(axisX, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axisY, Qt.AlignmentFlag.AlignLeft)
        
        self.lineSeries.attachAxis(axisX)
        self.lineSeries.attachAxis(axisY)
        
        axisX.setRange(0, 3.0)
        axisY.setRange(-250, 1200)
        
        chart.legend().hide()
        chart.setBackgroundBrush(QBrush(QColor("#002941")))
        chart.setBackgroundRoundness(0)
        chart.layout().setContentsMargins(0,0,0,0)

        self.chartView = QChartView()
        self.chartView.setChart(chart)
        self.chartView.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # self.chartView.rotate(90.0)

        
        
    def _initLayout(self):
        self.verticalBoxLayout = QVBoxLayout()
        self.centralWidget.setLayout(self.verticalBoxLayout)
        self.verticalBoxLayout.addWidget(self.chartView)
        self.verticalBoxLayout.setContentsMargins(0, 0, 0, 0)
        
        
    def updateChart(self, x: float, y: float):
        self.lineSeries.append(QPointF(x, y))

        if y > self.maxY or y < self.minY:
            self.minY = min(y, self.minY)
            self.maxY = max(y, self.maxY)
            self.chartView.chart().axes()[1].setRange(self.minY - 100, self.maxY + 100)
        
        windowSize = 2.0
        if x > windowSize:
            self.chartView.chart().axes()[0].setRange(x - windowSize, x)
        else:
            self.chartView.chart().axes()[0].setRange(0, windowSize)

        if self.lineSeries.count() > 1_000:
            self.lineSeries.remove(0)


        
if __name__ == "__main__":
    application = QApplication([])

    runner = ScriptRunner(
        "stdbuf",
        ["-oL", "./polarBatch.sh"],
        logToFile=False,
        parent=application
    )
    
    graphView = GraphView()

    
    runner.heartbeatSignal.connect(graphView.updateChart)
    application.aboutToQuit.connect(runner.cleanUp)
    
    graphView.show()
    runner.startScript(runner.getStdOut)
    
    sys.exit(application.exec())
