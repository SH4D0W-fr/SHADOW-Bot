CREATE TABLE configurations (
    server_id VARCHAR(255) PRIMARY KEY,
    config_key VARCHAR(255) NOT NULL,
    config_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE giveaways(
    giveaway_id VARCHAR(255) PRIMARY KEY,
    server_id VARCHAR(255) NOT NULL,
    giveaway_channel_id VARCHAR(255) NOT NULL,  
    giveaway_message_id VARCHAR(255),
    giveaway_title VARCHAR(255) NOT NULL,
    giveaway_prizes TEXT NOT NULL,
    giveaway_winner_count INT NOT NULL,
    giveaway_end_date TIMESTAMP NOT NULL,
    giveaway_organizer_id VARCHAR(255) NOT NULL,
    giveaway_participants TEXT,
    giveaway_conditions TEXT,
    giveaway_is_finished BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_server_id (server_id),
    INDEX idx_is_finished (giveaway_is_finished),
    INDEX idx_message_id (giveaway_message_id)
);

CREATE TABLE tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    server_id VARCHAR(255) NOT NULL,
    channel_id VARCHAR(255) NOT NULL UNIQUE,
    owner_id VARCHAR(255) NOT NULL,
    type_key VARCHAR(255) NOT NULL,
    claimed_by_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_owner_message TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_staff_message TIMESTAMP,
    members TEXT,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMP,
    closed_by_id VARCHAR(255),
    close_reason TEXT,
    INDEX idx_server_id (server_id),
    INDEX idx_owner_id (owner_id),
    INDEX idx_channel_id (channel_id),
    INDEX idx_is_closed (is_closed)
);