import sys
from PyQt5.QtWidgets import QColorDialog, QAbstractItemView, QApplication, QMainWindow, QAction, QMenu, QMessageBox, QToolBar, QStatusBar, QWidget, QVBoxLayout, QLabel, QStackedWidget, QPushButton, QLineEdit, QDateEdit, QHBoxLayout, QFormLayout, QCalendarWidget, QTableView, QTextEdit, QTimeEdit, QDialog, QDialogButtonBox, QDesktopWidget
from PyQt5.QtGui import QIcon, QPainter, QColor, QTextCharFormat, QStandardItemModel, QStandardItem, QBrush, QPen, QPixmap, QFont
from PyQt5.QtCore import QDate, Qt, QEvent, QTime, pyqtSignal, QRect, QVariant, QSize
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
import os

class EventManager:
    def __init__(self, db_filename="events.db"):
        self.db_filename = db_filename
        self.db = None
        self.connection_name = f"event_db_conn_{id(self)}"
        self.connectToDatabase()

    def connectToDatabase(self):
        self.db = QSqlDatabase.database(self.connection_name, open=False)
        if self.db.isValid():
            print(f"EventManager: Reusing existing database connection '{self.connection_name}'.")
            if not self.db.isOpen():
                if not self.db.open():
                    print(f"EventManager: Failed to re-open existing connection: {self.db.lastError().text()}")
                    return False
            self.createTable()
            return True

        # If no existing valid connection, add a new one with a specific name
        self.db = QSqlDatabase.addDatabase("QSQLITE", self.connection_name)
        self.db.setDatabaseName(self.db_filename)


        if not self.db.open():
            QMessageBox.critical(None, "Database Connection Error", f"Failed to open database: {self.db.lastError().text()}")
            self.db = None
            return False

        print(f"EventManager: Database connection opened for {self.db_filename} (Name: '{self.connection_name}')")
        self.createTable()
        return True

    def createTable(self):
        if self.db and self.db.isOpen():
            query = QSqlQuery(self.db)
            query.exec_('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    event_time TEXT,
                    event_color TEXT
                )
            ''')
            if query.lastError().isValid():
                print(f"EventManager: Error creating table: {query.lastError().text()}")
            else:
                print("EventManager: Table 'events' checked/created.")
        else:
            print("EventManager: Database not connected. Cannot create table")
    
    def addEvent(self, eventDate, eventTitle, eventDescription, eventTime, eventColor):
        if self.db and self.db.isOpen():
            query = QSqlQuery(self.db)
            query.prepare('''
                INSERT INTO events (event_date, title, description, event_time, event_color)
                VALUES (:event_date, :title, :description, :event_time, :event_color)
            ''')
            query.bindValue(":event_date", eventDate)
            query.bindValue(":title", eventTitle)
            query.bindValue(":description", eventDescription)
            query.bindValue(":event_time", eventTime)
            query.bindValue(":event_color", eventColor)

            if not query.exec_():
                print(f"EventManager: Error adding event: {query.lastError().text()}")
            else:
                print(f"EventManager: Event added for {eventDate}: {eventTitle}")
                return True #success
        return False #failure
    
    def updateEvent(self, edited_event_data):
        if self.db and self.db.isOpen():
            query = QSqlQuery(self.db)
            query.prepare('''
                UPDATE events
                SET
                    event_date = :event_date,
                    title = :title,
                    description = :description,
                    event_time = :event_time,
                    event_color = :event_color
                WHERE id = :event_id
            ''')

            val_event_date = edited_event_data.get("event_date")
            print(f"Binding :event_date -> Value: {val_event_date}, Type: {type(val_event_date)}")
            query.bindValue(":event_date", edited_event_data["event_date"])

            val_title = edited_event_data.get("title")
            print(f"Binding :title -> Value: '{val_title}', Type: {type(val_title)}")
            query.bindValue(":title", edited_event_data["title"])

            val_description = edited_event_data.get("description")
            print(f"Binding :description -> Value: '{val_description}', Type: {type(val_description)}")
            query.bindValue(":description", edited_event_data["description"])

            val_event_time = edited_event_data.get("event_time")
            print(f"Binding :event_time -> Value: {val_event_time}, Type: {type(val_event_time)}")
            query.bindValue(":event_time", edited_event_data["event_time"])

            val_event_color = edited_event_data.get("event_color")
            print(f"Binding :event_color -> Value: '{val_event_color}', Type: {type(val_event_color)}")
            query.bindValue(":event_color", edited_event_data["event_color"])

            val_event_id = edited_event_data.get("event_id")
            print(f"Binding :event_id -> Value: {val_event_id}, Type: {type(val_event_id)}")
            query.bindValue(":event_id", edited_event_data["event_id"])

            if not query.exec_():
                print(f"EventManager: Error Updating event: {query.lastError().text()}")
                print(f"Prepared Query: {query.lastQuery()}")
                print(edited_event_data)
            else:
                print(f"EventManager: Event Updated for {edited_event_data["event_id"]}: {edited_event_data["event_date"]}: {edited_event_data["title"]}")
                return True #success
        return False #failure


    def getEventsForDate(self, date:QDate):
        if not self.db or not self.db.isOpen(): return []
        query = QSqlQuery(self.db)
        query.prepare("SELECT title, description, event_time, event_color FROM events WHERE event_date = :date")
        date_string_for_query = date.toString(Qt.ISODate)
        query.bindValue(":date", QVariant(date_string_for_query))
        events = []
        if query.exec_():
            while query.next():
                events.append({
                    'title': query.value(0),
                    'description': query.value(1),
                    'time': query.value(2),
                    'color':query.value(3)
                })
        else:
            print(f"EventManager: Error getting events for date: {query.lastError().text()}")
        return events
    
    def getAllEvents(self):
        if not self.db or not self.db.isOpen(): return []
        query = QSqlQuery(self.db)
        query.prepare("SELECT id, event_date, title, description, event_time, event_color FROM events")
        events = []
        if query.exec_():
            while query.next():
                event_date_raw = query.value(1)
                q_date = QDate()
                if isinstance(event_date_raw, str):
                    q_date = QDate.fromString(event_date_raw, "yyyy-MM-dd")

                events.append({
                    'id': query.value(0),
                    'event_date': q_date,
                    'title': query.value(2),
                    'description': query.value(3),
                    'event_time': query.value(4),
                    'event_color': query.value(5)
                })
        else:
            print(f"EventManager: Error getting all events: {query.lastError().text()}")
        return events
    
    def getAllEventDates(self):
        all_events = self.getAllEvents()
        all_event_dates = []
        for event in all_events:
            if 'event_date' in event and isinstance(event['event_date'], QDate):
                all_event_dates.append(event['event_date'])
        return all_event_dates
    
    def getEventDetailsbyId(self, id):
        if not self.db or not self.db.isOpen(): return []
        query = QSqlQuery(self.db)
        query.prepare(f"SELECT id, event_date, title, description, event_time, event_color FROM events WHERE id = {id}")
        id_specific_event_details = []
        if query.exec_():
            while query.next():
                id_specific_event_details.append({
                    'id': query.value(0),
                    'event_date': query.value(1),
                    'title': query.value(2),
                    'description': query.value(3),
                    'event_time': query.value(4),
                    'event_color': query.value(5)
                })
        else:
            print("The query did not execute!")
        return id_specific_event_details
    
    def deleteEvent(self, eventId):
        if not self.db or not self.db.isOpen(): return []
        query = QSqlQuery(self.db)
        query.prepare(f"DELETE FROM events WHERE id = {eventId}")
        if not query.exec_():
            print(f"EventManager: Error deleting event with ID {eventId}: {query.lastError().text()}")
            return False
        else:
            print(f"EventManager: Event with ID {eventId} deleted.")
            return True

    def closeConnection(self):
        if self.db and self.db.isOpen():
            self.db.close()
            print("EventManager: Database connection closed.")

        if QSqlDatabase.contains(self.connection_name):
            QSqlDatabase.removeDatabase(self.connection_name)
            print(f"EventManager: Connection '{self.connection_name}' removed from pool.")


class EventViewerPage(QWidget):
    def __init__(self, event_manager):
        super().__init__()
        layout = QVBoxLayout()
        headerLabel = QLabel("Event List")
        headerLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(headerLabel)

        self.event_manager = event_manager
        if not (self.event_manager.db and self.event_manager.db.isOpen()):
            QMessageBox.critical(self, "Application Error", "Database connection failed to open via EventManager.")
            sys.exit(1) # Critical error, cannot proceed

        print("Main App: EventManager database connection is ready.")

        self.model = QSqlTableModel(self, self.event_manager.db)
        self.model.setTable("events")
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        self.model.setHeaderData(0, Qt.Horizontal, "ID")
        self.model.setHeaderData(1, Qt.Horizontal, "Date")
        self.model.setHeaderData(2, Qt.Horizontal, "Title")
        self.model.setHeaderData(3, Qt.Horizontal, "Description")
        self.model.setHeaderData(4, Qt.Horizontal, "Time")

        if not self.model.select():
            QMessageBox.critical(self, "Model Select Error", f"Failed to select data: {self.model.lastError().text()}")
            self.event_manager.closeConnection()
            sys.exit(1)
        

        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSortingEnabled(True)
        self.table_view.resizeColumnsToContents()
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.hideColumn(0) #Hides ID column
        #self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed) # if you want on_selection changed run every time you select a different row


        layout.addWidget(self.table_view)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setLayout(layout)

    def on_selection_changed(self):
        self.get_selected_row_and_return_event_id()

    def get_selected_row_and_return_event_id(self):
        selection_model = self.table_view.selectionModel()
        selected_row_indexes = selection_model.selectedRows()

        if selected_row_indexes and len(selected_row_indexes) == 1:
            row_number = (selected_row_indexes[0]).row()
            id = self.model.data(self.model.index(row_number, 0))
            return id
        
    def refresh_events_data(self):
        if not self.model.select():
            print(f"EventViewerPage: Error refreshing data: {self.model.lastError().text()}")


class MainSchedulingCalendar(QCalendarWidget):
    def __init__(self, event_manager:EventManager):
        super().__init__()
        self.event_manager = event_manager


        self.cached_event_dates = set()
        self.load_event_dates()

        self.apply_stylesheet()

        today_format = QTextCharFormat()
        today_format.setBackground(QColor("#A6ECA8"))
        today_format.setForeground(QColor("dark green"))
        today_format.setFontWeight(QFont.ExtraBold)
        today_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.setDateTextFormat(QDate.currentDate(), today_format)

    def load_event_dates(self):
        self.cached_event_dates = self.event_manager.getAllEventDates()
        self.update()

    def paintCell(self, painter:QPainter, rect:QRect, date:QDate):
        
        super().paintCell(painter, rect, date)

        if date in self.cached_event_dates:

            events_for_this_date = self.event_manager.getEventsForDate(date)
            events_painted_number_padding = 0
            for event in events_for_this_date:
                painter.save()
                color = event['color']

                painter.setBrush(QBrush(QColor(color)))
                painter.setPen(Qt.NoPen)

                radius = 3
                center_x = rect.bottomRight().x() - events_painted_number_padding - 5
                center_y = rect.bottom() - radius - 2
                
                painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

                painter.restore()
                events_painted_number_padding+=7

    def apply_stylesheet(self):
        stylesheet = '''
        QCalendarWidget QWidget#qt_calendar_navigationbar {
            background-color: #4CAF50; /* Green */
            border-bottom: 1px solid #388E3C;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            padding: 5px;
            font-size: 16px;
        }
        QCalendarWidget QAbstractItemView::item:selected {
            /* If setSelectionMode is NoSelection, this may still target today if it's
               internally marked as 'selected'. Ensure no special background. */
            background-color: transparent; /* Or match your normal cell background, e.g., #FFFFFF */
            border: none;
        }
        QCalendarWidget QAbstractItemView {
            background-color: #FFFFFF;
            /* Allow a custom selection highlight if SingleSelection is ON */
            selection-background-color: #ADD8E6; /* Light Blue for user selection */
            selection-color: black;
            border: none;
            outline: 0;
        }
        '''
        self.setStyleSheet(stylesheet)
            

class ScreenHome(QWidget):
    def __init__(self, event_manager:EventManager):
        super().__init__()
        layout = QVBoxLayout()
        headerLabel = QLabel("This is the Home Calendar Screen")
        headerLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(headerLabel)

        button_layout = QHBoxLayout()
        to_current_date_button = QPushButton()
        to_current_date_button.setText("Go to Today's Date")
        to_current_date_button.clicked.connect(self.to_current_date)
        self.date_lookup_field = QDateEdit()
        self.date_lookup_field.setCalendarPopup(True)
        self.date_lookup_field.setDate(QDate.currentDate())
        self.date_lookup_field.dateChanged.connect(self.to_selected_date)
        button_layout.addWidget(to_current_date_button)
        button_layout.addWidget(self.date_lookup_field)

        layout.addLayout(button_layout)

        self.event_manager = event_manager


        self.calendar = MainSchedulingCalendar(self.event_manager)
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self.on_calendar_selection_changed)
        layout.addWidget(self.calendar)

        # layout.addStretch()
        self.setLayout(layout)

    def to_current_date(self):
        self.calendar.setSelectedDate(QDate.currentDate())

    def to_selected_date(self):
        self.calendar.setSelectedDate(self.date_lookup_field.date())

    def on_calendar_selection_changed(self):
        self.date_lookup_field.setDate(self.calendar.selectedDate())
        

class AddEventScreen(QWidget):
    event_added_signal = pyqtSignal()

    def __init__(self, event_manager: EventManager):
        super().__init__()
        layout = QVBoxLayout()
        headerLabel = QLabel("This is the Adding an Event Screen")
        headerLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(headerLabel)

        self.event_manager = event_manager

        self.form_layout = QFormLayout()
        self.eventNameField = QLineEdit()
        self.eventNameField.setPlaceholderText("Enter a name for your Event")
        self.form_layout.addRow(QLabel("Event Name: "), self.eventNameField)
        self.eventDateField = QDateEdit()
        self.eventDateField.setCalendarPopup(True)
        self.eventDateField.setDate(QDate.currentDate())
        self.eventDateField.setDisplayFormat("MM/dd/yyyy")
        self.form_layout.addRow(QLabel("Date: "), self.eventDateField)
        self.eventDescriptionField = QTextEdit()
        self.eventDescriptionField.setPlaceholderText("Description")
        self.form_layout.addRow(QLabel("Event Description: "), self.eventDescriptionField)
        self.eventTimeField = QTimeEdit()
        self.eventTimeField.setTime(QTime.currentTime())
        self.form_layout.addRow(QLabel("Start Time: "), self.eventTimeField)

        self.color_picker = CustomColorPicker()
        self.form_layout.addRow(None, self.color_picker)

        layout.addLayout(self.form_layout)

        add_event_button = QPushButton("Add Event")
        add_event_button.clicked.connect(self.add_event_to_database)
        layout.addWidget(add_event_button)

        layout.addStretch()
        self.setLayout(layout)
    
    def resetEventFields(self):
        self.eventNameField.clear()
        self.eventDateField.setDate(QDate.currentDate())
        self.eventDescriptionField.clear()
        self.eventTimeField.setTime(QTime.currentTime())

    def add_event_to_database(self):
        event_date = self.eventDateField.date()
        event_title = self.eventNameField.text()

        if event_date and event_title:
            event_description = self.eventDescriptionField.toPlainText()
            event_time = self.eventTimeField.time()
            event_color = self.color_picker.current_color
            if self.event_manager.addEvent(event_date, event_title, event_description, event_time, event_color):
                QMessageBox.information(self, "Success", f"Event '{event_title}' added for '{event_date}'")
                self.resetEventFields()
                self.event_added_signal.emit()

        else:
            QMessageBox.warning(self, "Missing Fields", "You are missing one or more of the required fields",QMessageBox.Ok)


class AboutScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        icon_pixmap = QPixmap("userIcon1.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel("Nathanael Spear")
        title_label = QLabel("Entry Level Software Developer")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        layout.addWidget(title_label)
        layout.addStretch()

        self.setLayout(layout)



class CustomColorPicker(QWidget):
    color_changed = pyqtSignal(QColor)

    def __init__(self, initial_color = Qt.blue, parent = None):
        super().__init__(parent)
        self.current_color = QColor(initial_color)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        self.color_display_label = QLabel(self)
        self.color_display_label.setFixedSize(50,25)
        self.color_display_label.setFrameShape(QLabel.Box)
        self.color_display_label.setFrameShadow(QLabel.Sunken)

        self.pick_color_button = QPushButton("Choose Color", self)
        self.pick_color_button.clicked.connect(self.open_color_dialog)

        layout.addWidget(self.color_display_label)
        layout.addWidget(self.pick_color_button)

        self.setLayout(layout)

        self.update_color_display()

    def update_color_display(self):
        color_str = self.current_color.name()
        self.color_display_label.setStyleSheet(
            f"background-color: {color_str};"
            f"border: 1px solid #999;"
            f"border-radius: 3px;" # Rounded corners
        )

    def open_color_dialog(self):
        new_color = QColorDialog.getColor(self.current_color, self)

        if new_color.isValid():
            self.current_color = new_color
            self.update_color_display()
            self.color_changed.emit(self.current_color)

    def get_color(self):
        return self.current_color
    
    def set_color(self, color):
        new_qcolor = QColor(color)
        if new_qcolor.isValid() and new_qcolor != self.current_color:
            self.current_color = new_qcolor
            self.update_color_display()
            self.color_changed.emit(self.current_color)


class EditEventMessageBox(QDialog):
    def __init__(self, event_manager:EventManager, selectedEventID):
        super().__init__()
        self.setWindowTitle("Editing Selected Event")

        self.selectedEventID = selectedEventID

        self.event_manager = event_manager

        self.selected_event_details = self.event_manager.getEventDetailsbyId(selectedEventID)
        
        # widgets to add to QMessageBox
        self.eventDate = QDateEdit()
        date_to_set = QDate.fromString(self.selected_event_details[0]["event_date"], "yyyy-MM-dd")
        self.eventDate.setDate(date_to_set)
        self.eventDate.setCalendarPopup(True)
        self.eventTitle = QLineEdit()
        self.eventTitle.setText(self.selected_event_details[0]["title"])
        self.eventDescription = QTextEdit()
        self.eventDescription.setText(self.selected_event_details[0]["description"])
        self.eventTime = QTimeEdit()
        time_to_set = QTime.fromString(self.selected_event_details[0]["event_time"], "HH:mm:ss.zzz")
        self.eventTime.setTime(time_to_set)
        self.eventColor = CustomColorPicker()
        color_to_set = QColor(self.selected_event_details[0]["event_color"])
        self.eventColor.set_color(color_to_set)

        form_layout = QFormLayout()
        form_layout.addRow("Date:", self.eventDate)
        form_layout.addRow("Title:", self.eventTitle)
        form_layout.addRow("Description:", self.eventDescription)
        form_layout.addRow("Time:", self.eventTime)
        form_layout.addRow("Color:", self.eventColor)

        # widget layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                           QDialogButtonBox.StandardButton.Cancel)
        
        self.button_box.accepted.connect(self.accept) # <--- Connect 'Ok' to accept()
        self.button_box.rejected.connect(self.reject) # <--- Connect 'Cancel' to reject()

        main_layout.addWidget(self.button_box)

    def get_edited_event_data(self):
        return {
            "event_date": self.eventDate.date().toString("yyyy-MM-dd"),
            "title": self.eventTitle.text(),
            "description": self.eventDescription.toPlainText(),
            "event_time": self.eventTime.time().toString("HH:mm:ss"),
            "event_color": self.eventColor.get_color().name(QColor.NameFormat.HexRgb),
            "event_id": self.selectedEventID
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main Window Setup
        self.setWindowTitle("Scheduler App")
        self.resize(1000, 600)

        self.center()

        # Toolbar Creation / StatusBar Setup
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        # Back to the Home Screen Action
        toHomeScreenAction = QAction(QIcon("home.png"), "Home", self)
        toHomeScreenAction.setStatusTip("Home")
        toHomeScreenAction.setToolTip("Go to Home Screen")
        toHomeScreenAction.triggered.connect(self.toHomePage)
        toolbar.addAction(toHomeScreenAction)

        # Add Event Action (Brings you to a specific page for Adding an Event)
        addEventAction = QAction(QIcon("table--plus.png"), "Add Event", self)
        addEventAction.setStatusTip("Add an Event")
        addEventAction.setToolTip("Add an Event")
        addEventAction.triggered.connect(self.toEditPage)
        toolbar.addAction(addEventAction)

        # Delete Event Action (Required to be on View All Events Page, and have an event row selected)
        deleteEventAction = QAction(QIcon("table--minus.png"), "Delete Event", self)
        deleteEventAction.setStatusTip("Delete Event")
        deleteEventAction.setToolTip("Delete Event")
        deleteEventAction.triggered.connect(self.deleteEvent)
        toolbar.addAction(deleteEventAction)

        # Editing Event Action

        # Need to create pixmap in order to edit sizing of icon before adding to action and toolbar
        pixmap = QPixmap("editing.png")
        size = QSize(16,16)
        scaled_pixmap = pixmap.scaled(size, aspectRatioMode=1, transformMode=0)
        edit_icon = QIcon(scaled_pixmap)
        editEventAction = QAction(edit_icon, "Edit Event", self)
        editEventAction.setStatusTip("Edit Event")
        editEventAction.setToolTip("Edit Event")
        editEventAction.triggered.connect(self.editEvent)
        toolbar.addAction(editEventAction)

        # View All Events Screen Action
        viewAllEventsAction = QAction(QIcon("table.png"), "View All Events", self)
        viewAllEventsAction.setStatusTip("View All Events")
        viewAllEventsAction.setToolTip("View All Events")
        viewAllEventsAction.triggered.connect(self.toViewAllEventsPage)
        toolbar.addAction(viewAllEventsAction)

        about_page_action = QAction("About",self)
        about_page_action.setStatusTip("About The Program Developer")
        about_page_action.setToolTip("About The Program Developer")
        about_page_action.triggered.connect(self.toAboutDeveloperPage)

        # Setting the Status Bar
        self.setStatusBar(QStatusBar(self))

        # Menu Creation
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        file_menu.addAction(toHomeScreenAction)
        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(addEventAction)
        edit_menu.addAction(deleteEventAction)
        edit_menu.addAction(editEventAction)
        view_menu = menu.addMenu("&View")
        view_menu.addAction(viewAllEventsAction)
        menu.addAction(about_page_action)

        # Stacked Widget Creation and Adding Widgets
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.previous_page_index = self.stacked_widget.currentIndex()
        self.current_page_widget = self.stacked_widget.currentWidget()

        self.event_manager = EventManager(db_filename="events.db")
        ## Instantiating screen widgets/pages
        self.homeScreen = ScreenHome(self.event_manager)
        self.addEventScreen = AddEventScreen(self.event_manager)
        self.viewAllEventsScreen = EventViewerPage(self.event_manager)
        self.aboutScreen = AboutScreen()
        ## Adding screen widgets to stacked widget
        self.homeScreen_index = self.stacked_widget.addWidget(self.homeScreen)
        self.addEventScreen_index = self.stacked_widget.addWidget(self.addEventScreen)
        self.eventViewScreen_index = self.stacked_widget.addWidget(self.viewAllEventsScreen)
        self.aboutScreen_index = self.stacked_widget.addWidget(self.aboutScreen)

        # Connecting functions to specific events
        self.addEventScreen.event_added_signal.connect(self.handleEventAdded)

        self.stacked_widget.currentChanged.connect(self.handle_page_change)

        # Setting default landing page of stacked widget
        self.stacked_widget.setCurrentWidget(self.homeScreen)

    def handle_page_change(self, new_index):
        self.previous_index_for_this_call = self.previous_page_index
        self.previous_page_index = new_index

        self.current_page_widget = self.stacked_widget.widget(new_index)

        if self.previous_index_for_this_call == self.addEventScreen_index:
            print("Leaving Editing Page. Clearing Edits...")
            self.addEventScreen.resetEventFields()

        
    def toHomePage(self):
        self.stacked_widget.setCurrentWidget(self.homeScreen)

    def toEditPage(self):
        self.addEventScreen.resetEventFields()
        self.stacked_widget.setCurrentWidget(self.addEventScreen)

    def toViewAllEventsPage(self):
        self.stacked_widget.setCurrentWidget(self.viewAllEventsScreen)

    def toAboutDeveloperPage(self):
        self.stacked_widget.setCurrentWidget(self.aboutScreen)

    def handleEventAdded(self):
        self.stacked_widget.setCurrentWidget(self.homeScreen)

        self.viewAllEventsScreen.model.select()
        self.homeScreen.calendar.load_event_dates()

    def editEvent(self):
        if isinstance(self.current_page_widget, EventViewerPage):
            selected_event_id = self.viewAllEventsScreen.get_selected_row_and_return_event_id()
            if selected_event_id:
                editing_event_messagebox = EditEventMessageBox(self.event_manager, selected_event_id)
                
                if editing_event_messagebox.exec() == QDialog.DialogCode.Accepted:
                    edited_event_data = editing_event_messagebox.get_edited_event_data()
                    if self.event_manager.updateEvent(edited_event_data):
                        edited_event_success_box = QMessageBox(
                                                    QMessageBox.Information,
                                                    "Event Updated!",
                                                    f"The event with ID: {edited_event_data["event_id"]}, has been updated with the entered information!",
                                                    QMessageBox.Ok
                        )
                        edited_event_success_box.exec_()
                        self.viewAllEventsScreen.refresh_events_data()



    def deleteEvent(self):
        if isinstance(self.current_page_widget, EventViewerPage):
            selected_event_id = self.viewAllEventsScreen.get_selected_row_and_return_event_id()
            if selected_event_id:
                id_event_details = self.event_manager.getEventDetailsbyId(selected_event_id)
                event_name = id_event_details[0]["title"]
                event_date = id_event_details[0]["event_date"]
                confirm_event_deletion_message = QMessageBox.warning(
                    None,
                    "Warning: Deleting Event",
                    f"Are you sure you want to delete this event?\n\nEvent Name: {event_name}\nEvent Date: {event_date}\n\nThis action cannot be undone!",
                    QMessageBox.Yes | QMessageBox.Cancel
                )
                if confirm_event_deletion_message == QMessageBox.Yes:
                    if self.event_manager.deleteEvent(selected_event_id):
                        self.viewAllEventsScreen.refresh_events_data()
                        QMessageBox.information(
                            None,
                            "Event Deleted",
                            f"The following event has been permanently deleted:\n\nEvent Name: {event_name}\nEvent Date: {event_date}",
                            QMessageBox.Ok
                        )
                    else:
                        QMessageBox.warning(None, "Event Deletion Error", "Error: The Event that you selected was not able to be Deleted!")
        else:
            QMessageBox.warning(None, "Wrong Page for Deleting Events", "You are on the wrong page for using this action!\nPlease use the Event Viewer page for Deleting Events!")



    def closeEvent(self, event):

        if self.viewAllEventsScreen and self.viewAllEventsScreen.model:
            self.viewAllEventsScreen.model.clear()
            self.viewAllEventsScreen.table_view.setModel(None) #potentially optional
            print("MainWindow: QSqlTableModel cleared.")

        if self.viewAllEventsScreen.event_manager:
            self.viewAllEventsScreen.event_manager.closeConnection()
        
        super().closeEvent(event)

    def center(self):
        qr = self.frameGeometry()

        cp = QDesktopWidget().availableGeometry().center()

        qr.moveCenter(cp)

        self.move(qr.topLeft())


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()