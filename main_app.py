import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget

# Import standalone module
import db_helpers

# Import modules from the new 'packages' directory structure

# Imports from the 'packages' directory:
from packages.utils import STYLE
from packages.utils import ImageLoaderThread # Moved thread to utils

# Imports from sub-packages:
from packages.auth.pages_auth import (
    LoginPage, RegisterPage, CompleteInfoPage, DashboardPage
)
from packages.customer.pages_customer import (
    MyRentalsPage, CarSelectionPage, TimeInfoPage, SummaryPage
)
from packages.admin.pages_admin import (
    AdminPage, AdminRequestsPage
)


class CarRentalApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.user_data = {}

        # Define indices for navigation
        self.login_index = 0
        self.car_index = 1
        self.summary_index = 2
        self.dashboard_index = 3
        self.register_index = 4
        self.complete_info_index = 5
        self.my_rentals_index = 6
        self.time_index = 7
        self.admin_index = 8
        self.requests_index = 9

        # Add all pages to the stack in order
        self.addWidget(LoginPage(self))
        self.addWidget(CarSelectionPage(self))
        self.addWidget(SummaryPage(self))
        self.addWidget(DashboardPage(self))
        self.addWidget(RegisterPage(self))
        self.addWidget(CompleteInfoPage(self))
        self.addWidget(MyRentalsPage(self))
        self.addWidget(TimeInfoPage(self))
        self.addWidget(AdminPage(self))
        self.addWidget(AdminRequestsPage(self))

        self.setCurrentIndex(self.login_index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    # Use the imported module name
    conn_check = db_helpers.get_db_connection(show_error=True)

    if not conn_check:
        sys.exit(app.exec_())

    conn_check.close()

    win = CarRentalApp()
    win.setWindowTitle("Car Rental System — MySQL/XAMPP")
    win.showMaximized()

    sys.exit(app.exec_())