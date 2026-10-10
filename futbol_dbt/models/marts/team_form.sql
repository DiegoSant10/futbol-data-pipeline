-- Racha de los últimos 5 partidos de cada equipo (ej: 'WWDLW', del más antiguo al más reciente).
with ordered as (
    select
        league_name, season, team, match_date, result,
        row_number() over (
            partition by league_name, season, team order by match_date desc
        ) as recency
    from {{ ref('int_team_matches') }}
)

select
    league_name,
    season,
    team,
    string_agg(result, '' order by match_date) as last_5
from ordered
where recency <= 5
group by league_name, season, team
