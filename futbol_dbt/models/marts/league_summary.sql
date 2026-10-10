-- Indicadores por liga y temporada: goles por partido y reparto de resultados.
select
    league_name,
    season,
    count(*)                                                       as matches_played,
    round(avg(home_goals + away_goals), 2)                         as goals_per_match,
    round(100.0 * count(*) filter (where home_goals > away_goals) / count(*), 1) as home_win_pct,
    round(100.0 * count(*) filter (where home_goals = away_goals) / count(*), 1) as draw_pct,
    round(100.0 * count(*) filter (where home_goals < away_goals) / count(*), 1) as away_win_pct
from {{ ref('stg_matches') }}
where is_played
group by league_name, season
