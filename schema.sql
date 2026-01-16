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