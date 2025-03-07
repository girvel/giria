CREATE TABLE tiles (
    tile VARCHAR(8) PRIMARY KEY,
    growth_rate DOUBLE PRECISION NOT NULL,
    gold_rate DOUBLE PRECISION NOT NULL,
    wood_rate DOUBLE PRECISION NOT NULL
);

INSERT INTO tiles (tile, growth_rate, gold_rate, wood_rate) VALUES
('dead', 0.5, 0.5, 0.5),
('plain', 2, 1, 1),
('forest', 0.8, 0.8, 2),
('mountain', 0.8, 2, 0.5);

CREATE TABLE players (
    player_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    login VARCHAR(20) NOT NULL,
    password BYTEA NOT NULL,
    color CHAR(6) NOT NULL,
    gold INTEGER NOT NULL,
    wood INTEGER NOT NULL
);

INSERT INTO players (login, color, password, gold, wood)
VALUES
('remnants', 'dddddd', '$2b$12$VCMoArsi18YhtdDoJIfE5.J4PeUpJfLOxvJSnw5vB.0MLCDfSXQyi', 0, 0),
('girvel', 'dd134b', '$2b$12$D38R.HynTNpRGcsq1lhae.MyOSgVM7tUyfhfLBzbgXrWUQ5k.iRxi', 10, 10);

CREATE TABLE cities (
    city_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(20) NOT NULL,
    population INTEGER NOT NULL,
    player_id INTEGER NOT NULL REFERENCES players
);

INSERT INTO cities (name, population, player_id) VALUES
('Aldberg', 100, 1),
('Westhall', 150, 1),
('Eastwatch', 50, 1),
('Ledfolk', 100, 1);

CREATE TABLE armies (
    army_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    player_id INTEGER NOT NULL REFERENCES players,
    army_size INTEGER NOT NULL
);

INSERT INTO armies (player_id, army_size) VALUES
(1, 20);

CREATE TABLE world_map (
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    tile VARCHAR(8) NOT NULL REFERENCES tiles,
    configuration INTEGER NOT NULL,
    city_id INTEGER REFERENCES cities,
    army_id INTEGER REFERENCES armies,

    PRIMARY KEY(x, y),
    CONSTRAINT configurations_n CHECK (configuration BETWEEN 0 AND 4)
);
