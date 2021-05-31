CREATE TABLE IF NOT EXISTS characters (
    running_id INT AUTO_INCREMENT PRIMARY KEY,
    server VARCHAR(255) NOT NULL,
    player VARCHAR(255) NOT NULL,
    phy INT,
    ref INT,
    sta INT,
    kno INT,
    ins INT,
    pow INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)  ENGINE=INNODB;