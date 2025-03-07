CREATE FUNCTION fmod (
   dividend double precision,
   divisor double precision
) RETURNS double precision
    LANGUAGE sql IMMUTABLE AS
'SELECT dividend - floor(dividend / divisor) * divisor';

CREATE FUNCTION random_round (
    value double precision
) RETURNS INTEGER
    LANGUAGE sql IMMUTABLE AS
'SELECT FLOOR(value) + CASE WHEN RANDOM() < fmod(value, 1) THEN 1 ELSE 0 END';
