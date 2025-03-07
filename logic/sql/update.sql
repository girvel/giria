UPDATE cities
SET population = random_round(LEAST(1000, population * (1 + 0.00064 * growth_rate)))
FROM (
    SELECT growth_rate, city_id
    FROM world_map
    LEFT JOIN tiles ON world_map.tile = tiles.tile
) AS subquery
WHERE subquery.city_id = cities.city_id;

UPDATE players
SET
    gold = random_round(gold + gold_rate_total),
    wood = random_round(wood + wood_rate_total)
FROM (
    SELECT SUM(gold_rate) AS gold_rate_total,
           SUM(wood_rate) AS wood_rate_total,
           player_id
    FROM cities
    JOIN world_map ON cities.city_id = world_map.city_id
    JOIN tiles ON world_map.tile = tiles.tile
    GROUP BY player_id
) AS subquery
WHERE players.player_id = subquery.player_id;
