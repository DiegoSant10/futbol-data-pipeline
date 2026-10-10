-- En una liga, todo gol marcado por un equipo es un gol recibido por otro.
select league_name, season, sum(goals_for) as gf, sum(goals_against) as gc
from {{ ref('standings') }}
group by league_name, season
having sum(goals_for) != sum(goals_against)
