"""
memo to myself: add untrust, unpair to shell skript
"""
import sys
from math import inf
from typing import Callable, Tuple, Literal
from collections import deque
from dataclasses import dataclass

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
    QScatterSeries,
    QValueAxis,
    QAbstractAxis,
    QAbstractSeries,
)

from PyQt6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
)



@dataclass
class StreamConfig:
    
    sampleRateInHz: int = 130
    peak_threshold: float = 500.0
    refractoryTimeInS: float = 0.25

    @property
    def delayInSeconds(self) -> float:
        return 1.0 / self.sampleRateInHz

    @property
    def delayInMilliseconds(self) -> int:
        return int(
            self.delayInSeconds * 1_000
        )

    @property
    def delayInNanoseconds(self) -> int:
        return int(
            self.delayInSeconds * 1_000_000_000
        )

class DataTimer(QTimer):
    def __init__(
            self,
            config: StreamConfig
    ) -> None:
        super().__init__()
        self.config = config
        self.setTimerType(
            Qt.TimerType.PreciseTimer
        )
       
        # Plot is faster than data:
        # 1/130 = 7.6... -> 7ms
        self.setInterval(
            config.delayInMilliseconds
        )
        self.timeSinceStartInNanoseconds: int = 0

    def updateTimeSinceStartInNanoseconds(self) -> None:
        self.timeSinceStartInNanoseconds += self.config.delayInNanoseconds

    def timeSinceStartInSeconds(self) -> float:
        return self.timeSinceStartInNanoseconds / 1_000_000_000.0


class HRV():
    bufferLength: int = 3
    
    def __init__(self, timer: DataTimer) -> None:
        self.timer = timer
        self.previousPeakTimeInNanoseconds: float = 0.0
        self.latestHRV: float = 0.0
        self.buffer: deque = deque(maxlen = self.bufferLength)
        self.runningMean: float = 0.0

    def update(self) -> None:
        self.latestHRV = (
            self.timer.timeSinceStartInNanoseconds
            - self.previousPeakTimeInNanoseconds
        )
        
        # update running mean
        self.buffer.append(self.latestHRV)
        self.runningMean = sum(self.buffer) / len(self.buffer)
        
        self.previousPeakTimeInNanoseconds = self.timer.timeSinceStartInNanoseconds



class ScriptRunner(QProcess):
    heartbeatSignal = pyqtSignal(float, float)

    def __init__(
            self,
            cmd: str,
            options: list[str],
            timer: QTimer,
            logToFile = False,
            parent = None
    ) -> None:
        
        super().__init__(parent)
        self.setProcessChannelMode(
            QProcess
            .ProcessChannelMode
            .SeparateChannels
        )
        self.cmd = cmd
        self.options: list[str]  = options
        self.logToFile: bool = logToFile
        self.timer: DataTimer = timer
        
        self.dataQueue: deque = deque()
        
        self.setupTimer()

        if logToFile:
            self.setProcessChannelMode(
                QProcess
                .ProcessChannelMode
                .MergedChannels
            )

            
    def setupTimer(self) -> None:
        self.timer.timeout.connect(
            self._processQueuePoint
        )

        
    def startScript(self,
                    callback: Callable
                    ) -> None:
        print("[ScriptRunner]: Starting Script...")
        
        (
            self.readyReadStandardOutput
            .connect(callback)
        )
        
        self.start(
            self.cmd,
            self.options
        )
        self.timer.start()

        
    def getStdOut(self):
        print("[ScriptRunner]: Processing StdOut...")
        
        rawData = (
            self.readAllStandardOutput()
            .data()
            .decode(errors="replace")
        )

        for line in rawData.splitlines():
            line = line.strip()

            if not line:
                continue
            
            # print("[ScriptRunner]: Updating Queue...")                
            for value in self.batchToTuple(line):
                (
                self.dataQueue
                .append(float(value))
                )


    def _processQueuePoint(self):
        if self.dataQueue:
            self.heartbeatSignal.emit(
                self.timer.timeSinceStartInSeconds(),
                self.dataQueue.popleft()
            )
            self.timer.updateTimeSinceStartInNanoseconds()


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
            int(valStr)
            for valStr in batch.split(" ")
            if valStr.strip()
        )


@dataclass
class ChartAxis:
    object: QAbstractAxis
    alignment: Qt.AlignmentFlag

@dataclass
class ChartSeries:
    object: QAbstractSeries
    xAxis: ChartAxis
    yAxis: ChartAxis


class GraphView(QMainWindow):
    minY: float = -200.0
    maxY: float = 1_000.0
    maxBufferSize: int = 1_000

    gridPen = QPen(
        QColor("#00a6ff"),
        1,
        Qt.PenStyle.DashLine
    )
        
    # axisPen = QPen(
    #     QColor("#00a6ff"),
    #     1,
    #     Qt.PenStyle.NoPen
    # )

    noPen = QPen(Qt.PenStyle.NoPen)
    backgroundBrush = QBrush(QColor("#002941"))
    peakBrush = QBrush(QColor("#d29922"))
    lineSeriesPen = QPen(
                QColor("#3fb950"),
                2,
                Qt.PenStyle.SolidLine
            )
    hrvSeriesPen = QPen(
        QColor("#00ffff"),
        2,
        Qt.PenStyle.SolidLine
    )
    possibleSeries: Literal = ["line", "scatter"]
    
    def __init__(self, config: StreamConfig, hrv: HRV) -> None:
        super().__init__()
        self.config = config
        self.hrv = hrv
        self.setFixedSize(1600, 600)
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.setWindowTitle("Polar Live ECG")

        self._initChart()
        self._initLayout()

        self.latestPeak: Tuple[float, float] = (0.0, 0.0)
        self.isPeak: Callable = self._findPeakFactory(
            threshold = self.config.peak_threshold,
            refractoryTime = self.config.refractoryTimeInS
        )

    def _axisFactory(self,
                     gridPen: QPen,
                     linePen: QPen,
                     axisRange: Tuple[int, int],
                     showLabels: bool = False
                     ) -> QValueAxis:
        
        axis = QValueAxis()
        
        axis.setGridLinePen(gridPen)
        axis.setLinePen(linePen)

        if gridPen is self.noPen:
            axis.setGridLineVisible(False)
        else:
            axis.setGridLineVisible(True)
            
        axis.setMinorGridLineVisible(False)

        if showLabels:
            axis.setLabelsVisible(True)
        else:
            axis.setLabelsVisible(False)
        
        axis.setRange(axisRange[0], axisRange[1])

        return axis

    def _seriesFactory(
            self,
            seriesType: possibleSeries,
            pen: QPen,
            brush: QBrush = peakBrush,
            markerSize: float = 10.0
    ) -> QLineSeries | QScatterSeries:
        
        if seriesType == "line":
            series = QLineSeries()
        if seriesType == "scatter":
            series = QScatterSeries()
            series.setBrush(brush)
            series.setMarkerSize(markerSize)
        
        series.setPen(pen)
        
        return series
        
    def _initChart(self):
        self.axes = {
            "xTimeInSeconds": ChartAxis(
                self._axisFactory(self.gridPen, self.noPen, (0, 3.0)),
                Qt.AlignmentFlag.AlignBottom
            ),
            "yVoltage": ChartAxis(
                self._axisFactory(self.gridPen, self.noPen, (-250, 1_200)),
                Qt.AlignmentFlag.AlignLeft
            ),
            "yTimeInMilliseconds": ChartAxis(
                self._axisFactory(self.noPen, self.noPen, (600, 1_000)),
                Qt.AlignmentFlag.AlignRight
            )
        }

        self.series = {
            "lineSeries": ChartSeries(
                self._seriesFactory("line", self.lineSeriesPen),
                self.axes["xTimeInSeconds"],
                self.axes["yVoltage"]
            ),
            "peakSeries": ChartSeries(
                self._seriesFactory("scatter", self.noPen),
                self.axes["xTimeInSeconds"],
                self.axes["yVoltage"]
            ),
            "hrvSeries": ChartSeries(
                self._seriesFactory("line", self.hrvSeriesPen),
                self.axes["xTimeInSeconds"],
                self.axes["yTimeInMilliseconds"]
            )
        }

        chart = QChart()

        for s in self.series.values():
            chart.addSeries(s.object)
        
        for ax in self.axes.values():
            chart.addAxis(ax.object, ax.alignment)

        for s in self.series.values():
            s.object.attachAxis(s.xAxis.object)
            s.object.attachAxis(s.yAxis.object)

        chart.legend().hide()
        chart.setBackgroundBrush(
            self.backgroundBrush
        )
        chart.setBackgroundRoundness(0)
        chart.layout().setContentsMargins(0, 0, 0, 0)

        self.chartView = QChartView()
        self.chartView.setChart(chart)
        self.chartView.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        
        
    def _initLayout(self):
        self.verticalBoxLayout = QVBoxLayout()
        self.centralWidget.setLayout(self.verticalBoxLayout)
        self.verticalBoxLayout.addWidget(self.chartView)
        self.verticalBoxLayout.setContentsMargins(0, 0, 0, 0)

    def _findPeakFactory(
            self,
            threshold: float = 500.0,
            refractoryTime: float = 0.25
    ) -> Callable[[float, float], Tuple[float, float]]:
        candidate: Tuple[float, float] = (0.0, -inf)
        lastValue: Tuple[float, float] = (0.0, 0.0)
        isPeak: bool = False

        def __detectPeak(x, y):
            nonlocal candidate, lastValue, isPeak

            isPeak = False
            
            if y < threshold:
                if lastValue[1] >= threshold:
                    if x > self.latestPeak[0] + refractoryTime:
                        if candidate[1] != -inf:
                            self.latestPeak = candidate
                            isPeak = True
                        candidate = (0.0, -inf)
                        

            if y >= threshold:
                if y >= candidate[1]:
                    candidate = (x, y)
                    
            lastValue = (x, y)

            return isPeak
            
        return __detectPeak


        
        
    def updateChart(self, x: float, y: float):
        # add data points
        self.series["lineSeries"].object.append(QPointF(x, y))

        # add peaks
        if self.isPeak(x, y):
            self.series["peakSeries"].object.append(
                QPointF(
                    self.latestPeak[0],
                    self.latestPeak[1]
                )
            )
            self.hrv.update()
            # print(f"[HRV]: {self.hrv.latestHRV}")


        hrvInMs = self.hrv.latestHRV / 1_000_000.0

        runningMean = self.hrv.runningMean
        
        self.series["hrvSeries"].object.append(QPointF(x, hrvInMs))

        # dynamically adjust y ranges
        if y > self.maxY or y < self.minY:
            self.minY = min(y, self.minY)
            self.maxY = max(y, self.maxY)

            self.axes["yVoltage"].object.setRange(
                self.minY - 100,
                self.maxY + 100
            )


        # dynamically adjust x ranges
        windowSize = 7.0
        if x > windowSize:
            self.axes["xTimeInSeconds"].object.setRange(x - windowSize, x)
        else:
            self.axes["xTimeInSeconds"].object.setRange(0, windowSize)

            
        # keeping buffer length
        if self.series["lineSeries"].object.count() > 1_000:
            self.series["lineSeries"].object.remove(0)
            
        if self.series["peakSeries"].object.count() > 1_000:
            self.series["peakSeries"].object.remove(0)
            
        if self.series["hrvSeries"].object.count() > 1_000:
            self.series["hrvSeries"].object.remove(0)



        
if __name__ == "__main__":
    application = QApplication([])

    config = StreamConfig()
    timer = DataTimer(config)
    hrv = HRV(timer)
    
    runner = ScriptRunner(
        "stdbuf",
        ["-oL", "./polarBatch.sh"],
        timer,
        logToFile=False,
        parent=application
    )
    
    graphView = GraphView(config, hrv)
    
    runner.heartbeatSignal.connect(
        graphView.updateChart
    )

    application.aboutToQuit.connect(
        runner.cleanUp
    )
    
    graphView.show()

    runner.startScript(
        runner.getStdOut
    )
    
    sys.exit(application.exec())

