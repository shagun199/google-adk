-- Create the database schema and tables

-- Hotels table (assuming you already have this)
CREATE TABLE IF NOT EXISTS hotels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    price_tier VARCHAR(50) NOT NULL CHECK (price_tier IN ('Midscale', 'Upper Midscale', 'Upscale', 'Upper Upscale', 'Luxury')),
    rating DECIMAL(2,1) CHECK (rating >= 0 AND rating <= 5),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Amenities table
CREATE TABLE amenities (
    id SERIAL PRIMARY KEY,
    amenity_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hotel amenities junction table
CREATE TABLE hotel_amenities (
    hotel_id INTEGER REFERENCES hotels(id) ON DELETE CASCADE,
    amenity_id INTEGER REFERENCES amenities(id) ON DELETE CASCADE,
    PRIMARY KEY (hotel_id, amenity_id)
);

-- Flights table
CREATE TABLE flights (
    id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    airline VARCHAR(100) NOT NULL,
    departure_city VARCHAR(100) NOT NULL,
    arrival_city VARCHAR(100) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    available_seats INTEGER NOT NULL DEFAULT 0,
    total_seats INTEGER NOT NULL,
    aircraft_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Restaurants table
CREATE TABLE restaurants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    cuisine_type VARCHAR(100) NOT NULL,
    rating DECIMAL(2,1) CHECK (rating >= 0 AND rating <= 5),
    price_range VARCHAR(20) CHECK (price_range IN ('$', '$$', '$$$', '$$$$')),
    phone VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Menu items table
CREATE TABLE menu_items (
    id SERIAL PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(8,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_vegetarian BOOLEAN DEFAULT FALSE,
    is_vegan BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rental cars table
CREATE TABLE rental_cars (
    id SERIAL PRIMARY KEY,
    vehicle_type VARCHAR(50) NOT NULL CHECK (vehicle_type IN ('Economy', 'Compact', 'Mid-size', 'Full-size', 'SUV', 'Luxury')),
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    pickup_location VARCHAR(255) NOT NULL,
    daily_rate DECIMAL(8,2) NOT NULL,
    available BOOLEAN DEFAULT TRUE,
    features TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bookings table
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    booking_type VARCHAR(50) NOT NULL CHECK (booking_type IN ('hotel', 'flight', 'restaurant', 'car_rental')),
    service_id INTEGER NOT NULL,
    booking_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'cancelled', 'pending')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample amenities
INSERT INTO amenities (amenity_name, description) VALUES
('WiFi', 'Complimentary wireless internet access'),
('Swimming Pool', 'Outdoor swimming pool'),
('Fitness Center', '24-hour fitness center'),
('Business Center', 'Business center with meeting rooms'),
('Pet Friendly', 'Pets allowed with additional fee'),
('Parking', 'Free self parking'),
('Room Service', '24-hour room service'),
('Spa', 'Full-service spa'),
('Restaurant', 'On-site restaurant'),
('Bar/Lounge', 'Hotel bar and lounge');

-- Insert sample hotels
INSERT INTO hotels (name, location, price_tier, rating, description) VALUES
('Grand Plaza Hotel', 'New York, NY', 'Luxury', 4.8, 'Luxury hotel in the heart of Manhattan'),
('Comfort Inn Downtown', 'Chicago, IL', 'Midscale', 4.2, 'Comfortable accommodations in downtown Chicago'),
('Marriott Business Center', 'San Francisco, CA', 'Upper Upscale', 4.5, 'Business-focused hotel with modern amenities'),
('Holiday Inn Express', 'Los Angeles, CA', 'Upper Midscale', 4.0, 'Convenient location near LAX airport'),
('Ritz Carlton Executive', 'Miami, FL', 'Luxury', 4.9, 'Beachfront luxury resort with world-class service');

-- Insert hotel amenities relationships
INSERT INTO hotel_amenities (hotel_id, amenity_id) VALUES
(1, 1), (1, 2), (1, 4), (1, 7), (1, 8), (1, 9), (1, 10), -- Grand Plaza
(2, 1), (2, 3), (2, 6), -- Comfort Inn
(3, 1), (3, 3), (3, 4), (3, 6), (3, 9), -- Marriott
(4, 1), (4, 6), (4, 3), -- Holiday Inn
(5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10); -- Ritz Carlton

-- Insert sample flights
INSERT INTO flights (flight_number, airline, departure_city, arrival_city, departure_time, arrival_time, price, available_seats, total_seats, aircraft_type) VALUES
('AA123', 'American Airlines', 'New York', 'Los Angeles', '2025-10-15 08:00:00', '2025-10-15 11:30:00', 299.99, 45, 180, 'Boeing 737'),
('UA456', 'United Airlines', 'Chicago', 'San Francisco', '2025-10-16 14:00:00', '2025-10-16 16:45:00', 324.50, 67, 160, 'Airbus A320'),
('DL789', 'Delta Airlines', 'Miami', 'New York', '2025-10-17 09:30:00', '2025-10-17 12:15:00', 278.25, 23, 150, 'Boeing 757'),
('SW101', 'Southwest Airlines', 'Los Angeles', 'Chicago', '2025-10-18 16:45:00', '2025-10-18 21:30:00', 189.99, 89, 140, 'Boeing 737'),
('JB202', 'JetBlue Airways', 'San Francisco', 'Miami', '2025-10-19 11:20:00', '2025-10-19 19:45:00', 367.75, 34, 162, 'Airbus A321');

-- Insert sample restaurants
INSERT INTO restaurants (name, location, cuisine_type, rating, price_range, phone, description) VALUES
('The Italian Corner', 'New York, NY', 'Italian', 4.6, '$$$', '212-555-0123', 'Authentic Italian cuisine with fresh pasta and wine'),
('Sushi Zen', 'Los Angeles, CA', 'Japanese', 4.8, '$$$$', '310-555-0456', 'Premium sushi and sashimi experience'),
('BBQ Masters', 'Chicago, IL', 'American', 4.3, '$$', '312-555-0789', 'Traditional American BBQ with craft beer selection'),
('Spice Route', 'San Francisco, CA', 'Indian', 4.4, '$$', '415-555-0321', 'Flavorful Indian dishes with vegetarian options'),
('Ocean Breeze', 'Miami, FL', 'Seafood', 4.7, '$$$', '305-555-0654', 'Fresh seafood with ocean views');

-- Insert sample menu items
INSERT INTO menu_items (restaurant_id, item_name, description, price, category, is_vegetarian, is_vegan) VALUES
-- The Italian Corner
(1, 'Margherita Pizza', 'Classic pizza with tomato, mozzarella, and basil', 18.99, 'Main Course', true, false),
(1, 'Fettuccine Alfredo', 'Creamy pasta with parmesan cheese', 22.50, 'Main Course', true, false),
(1, 'Tiramisu', 'Traditional Italian dessert', 8.99, 'Dessert', true, false),
-- Sushi Zen  
(2, 'Omakase Tasting', 'Chef selection of premium sushi', 85.00, 'Tasting Menu', false, false),
(2, 'Dragon Roll', 'Eel and avocado with special sauce', 16.50, 'Sushi Roll', false, false),
(2, 'Miso Soup', 'Traditional soybean soup', 4.50, 'Appetizer', true, true),
-- BBQ Masters
(3, 'Brisket Platter', 'Slow-smoked brisket with two sides', 24.99, 'Main Course', false, false),
(3, 'Pulled Pork Sandwich', 'House-smoked pork with coleslaw', 14.99, 'Sandwich', false, false),
(3, 'Mac and Cheese', 'Creamy three-cheese macaroni', 8.99, 'Side', true, false);

-- Insert sample rental cars
INSERT INTO rental_cars (vehicle_type, make, model, year, pickup_location, daily_rate, available, features) VALUES
('Economy', 'Toyota', 'Corolla', 2023, 'Los Angeles Airport', 29.99, true, ARRAY['Air Conditioning', 'Bluetooth', 'Backup Camera']),
('Compact', 'Honda', 'Civic', 2024, 'Chicago Downtown', 34.99, true, ARRAY['Air Conditioning', 'Bluetooth', 'Lane Assist']),
('Mid-size', 'Nissan', 'Altima', 2023, 'New York JFK', 42.99, true, ARRAY['Air Conditioning', 'Navigation', 'Heated Seats']),
('Full-size', 'Chevrolet', 'Malibu', 2024, 'Miami Airport', 48.99, true, ARRAY['Air Conditioning', 'Navigation', 'Heated Seats', 'Sunroof']),
('SUV', 'Ford', 'Explorer', 2023, 'San Francisco Airport', 62.99, true, ARRAY['4WD', 'Navigation', 'Third Row Seating', 'Tow Package']),
('Luxury', 'BMW', '3 Series', 2024, 'New York Manhattan', 89.99, true, ARRAY['Leather Seats', 'Premium Sound', 'Navigation', 'Heated/Cooled Seats']);

-- Insert sample bookings
INSERT INTO bookings (customer_name, booking_type, service_id, booking_date, total_amount, status) VALUES
('John Smith', 'hotel', 1, '2025-10-15', 450.00, 'confirmed'),
('Jane Doe', 'flight', 2, '2025-10-16', 324.50, 'confirmed'),
('Mike Johnson', 'restaurant', 1, '2025-10-17', 65.48, 'confirmed'),
('Sarah Wilson', 'car_rental', 3, '2025-10-18', 171.96, 'confirmed'),
('David Brown', 'hotel', 5, '2025-10-19', 899.99, 'pending');

-- Create indexes for better performance
CREATE INDEX idx_hotels_location ON hotels(location);
CREATE INDEX idx_hotels_price_tier ON hotels(price_tier);
CREATE INDEX idx_flights_departure_city ON flights(departure_city);
CREATE INDEX idx_flights_arrival_city ON flights(arrival_city);
CREATE INDEX idx_flights_departure_time ON flights(departure_time);
CREATE INDEX idx_restaurants_location ON restaurants(location);
CREATE INDEX idx_restaurants_cuisine_type ON restaurants(cuisine_type);
CREATE INDEX idx_rental_cars_pickup_location ON rental_cars(pickup_location);
CREATE INDEX idx_rental_cars_vehicle_type ON rental_cars(vehicle_type);
CREATE INDEX idx_bookings_customer_name ON bookings(customer_name);
CREATE INDEX idx_bookings_booking_type ON bookings(booking_type);