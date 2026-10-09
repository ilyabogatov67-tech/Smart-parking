-- Smart Parking
-- Database initialization

CREATE TABLE IF NOT EXISTS parking_sessions (
    id SERIAL PRIMARY KEY,

    plate VARCHAR(20) NOT NULL,

    minutes INTEGER NOT NULL
        CHECK (minutes > 0),

    billed_hours INTEGER NOT NULL
        CHECK (billed_hours > 0),

    hourly_rate NUMERIC(10, 2) NOT NULL
        CHECK (hourly_rate >= 0),

    total NUMERIC(10, 2) NOT NULL
        CHECK (total >= 0),

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Initial demonstration data

INSERT INTO parking_sessions
(plate, minutes, billed_hours, hourly_rate, total)
VALUES
('A123BC77', 60, 1, 100.00, 100.00),
('B456CD77', 125, 3, 100.00, 300.00),
('E777KK77', 90, 2, 100.00, 200.00);
