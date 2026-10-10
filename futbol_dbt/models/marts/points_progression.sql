-- Puntos acumulados de cada equipo partido a partido (suma acumulada con ventana).
select
    league_name,
    season,
    team,
    match_date,
    row_number() over w as games_played,
    sum(points) over w  as cumulative_points
from {{ ref('int_team_matches') }}
window w as (
    partition by league_name, season, team
    order by match_date
    rows between unbounded preceding and current row
)
