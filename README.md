# DriveSync-XAMPP-MYSQL-
<img width="1920" height="1037" alt="image" src="https://github.com/user-attachments/assets/fb6fe024-4857-47e3-a496-0e31a712fcf5" />
DriveSync 🚗 Car Rental Management System
DriveSync is a Python-based Car Rental Management System designed to streamline booking and inventory operations using a professional desktop GUI built with PyQt5. It features secure authentication for separate user and administrator roles, with persistent data storage managed by a MySQL database.

✨ Key Features
Dynamic Car Display: Displays available rental cars in a dynamic grid view, with filtering options based on availability.

Booking Management: Users can select vehicles, specify rental periods, view a booking summary, and confirm reservations.

User Dashboard: A personalized dashboard to view current and past rental history ("My Rentals").

Admin Panel: A comprehensive dashboard for administrators to view all users, cars, and manage pending requests.

Pending Requests System: User-requested car changes go into a 'Pending' status, requiring explicit approval from an administrator via the dedicated Admin Requests panel.

📋 Prerequisites
Ensure you have the following installed on your system:

Python 3: The core language environment.

MySQL Database: A running MySQL server instance (commonly achieved using tools like XAMPP, WAMP, or MAMP).

Required Python Libraries
Install the necessary libraries using pip:

Bash

pip install PyQt5 mysql-connector-python
🛠️ Setup and Installation
💾 Database Setup (SQL)
You must run the entire SQL script below in your MySQL environment (e.g., phpMyAdmin, MySQL Workbench) to create the database, all necessary tables, and the initial data before running the Python application.

SQL

-- SQL Script for DriveSync Car Rental Management System

-- 1. Create the database and select it
CREATE DATABASE IF NOT EXISTS car_rental;
USE car_rental;

-- 2. Create the tables:

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    phone VARCHAR(20),
    addr VARCHAR(255),
    role ENUM('user', 'admin') DEFAULT 'user'
);

-- Cars Table
CREATE TABLE IF NOT EXISTS cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    hourly_rate DECIMAL(10, 2) NOT NULL,
    car_condition VARCHAR(50) NOT NULL,
    status ENUM('Available', 'In Use', 'Maintenance') DEFAULT 'Available',
    img_url VARCHAR(255)
);

-- Rentals Table
CREATE TABLE IF NOT EXISTS rentals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    car_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    hours_rented INT NOT NULL,
    rental_mode ENUM('Pickup', 'Delivery') DEFAULT 'Pickup',
    delivery_location VARCHAR(255),
    total_cost DECIMAL(10, 2) NOT NULL,
    created_at DATETIME NOT NULL,
    status ENUM('Active', 'Completed', 'Cancelled') DEFAULT 'Active',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (car_id) REFERENCES cars(id)
);

-- Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rental_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_time DATETIME NOT NULL,
    FOREIGN KEY (rental_id) REFERENCES rentals(id)
);

-- Car Change Requests Table (Admin Approval Workflow)
CREATE TABLE car_change_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    rental_id INT NOT NULL,
    old_car_id INT NOT NULL,
    new_car_id INT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (rental_id) REFERENCES rentals(id),
    FOREIGN KEY (old_car_id) REFERENCES cars(id),
    FOREIGN KEY (new_car_id) REFERENCES cars(id)
);

-- 3. Insert initial data

-- Admin User (Default Credentials)
INSERT INTO users (username, password, name, phone, addr, role) VALUES
('admin', 'admin', 'System Admin', '555-1234', 'Headquarters, Main St', 'admin');

-- Sample Cars (8 cars)
INSERT INTO cars (name, hourly_rate, car_condition, status, img_url) VALUES
('Toyota Vios', 50.00, 'Good', 'Available', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Toyota_Vios_XP150_facelift_01.jpg/250px-Toyota_Vios_XP150_facelift_01.jpg'),
('Honda City', 65.00, 'Excellent', 'Available', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Honda_City_Hatchback_e%3AHEV_RS_cropped.jpg/250px-Honda_City_Hatchback_e%3AHEV_RS_cropped.jpg'),
('Mitsubishi Mirage', 45.00, 'Fair', 'In Use', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Mitsubishi_Mirage_G4_%28facelift%29_--_01-27-2021.jpg/250px-Mitsubishi_Mirage_G4_%28facelift%29_--_01-27-2021.jpg'),
('Ford Everest', 120.00, 'Excellent', 'Available', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/2023_Ford_Everest_Sport_in_Australia_%28cropped%29.jpg/250px-2023_Ford_Everest_Sport_in_Australia_%28cropped%29.jpg'),
('Nissan Navara', 100.00, 'Good', 'Available', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Nissan_Navara_V_2.5_Automatic_%28Thailand%29_front.jpg/250px-Nissan_Navara_V_2.5_Automatic_%28Thailand%29_front.jpg'),
('Hyundai Accent', 55.00, 'Good', 'Maintenance', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/2020_Hyundai_Accent_GLS_sedan.jpg/250px-2020_Hyundai_Accent_GLS_sedan.jpg'),
('Suzuki Ertiga', 80.00, 'Excellent', 'Available', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Suzuki_Ertiga_II_facelift_in_Indonesia.jpg/250px-Suzuki_Ertiga_II_facelift_in_Indonesia.jpg'),
('Kia Picanto', 40.00, 'Fair', 'Available', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/Kia_Picanto_GT-Line_MY18_%28cropped%29.jpg/250px-Kia_Picanto_GT-Line_MY18_%28cropped%29.jpg');
▶️ How to Run the Application
1. Start MySQL Service
Make sure your MySQL server is running before starting the application.

2. Activate Virtual Environment
Always activate your virtual environment before running the application.

Operating System	Command
Windows	venv\Scripts\activate
macOS/Linux	source venv/bin/activate

Export to Sheets

3. Run the Application
Run the main Python script (assumed to be named crsdatabase.py or similar).

Bash

python crsdatabase.py
First Run Behavior
If the SQL script has been successfully executed, the application will:

Connect to Database: Establish a connection to the car_rental database.

Verify Data: Confirm the existence of all five tables and the initial admin/car data.

Display Main Window: Display the main application window, defaulting to the Login Page.

Default Admin Credentials	
Username:	admin
Password:	admin

Export to Sheets

❓ How to Use (Workflow)
Logging In & Registration
Login: Input your Username and Password on the Login Page and click "Login." If you are a new user, you will be prompted to complete any missing information (Name, Phone, Address).

Register: Click the "Register" button, input your information (Name, Phone Number, and Address are optional but recommended), and you will be added to the database.

Renting a Car
Click "Rent A Car" from the Dashboard.

Select the car you wish to rent.

Input the start/end time and select the rental mode (Delivery/Pick-up).

A summary page will show the total cost. After payment/confirmation, the rental is saved to the database.

Viewing and Editing Rentals (My Rentals)
Click "My Rentals" from the Dashboard. A table will display all your current and past rentals.

Edit Car (Change Request): a. Click "Edit Car" next to an active rental. b. Select the new car you want. c. The request is saved in the car_change_requests table with a Pending status for the Admin to review.

Edit Time/Info: a. Click "Edit Time" or "Edit Delivery". b. Input the new information (time or location). c. The updated information is immediately saved to the database for the active rental.

Admin Dashboard
Log in using the default admin credentials (admin/admin).

Admin Requests: a. Click "Pending Requests" button. b. Select a car change request from the table. c. Click "Approve" or "Deny". The choice is saved in the database, and the rental status is updated if approved.

Admin Car Management: a. Click "Car Status Panel" button. b. Select a car to manage. c. Update the car's condition or status (e.g., from 'Available' to 'Maintenance'). The update is saved to the database.

#🖼️ Screenshots
<img width="1920" height="1022" alt="image" src="https://github.com/user-attachments/assets/2b186d25-a8ca-4c4e-9daa-2374c61de917" />
<img width="1918" height="1040" alt="image" src="https://github.com/user-attachments/assets/e989dc95-268d-4ae6-8a65-901ce57b41f9" />
<img width="1915" height="1030" alt="image" src="https://github.com/user-attachments/assets/d0a30bd5-7a2f-4df8-afd9-1d4818727e53" />
<img width="1920" height="1044" alt="image" src="https://github.com/user-attachments/assets/9980f8f3-fd5d-4086-bec2-d113168a0acb" />
<img width="1920" height="1033" alt="image" src="https://github.com/user-attachments/assets/4c172bb7-c560-4415-832f-80ce182f3711" />








#
