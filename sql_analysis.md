# SQL Analysis — Premier League (2015–2025)
**Database:** `football.db` (SQLite) · 3,800+ matches across 10 seasons

## 1. How many matches did each team play in total?

```sql
WITH home_appearances AS (
    SELECT home_team_name AS team, COUNT(*) AS matches
    FROM matches
    WHERE status = 'FINISHED'
    GROUP BY home_team_name
),
away_appearances AS (
    SELECT away_team_name AS team, COUNT(*) AS matches
    FROM matches
    WHERE status = 'FINISHED'
    GROUP BY away_team_name
)
SELECT
    h.team,
    h.matches + a.matches   AS total_matches
FROM home_appearances h
JOIN away_appearances a ON h.team = a.team
ORDER BY total_matches DESC;
```
I split the count into two CTEs (one for home, one for away) and joined them together to get each club's true total. Teams with fewer than 380 appearances were promoted or relegated at some point during the 10 seasons.

## 2. How did average goals per match change across seasons?

```sql
SELECT
    season,
    COUNT(*)                                    AS total_matches,
    ROUND(AVG(home_score + away_score), 2)      AS avg_goals_per_match
FROM matches
WHERE status = 'FINISHED'
GROUP BY season
ORDER BY season;
```
I wanted to see if the league was getting more or less open over time. A simple grouped average by season does the job.

## 3. Which teams had the best home win rate?

```sql
SELECT
    home_team_name                                                  AS team,
    COUNT(*)                                                        AS home_matches,
    SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END)       AS home_wins,
    ROUND(
        SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 1
    )                                                               AS home_win_pct
FROM matches
WHERE status = 'FINISHED'
GROUP BY home_team_name
ORDER BY home_win_pct DESC
LIMIT 10;
```
Home advantage is not equal across clubs. The top sides tend to win well over 60% of home games and the gap to the bottom of the table is pretty significant.

## 4. Did home advantage drop during COVID?

```sql
SELECT
    season,
    ROUND(
        SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 1
    )   AS home_win_pct,
    ROUND(
        SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 1
    )   AS draw_pct,
    ROUND(
        SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 1
    )   AS away_win_pct
FROM matches
WHERE status = 'FINISHED'
GROUP BY season
ORDER BY season;
```
The 2019/20 season was played behind closed doors. I wanted to check whether the home win rate actually dropped that year compared to normal seasons. The numbers make for an interesting comparison.

## 5. Which teams scored the most goals away from home?

```sql
SELECT
    away_team_name                          AS team,
    COUNT(*)                                AS away_matches,
    SUM(away_score)                         AS total_away_goals,
    ROUND(AVG(away_score), 2)               AS avg_away_goals
FROM matches
WHERE status = 'FINISHED'
GROUP BY away_team_name
ORDER BY avg_away_goals DESC
LIMIT 10;
```
Scoring away from home is harder than it looks. This shows which teams managed it consistently rather than just in the odd game.

## 6. How often did matches end with 3 or more goals?

```sql
SELECT
    season,
    COUNT(*)                                                                AS total_matches,
    SUM(CASE WHEN home_score + away_score >= 3 THEN 1 ELSE 0 END)          AS high_scoring,
    ROUND(
        SUM(CASE WHEN home_score + away_score >= 3 THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 1
    )                                                                       AS high_scoring_pct
FROM matches
WHERE status = 'FINISHED'
GROUP BY season
ORDER BY season;
```
A rough measure of how open each season was. Not the most sophisticated metric but it gives a quick feel for how attacking the football was in a given year.

## 7. Which season had the closest top-4 finish?

```sql
SELECT
    season,
    MAX(points)                         AS first_place_pts,
    MIN(points)                         AS fourth_place_pts,
    MAX(points) - MIN(points)           AS gap_1st_to_4th
FROM standings
WHERE position <= 4
GROUP BY season
ORDER BY gap_1st_to_4th ASC;
```
Champions League qualification is worth a huge amount of money so I was curious which seasons had the tightest race for those four spots. A small gap means the battle went right to the end of the season.

## 8. Which clubs finished in the top 4 most often?

```sql
SELECT
    team_name,
    COUNT(*)    AS top_4_finishes
FROM standings
WHERE position <= 4
GROUP BY team_name
ORDER BY top_4_finishes DESC
LIMIT 8;
```
This just counts how many times each club landed in the top four across the 10 seasons. It is a decent measure of long-term consistency at the top of the league.

## 9. Which stadiums saw the most goals on average? (JOIN)

```sql
SELECT
    t.venue,
    t.name                                      AS home_team,
    COUNT(m.id)                                 AS matches_played,
    ROUND(AVG(m.home_score + m.away_score), 2)  AS avg_goals_per_match
FROM matches m
JOIN teams t ON m.home_team_id = t.id
WHERE m.status = 'FINISHED'
  AND t.venue IS NOT NULL
GROUP BY t.venue, t.name
ORDER BY avg_goals_per_match DESC
LIMIT 10;
```
Joined the matches table to teams on home_team_id to bring in stadium names. Some grounds tend to produce more open games than others regardless of who is playing.

## 10. Full 2023/24 standings with club details (JOIN)

```sql
SELECT
    s.position,
    s.team_name,
    s.points,
    s.goals_for,
    s.goals_against,
    s.goals_for - s.goals_against   AS goal_difference,
    t.venue
FROM standings s
JOIN teams t ON s.team_id = t.id
WHERE s.season = 2023
ORDER BY s.position;
```
A straightforward join between standings and teams to pull club details alongside the final league table. This is the kind of query you would use as a base for a season summary report.

## 11. How many home goals did each title winner average? (JOIN)

```sql
SELECT
    m.home_team_name                            AS team,
    m.season,
    s.position                                  AS final_position,
    ROUND(AVG(m.home_score), 2)                 AS avg_home_goals
FROM matches m
JOIN standings s
    ON  m.home_team_id = s.team_id
    AND m.season       = s.season
WHERE m.status = 'FINISHED'
GROUP BY m.home_team_name, m.season, s.position
HAVING s.position = 1
ORDER BY avg_home_goals DESC;
```
This joins matches and standings on both team ID and season so each match row picks up the correct end-of-season position. HAVING then filters it down to title winners only.

## 12. Total goals per team combining home and away (CTE)

```sql
WITH home_goals AS (
    SELECT home_team_name AS team, SUM(home_score) AS goals
    FROM matches
    WHERE status = 'FINISHED'
    GROUP BY home_team_name
),
away_goals AS (
    SELECT away_team_name AS team, SUM(away_score) AS goals
    FROM matches
    WHERE status = 'FINISHED'
    GROUP BY away_team_name
)
SELECT
    h.team,
    h.goals                         AS home_goals,
    a.goals                         AS away_goals,
    h.goals + a.goals               AS total_goals,
    ROUND(a.goals * 100.0
        / (h.goals + a.goals), 1)   AS away_goal_pct
FROM home_goals h
JOIN away_goals a ON h.team = a.team
ORDER BY total_goals DESC
LIMIT 10;
```
Two CTEs split each team's goals by venue, then a join combines them. The away_goal_pct column shows what share of a team's scoring came on the road, which gives you a sense of how dependent they were on playing at home.

## 13. Rank teams by points within each season (Window Function)

```sql
SELECT
    season,
    team_name,
    points,
    RANK() OVER (
        PARTITION BY season
        ORDER BY points DESC
    )   AS season_rank
FROM standings
ORDER BY season, season_rank;
```
RANK() with PARTITION BY season gives each team a rank within their own season rather than across the whole dataset. Without the partition you would just be ranking all rows together which is not what you want here.

## 14. How did each team's league position change year on year? (CTE + Window Function)

```sql
WITH yearly_positions AS (
    SELECT
        team_name,
        season,
        position,
        LAG(position) OVER (
            PARTITION BY team_name
            ORDER BY season
        )   AS prev_season_position
    FROM standings
)
SELECT
    team_name,
    season,
    position                                    AS current_position,
    prev_season_position,
    prev_season_position - position             AS positions_gained
FROM yearly_positions
WHERE prev_season_position IS NOT NULL
ORDER BY positions_gained DESC
LIMIT 15;
```
LAG() inside the CTE looks back one row per team (partitioned by team_name so the window resets for each club) to grab the previous season's position. A positive positions_gained means the team climbed the table that year. The WHERE filter removes the first season for each club since there is no prior year to compare against.

*Queries written against a SQLite database sourced from the Football-Data.org API.*
