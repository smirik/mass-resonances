# SQL requests

### List of asteroids with librations:

```sql
SELECT asteroid.name as asteroid, libration.percentage AS libration_percentage, planet_1.name as planet1, planet_2.name as planet2, planet_1.longitude_coeff as mm, planet_2.longitude_coeff as ms, asteroid.longitude_coeff as m, planet_1.perihelion_longitude_coeff as lm, planet_2.perihelion_longitude_coeff as ls, asteroid.perihelion_longitude_coeff as l
FROM libration 
JOIN resonance ON resonance.id = libration.resonance_id 
JOIN planet AS planet_1 ON planet_1.id = resonance.first_body_id 
JOIN planet AS planet_2 ON planet_2.id = resonance.second_body_id 
JOIN asteroid ON asteroid.id = resonance.small_body_id 
LEFT OUTER JOIN resonance AS resonance_1 ON resonance_1.id = libration.resonance_id 
WHERE planet_1.name='MARS' 
ORDER BY asteroid.name 
LIMIT 100;
```

#### Conditions and filtering

* *gcd condition*: `AND NOT((planet_1.longitude_coeff%2=0) AND (planet_2.longitude_coeff%2=0) AND (asteroid.longitude_coeff%2=0)) AND NOT((planet_1.longitude_coeff%3=0) AND (planet_2.longitude_coeff%3=0) AND (asteroid.longitude_coeff%3=0))`
* *pure condition*: `AND libration.percentage is NULL`

#### Number of asteroids Mars-Jupiter with gcd=1
```sql
SELECT COUNT(*) FROM libration 
JOIN resonance ON resonance.id = libration.resonance_id 
JOIN planet AS planet_1 ON planet_1.id = resonance.first_body_id 
JOIN planet AS planet_2 ON planet_2.id = resonance.second_body_id 
JOIN asteroid ON asteroid.id = resonance.small_body_id 
LEFT OUTER JOIN resonance AS resonance_1 ON resonance_1.id = libration.resonance_id 
WHERE planet_1.name='MARS';
```

#### Number of asteroids Mars-Jupiter without gcd

```sql 
SELECT COUNT(*) FROM libration 
JOIN resonance ON resonance.id = libration.resonance_id
JOIN planet AS planet_1 ON planet_1.id = resonance.first_body_id 
JOIN planet AS planet_2 ON planet_2.id = resonance.second_body_id 
JOIN asteroid ON asteroid.id = resonance.small_body_id 
LEFT OUTER JOIN resonance AS resonance_1 ON resonance_1.id = libration.resonance_id 
WHERE planet_1.name='MARS' and not((planet_1.longitude_coeff%2=0) and (planet_2.longitude_coeff%2=0) and (asteroid.longitude_coeff%2=0)) and not((planet_1.longitude_coeff%3=0) and (planet_2.longitude_coeff%3=0) and (asteroid.longitude_coeff%3=0));
```

#### Number of pure resonant asteroids Mars-Jupiter with gcd=1

```sql 
SELECT COUNT(*) FROM libration 
JOIN resonance ON resonance.id = libration.resonance_id
JOIN planet AS planet_1 ON planet_1.id = resonance.first_body_id 
JOIN planet AS planet_2 ON planet_2.id = resonance.second_body_id 
JOIN asteroid ON asteroid.id = resonance.small_body_id 
LEFT OUTER JOIN resonance AS resonance_1 ON resonance_1.id = libration.resonance_id 
WHERE planet_1.name='MARS' and libration.percentage is NULL and not((planet_1.longitude_coeff%2=0) and (planet_2.longitude_coeff%2=0) and (asteroid.longitude_coeff%2=0)) and not((planet_1.longitude_coeff%3=0) and (planet_2.longitude_coeff%3=0) and (asteroid.longitude_coeff%3=0));
```

#### The same for Jupiter

```sql
SELECT COUNT(*) FROM libration JOIN resonance ON resonance.id = libration.resonance_id JOIN planet AS planet_1 ON planet_1.id = resonance.first_body_id JOIN planet AS planet_2 ON planet_2.id = resonance.second_body_id JOIN asteroid ON asteroid.id = resonance.small_body_id LEFT OUTER JOIN resonance AS resonance_1 ON resonance_1.id = libration.resonance_id WHERE planet_1.name='JUPITER';
```

#### Most popular resonances with Jupiter without gcd

```sql 
SELECT planet_1.longitude_coeff::text||' '||planet_2.longitude_coeff::text||' '||asteroid.longitude_coeff::text||' '||planet_1.perihelion_longitude_coeff::text||' '||planet_2.perihelion_longitude_coeff::text||' '||asteroid.perihelion_longitude_coeff::text as res, COUNT(*) as num
FROM libration 
JOIN resonance ON resonance.id = libration.resonance_id 
JOIN planet AS planet_1 ON planet_1.id = resonance.first_body_id 
JOIN planet AS planet_2 ON planet_2.id = resonance.second_body_id JOIN asteroid ON asteroid.id = resonance.small_body_id 
LEFT OUTER JOIN resonance AS resonance_1 ON resonance_1.id = libration.resonance_id 
WHERE planet_1.name='JUPITER'
GROUP BY res
ORDER BY num DESC
LIMIT 10;
```

#### Most popular resonances with Mars with gcd=1

```sql
SELECT planet_1.longitude_coeff::text||' '||planet_2.longitude_coeff::text||' '||asteroid.longitude_coeff::text||' '||planet_1.perihelion_longitude_coeff::text||' '||planet_2.perihelion_longitude_coeff::text||' '||asteroid.perihelion_longitude_coeff::text as res, COUNT(*) as num
FROM libration 
JOIN resonance ON resonance.id = libration.resonance_id 
JOIN planet AS planet_1 ON planet_1.id = resonance.first_body_id 
JOIN planet AS planet_2 ON planet_2.id = resonance.second_body_id JOIN asteroid ON asteroid.id = resonance.small_body_id 
LEFT OUTER JOIN resonance AS resonance_1 ON resonance_1.id = libration.resonance_id 
WHERE planet_1.name='MARS' and not((planet_1.longitude_coeff%2=0) and (planet_2.longitude_coeff%2=0) and (asteroid.longitude_coeff%2=0))
GROUP BY res
ORDER BY num DESC
LIMIT 100;
```