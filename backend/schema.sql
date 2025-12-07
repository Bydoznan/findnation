CREATE TABLE IF NOT EXISTS found_items (
    id UUID PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    location_found TEXT NOT NULL,
    dominant_color VARCHAR(30) NOT NULL,
    date_found DATE NOT NULL,
    email VARCHAR(200) NOT NULL,
    voivodeship VARCHAR(50),
    reporting_entity VARCHAR(100)
);