select
    league_code || '_' || season || '_' || home_team || '_' || away_team as match_id,
    league_code,
    league_name,
    season,
    round,
    match_date,
    home_team,
    away_team,
    home_goals,
    away_goals,
    ht_home_goals,
    ht_away_goals,
    is_played
from {{ source('raw', 'matches') }}
