-- Tabla de clasificación por liga y temporada.
with totals as (
    select
        league_name,
        season,
        team,
        count(*)                                 as played,
        count(*) filter (where result = 'W')     as won,
        count(*) filter (where result = 'D')     as drawn,
        count(*) filter (where result = 'L')     as lost,
        sum(goals_for)::integer                  as goals_for,
        sum(goals_against)::integer              as goals_against,
        sum(goals_for - goals_against)::integer  as goal_diff,
        sum(points)::integer                     as points
    from {{ ref('int_team_matches') }}
    group by league_name, season, team
)

select
    rank() over (
        partition by league_name, season
        order by points desc, goal_diff desc, goals_for desc
    ) as position,
    *
from totals
