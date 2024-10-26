IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'camping')
BEGIN
    EXEC ('CREATE SCHEMA camping')
END;

DROP TABLE IF EXISTS camping.booking;
DROP TABLE IF EXISTS camping.customers;
DROP TABLE IF EXISTS camping.summary;


CREATE TABLE camping.customers(
	customer_id int  IDENTITY(1,1) PRIMARY KEY,
	first_name varchar(255) NOT NULL,
	last_name varchar(255) NOT NULL,
	phone varchar (25) NULL,
	address varchar(255) NULL,
	post_code varchar(4) NULL
);


CREATE TABLE camping.booking(
	booking_id int IDENTITY(1,1) PRIMARY KEY,
	customer_id int NULL FOREIGN KEY REFERENCES camping.customers(customer_id),
	booking_date date NOT NULL,
	arrival_date date NOT NULL,
	campground_id int NOT NULL,
	campsite_size varchar(10),
	num_campsites INT
);



CREATE TABLE camping.summary (
	summary_id  int  IDENTITY(1,1) PRIMARY KEY,
	campground_id int NULL,
	summary_date date NULL,
	total_sales decimal (10, 2) NULL,
	total_bookings int NULL
);