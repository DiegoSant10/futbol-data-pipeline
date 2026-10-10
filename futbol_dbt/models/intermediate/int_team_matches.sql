-- Cada partido jugado aparece DOS veces, una por cada equipo.
-- Así es mucho más fácil calcular estadísticas por equipo (patrón "unpivot").
with played as (
    select * from {{ ref('stg_matches') }} where is_played
),

unpivoted as (
    select match_id, league_name, season, match_date,
           home_team as team, away_team as opponent, 'home' as venue,
           home_goals as goals_for, away_goals as goals_against
    from played
    union all
    select match_id, league_name, season, match_date,
           away_team, home_team, 'away',
           away_goals, home_goals
    from played
)

select
    *,
    case when goals_for > goals_against then 'W'
         when goals_for = goals_against then 'D'
         else 'L' end as result,
    case when goals_for > goals_against then 3
         when goals_for = goals_against then 1
         else 0 end as points
from unpivoted
