SELECT 
    b.booking_id,                                 -- Booking identifier
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,  -- Full name of the customer
    b.booking_date,                               -- Date when the booking was made
    b.arrival_date,                               -- Customer's arrival date
    b.campground_id,                              -- Identifier of the campground where the booking was made
    b.campsite_size,                              -- Size category of the campsite booked
    b.num_campsites,                              -- Number of campsites booked
    b.num_campsites * campsite_rate AS total_cost, -- Total cost calculation (if campsite_rate exists)
    c.phone AS customer_phone                     -- Customer's phone number for easy contact
FROM 
    camping.booking b
JOIN 
    camping.customers c ON b.customer_id = c.customer_id  -- Join customers and bookings based on customer_id
-- Replace the ? placeholder with an actual parameter in your application or query tool
WHERE 
    b.campground_id = 1                           -- Placeholder for campground_id
ORDER BY 
    b.booking_date DESC;                          -- Sort by booking date (most recent first)
