# DriveSync-XAMPP-MYSQL-
<img width="1920" height="1037" alt="image" src="https://github.com/user-attachments/assets/fb6fe024-4857-47e3-a496-0e31a712fcf5" />
fix the following to fit into github :

DriveSync is a Python-based Car Rental Management System designed to streamline booking and inventory operations using a professional desktop GUI built with PyQt5. It features secure authentication for separate user and administrator roles.

📋 Prerequisites

Python 3: Ensure you have Python 3 installed.



MySQL Database: You need a running MySQL server (e.g., using XAMPP, WAMP, or MAMP).



Required Python Libraries:

pip install PyQt5

pip install mysql-connector-python



#✨ Key Features

Dynamic Car Display: Displays available rental cars in a dynamic grid view, with the ability to filter and select based on availability.



Booking Management: Users can select vehicles, specify rental periods, view a booking summary, and confirm reservations.



User Dashboard: A personalized dashboard to view current and past rental history ("My Rentals").



Admin Panel: A comprehensive dashboard for administrators to view all users, all cars, and manage Pending Change Requests from users.



Pending Requests System: User-requested car changes go into a 'Pending' status, requiring explicit approval from an administrator.



#🛠️ Setup and Installation

💾 Database Setup (SQL)

You must run the following SQL code in your MySQL environment (phpMyAdmin, MySQL Workbench, etc.) 

to create the database and the necessary tables before running the Python application.



SQL

-- 1. Create the database and select it

CREATE DATABASE IF NOT EXISTS car_rental;

USE car_rental;



-- 2. Create the tables - Input the following code in SQL:

-- SQL Script for DriveSync Car Rental Management System



-- 1. Create the database and select it

-- NOTE: The database name is 'car_rental'

CREATE DATABASE IF NOT EXISTS car_rental;

USE car_rental;



-- 2. Create the tables:

-- SQL Script for DriveSync Car Rental Management System

-- 1. Create the database and select it
-- NOTE: The database name is 'car_rental'
CREATE DATABASE IF NOT EXISTS car_rental;
USE car_rental;

-- 2. Create the tables

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
-- Foreign keys: user_id (-> users), car_id (-> cars)
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
-- Foreign key: rental_id (-> rentals)
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rental_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_time DATETIME NOT NULL,
    FOREIGN KEY (rental_id) REFERENCES rentals(id)
);

-- Car Change Requests Table (Corrected Foreign Key Syntax)
-- Ensures the data types for foreign key columns match the primary keys they reference (INT NOT NULL).
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

-- Admin User (username: admin, password: admin)
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

#▶️ How to Run the Application

1.Start MySQL Service

   Make sure your MySQL server is running before starting the application.

2.Activate Virtual Environment

   Windows:

      venv\Scripts\activate

  macOS/Linux:

      source venv/bin/activate

3.Run the Application

4.First Run

After executing the car_rental setup script, the application will:

Connect to Database: Connect to the car_rental database instance on your local MySQL server.

Verify Tables: Confirm the existence of all five tables (users, cars, rentals, payments, and car_change_requests).

Insert Data: Automatically insert the default administrator account (admin/admin) and eight sample cars into the tables.

Display Main Window: Display the main application window, defaulting to the Login Page.

How to Use



Logging In

1.User Inputs their User Information [Name & Password]

2.Click "Login"

3.If user information is not full a window will show where they place the missing information



Register User

1.Click "Register" button

2.User inputs information [Name,Phone Number and Address are optional but will be needed upon login]

3.User is added to the database and appear in the table



Renting a Car Selction

1.Click "Rent A Car" button

2.Select Car to be Rented

3.Input time and method of acquiring car[Delivery/Pick-up]

4.A summary page will be showed and total payment

5.After payment the rental information will be saved in database



View Rentals 

1.Click "My Rentals" button

2.Table Displays all user rentals and allows editing

  Edit Car

    1.Click "Edit Car" button

    2.Select the new car you want

    3.Reqeust is Saved in database for admin to review

  Edit Information [Acquisition/Time Info]

    1.Click "Edit Time" or "Edit Delivery" button

    2.Input new user information

    3.Saves updated information inside the database

Admin Dashboard

1.Login with Username and password [admin/admin]

2.Select admin action

    Admin Reqeusts

    1.Click "Pending Requests" button

    2.Select car change reqeust

    3.Approve/Deny Reqeust

    4.Choice is saved in database

    Admin Car Management

    1.Click "Car Status Panel" button

    2.Select car to manage

    3.Updated Car condition is saved in database

    
#🖼️ Screenshots
<img width="1920" height="1022" alt="image" src="https://github.com/user-attachments/assets/2b186d25-a8ca-4c4e-9daa-2374c61de917" />
<img width="1918" height="1040" alt="image" src="https://github.com/user-attachments/assets/e989dc95-268d-4ae6-8a65-901ce57b41f9" />
<img width="1915" height="1030" alt="image" src="https://github.com/user-attachments/assets/d0a30bd5-7a2f-4df8-afd9-1d4818727e53" />
<img width="1920" height="1044" alt="image" src="https://github.com/user-attachments/assets/9980f8f3-fd5d-4086-bec2-d113168a0acb" />
<img width="1920" height="1033" alt="image" src="https://github.com/user-attachments/assets/4c172bb7-c560-4415-832f-80ce182f3711" />
<img width="1917" height="1035" alt="image" src="https://github.com/user-attachments/assets/b3525519-64f2-4a71-b9f7-922d08dbe8e4" />
<img width="1916" height="1035" alt="image" src="https://github.com/user-attachments/assets/aed012f1-1163-452f-8f2f-edd4fa43344f" />
<img width="1920" height="1044" alt="image" src="https://github.com/user-attachments/assets/daaea71e-dcbb-4b30-a018-c3b75f295659" />
<img width="1920" height="1038" alt="image" src="https://github.com/user-attachments/assets/a3f68620-4f55-4684-a5de-ce7be024df0c" />
<img width="1919" height="1038" alt="image" src="https://github.com/user-attachments/assets/51533210-f01d-497e-a51c-d0347221b9aa" />
<img width="1920" height="1038" alt="image" src="https://github.com/user-attachments/assets/48a5624d-707f-4ea4-9a65-5dc5e6d2f87e" />



# 🔰  Revisions from panel’s advice or recommendations
Admin now has authority to confirm the cars change
         <img width="1920" height="1038" alt="image" src="https://github.com/user-attachments/assets/44a44219-af74-4a76-bc43-a792d66cbe72" />
Unavailable Cars are now grayed out when selecting a new car
        <img width="1919" height="1041" alt="image" src="https://github.com/user-attachments/assets/2b204b46-3d66-4370-a947-a9ae41fc17e4" />
DB Security the database information is now in separate files
        <img width="1836" height="674" alt="image" src="https://github.com/user-attachments/assets/76274dcb-e283-4f27-acd8-dd5145bbacc7" />
Files are now Separated
        <img width="1915" height="799" alt="image" src="https://github.com/user-attachments/assets/f5a482f5-2258-4f7e-b8c5-04a083e66655" />


