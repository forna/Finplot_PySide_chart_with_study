import sys
import yfinance
import datetime as dt
from PySide6.QtWidgets import QWidget, QMainWindow, QApplication, QTabWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtWidgets import QTableView, QHeaderView, QGridLayout, QSizePolicy, QSpacerItem, QLabel
from PySide6.QtCore import QSortFilterProxyModel, QAbstractTableModel, QSize
from PySide6.QtGui import Qt, QFont
import finplot as fplt
import talib.abstract as talib


class TickerListWidget(QWidget):
    def __init__(self, parent, header_list, ticker_list):
        super(TickerListWidget, self).__init__(parent)
        self.parent = parent

        # Creating a QTableView
        self.table_view = QTableView()

        # Getting the Model
        source_model = CustomTableModel(header_list, ticker_list)

        # Enable sorting
        proxy_model = QSortFilterProxyModel(self)
        proxy_model.setSourceModel(source_model)
        self.table_view.setModel(proxy_model)
        self.table_view.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        self.table_view.setSortingEnabled(True)

        # Connect the 'clicked' signal
        self.table_view.clicked.connect(self.clicked_ticker)

        # QTableView Headers
        self.horizontal_header = self.table_view.horizontalHeader()
        self.vertical_header = self.table_view.verticalHeader()
        self.horizontal_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.vertical_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        font = QFont()
        font.setBold(True)
        self.horizontal_header.setFont(font)

        # Set the Tableview Size
        self.table_view.setMinimumSize(QSize(60, 500))
        self.table_view.setMaximumSize(QSize(60, 16777215))

        # QWidget Layout
        self.main_layout = QGridLayout()
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Left layout
        self.table_view.setSizePolicy(size)
        self.main_layout.addWidget(self.table_view)

        # Set the layout to the QWidget
        self.setLayout(self.main_layout)

    def clicked_ticker(self):
        index = {index for index in self.table_view.selectionModel().selectedIndexes()}.pop()
        row = index.row()
        ticker = self.table_view.model().index(row, 0).data()
        self.parent.clicked_ticker_list_widget(ticker)


class CustomTableModel(QAbstractTableModel):
    def __init__(self, header_list, ticker_list, *args):
        QAbstractTableModel.__init__(self, *args)
        self.header = header_list
        self.table_data = ticker_list

    def rowCount(self, parent):
        return len(self.table_data)

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        # Display the values in the cells
        if role == Qt.DisplayRole:
            return self.table_data[index.row()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]


class FinplotWidget(QWidget):
    def __init__(self, parent, symbol, df):
        super(FinplotWidget, self).__init__(parent)
        self.parent = parent

        # Finplot settings
        fplt.display_timezone = dt.timezone.utc
        fplt.poc_color = "#fff"
        fplt.background = "#000"  # Set the background color to black
        fplt.odd_plot_background = "#000"
        fplt.foreground = "#fff"
        fplt.cross_hair_color = "#fff"
        fplt.draw_line_color = "#fff"
        fplt.side_margin = 1
        fplt.clamp_grid = False
        fplt.right_margin_candles = 2

        # Layout and labels
        self.labels = QHBoxLayout()
        self.labels.spacer = QSpacerItem(10, 0)
        self.labels.addStretch(1)
        self.labels.symbol = QLabel()
        self.labels.addWidget(self.labels.symbol)

        # Add the chart
        self.layout = QVBoxLayout(self)
        self.fplt_main, self.fplt_study = fplt.create_plot_widget(self.window(), rows=2)

        # y axis
        self.ax_left = self.fplt_main.getAxis("left")
        self.ax_left.setPen(style=Qt.DotLine)

        # Show the grid
        self.fplt_main.set_visible(xgrid=True, ygrid=True)
        self.layout.addLayout(self.labels)
        self.layout.addWidget(self.fplt_main.ax_widget)
        self.layout.addWidget(self.fplt_study.ax_widget)
        self.window().axs = self.fplt_main, self.fplt_study  # required property of window
        self.setLayout(self.layout)
        self.load_df(symbol, df)

    def load_df(self, symbol, df):
        self.fplt_main.reset()
        self.fplt_study.reset()
        if len(df.index) != 0:  # Ensure there is data in the dataframe
            # Main
            df.columns = df.columns.str.lower()
            df_cols_list = ["open", "close", "high", "low", "volume"]
            candlesticks = fplt.candlestick_ochl(df[df_cols_list], ax=self.fplt_main)
            candlesticks.colors.update(dict(bull_body="#00AA00", bull_shadow="#fff", bull_frame="#00AA00",
                                            bear_body="#D20000", bear_shadow="#fff", bear_frame="#D20000"))
            candlesticks.x_offset = 0.5

            # Studies
            study_name = "MFI"
            talib_function = talib.Function(study_name)
            study_df = talib_function(df[df_cols_list])
            fplt.plot(study_df, legend=study_name, color="#FFFF66", ax=self.fplt_study)

            fplt.refresh()
        self.labels.symbol.setText(f"<B>{symbol}</B>")  # set the symbol


class ComboStockChartWidget(QWidget):
    def __init__(self, parent, header_list, ticker_list, df_dict, initial_symbol):
        super(ComboStockChartWidget, self).__init__(parent)
        self.df_dict = df_dict
        self.ticker_list_widget = TickerListWidget(self, header_list, ticker_list)
        df = df_dict[initial_symbol]
        self.finplot_widget = FinplotWidget(self, initial_symbol, df)
        self.hBox = QHBoxLayout()
        self.hBox.addWidget(self.ticker_list_widget)
        self.hBox.addWidget(self.finplot_widget)
        self.setLayout(self.hBox)

    def clicked_ticker_list_widget(self, symbol):
        df = self.df_dict[symbol]
        self.finplot_widget.load_df(symbol, df)


def instantiate_combo_chart_widget(df_dict):
    ticker_list_header_list = ["Symbol"]
    ticker_list = list(df_dict.keys())
    initial_symbol = list(df_dict.keys())[0]  # Take the first item in the dictionary to display it
    return ComboStockChartWidget(None, ticker_list_header_list, ticker_list, df_dict, initial_symbol)


class MainWindow(QMainWindow):
    def __init__(self, parent, df_dict):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Stocks")

        self.tab_widget = QTabWidget()
        self.tab_widget.setMovable(True)
        self.setCentralWidget(self.tab_widget)

        # Stock Chart
        combo_stock_chart_widget = instantiate_combo_chart_widget(df_dict)
        self.tab1 = combo_stock_chart_widget
        self.tab_widget.addTab(self.tab1, "Stock Chart")


def main():
    df_dict = {}
    symbols_list = ["AAPL", "GOOGL", "FB"]
    period = "180d"
    for symbol in symbols_list:
        df_dict[symbol] = yfinance.download(symbol, period=period)
    app = QApplication(sys.argv)
    main_window = MainWindow(None, df_dict)
    main_window.showMaximized()
    ret = app.exec()
    sys.exit(ret)


if __name__ == '__main__':
    main()
