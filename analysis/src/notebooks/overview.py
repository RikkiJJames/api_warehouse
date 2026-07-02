import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Media Overview

    Combined view of your Spotify listening history and Trakt watch history.
    Switch tabs below for a cross-source summary or to drill into either source individually.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    from datetime import timedelta, datetime, timezone
    from dotenv import load_dotenv
    from src.db.core.db import Database, DATABASE_CONFIG

    return (
        DATABASE_CONFIG,
        Database,
        alt,
        datetime,
        load_dotenv,
        mo,
        pd,
        timedelta,
        timezone,
    )


@app.cell
def _(load_dotenv):
    loaded = load_dotenv()
    return


@app.cell
def _(DATABASE_CONFIG, Database):
    db = Database(DATABASE_CONFIG)
    db.connect()
    return (db,)


# ── Spotify data ─────────────────────────────────────────────────────────────


@app.cell
def _(db, pd):
    enriched_track_df = pd.DataFrame(
        db.execute_query("SELECT * FROM intermediate.int_track_enriched;")
    )
    enriched_track_df['release_date'] = pd.to_datetime(enriched_track_df['release_date'], format='mixed')
    enriched_track_df['decade'] = (enriched_track_df['release_date'].dt.year // 10) * 10
    return (enriched_track_df,)


@app.cell
def _(db, pd):
    track_df = pd.DataFrame(db.execute_query("SELECT * FROM staging.recently_played;"))
    return (track_df,)


# ── Trakt data ───────────────────────────────────────────────────────────────


@app.cell
def _(db, pd):
    history_df = pd.DataFrame(db.execute_query("SELECT * FROM marts.fct_watch_history ORDER BY watched_at DESC;"))
    return (history_df,)


@app.cell
def _(db, pd):
    dim_movies_df = pd.DataFrame(db.execute_query("SELECT * FROM marts.dim_movies;"))
    fct_movie_stats_df = pd.DataFrame(db.execute_query("SELECT * FROM marts.fct_movie_stats;"))
    movies_df = dim_movies_df.merge(fct_movie_stats_df, on="trakt_movie_id", how="left")
    return (movies_df,)


@app.cell
def _(db, pd):
    dim_shows_df = pd.DataFrame(db.execute_query("SELECT * FROM marts.dim_shows;"))
    fct_show_stats_df = pd.DataFrame(db.execute_query("SELECT * FROM marts.fct_show_stats;"))
    shows_df = dim_shows_df.merge(fct_show_stats_df, on="trakt_show_id", how="left")
    return (shows_df,)


@app.cell
def _(db, pd):
    watchlist_df = pd.DataFrame(db.execute_query("SELECT * FROM marts.fct_watchlist ORDER BY rank;"))
    return (watchlist_df,)


@app.cell
def _(db, pd):
    genre_stats_df = pd.DataFrame(db.execute_query("SELECT * FROM marts.fct_genre_stats ORDER BY title_count DESC;"))
    return (genre_stats_df,)


# ── Overview tab: cross-source summary ──────────────────────────────────────


@app.cell
def _(history_df, mo, track_df):
    overview_summary = mo.md(f"""
    **Spotify plays logged:** {len(track_df)}
    **Trakt items watched:** {len(history_df)}
    **Spotify tracked since:** {track_df['played_at'].min()}
    **Trakt tracked since:** {history_df['watched_at'].min()}
    """)
    return (overview_summary,)


@app.cell
def _(alt, history_df, mo, pd, track_df):
    _spotify_daily = (
        track_df.assign(date=pd.to_datetime(track_df['played_at']).dt.date.astype(str))
        .groupby('date').size().reset_index(name='count').assign(source='Spotify')
    )
    _trakt_daily = (
        history_df.assign(date=pd.to_datetime(history_df['watched_at']).dt.date.astype(str))
        .groupby('date').size().reset_index(name='count').assign(source='Trakt')
    )
    _combined_daily = pd.concat([_spotify_daily, _trakt_daily], ignore_index=True)

    combined_activity_chart = mo.ui.altair_chart(
        alt.Chart(_combined_daily).mark_line(point=True).encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('count:Q', title='Events'),
            color=alt.Color('source:N', title='Source'),
            tooltip=['date', 'source', 'count'],
        ).properties(title='Daily Activity — Spotify Plays vs. Trakt Watches', height=350)
    )
    return (combined_activity_chart,)


# ── Spotify tab: Tracks ──────────────────────────────────────────────────────


@app.cell
def _(mo):
    metric = mo.ui.dropdown(
        options={
            "Weekly Plays": "weekly_plays",
            "Monthly Plays": "monthly_plays",
            "Annual Plays": "annual_plays",
            "All Time": "times_played",
        },
        value="Weekly Plays",
        label="Ranking metric"
    )
    top_n = mo.ui.slider(1, 50, value=10, label="Top N")
    return metric, top_n


@app.cell
def _(enriched_track_df, metric, top_n):
    top_tracks_df = (
        enriched_track_df[['track_name', 'artist_name', 'album_name', 'popularity', 'weekly_plays', 'monthly_plays', 'annual_plays', 'times_played']]
        .sort_values(by=metric.value, ascending=False)
        .head(top_n.value)
        .reset_index(drop=True)
    )
    return (top_tracks_df,)


@app.cell
def _(alt, enriched_track_df, mo, pd):
    _pop_mid = 50
    _plays_mid = int(enriched_track_df['times_played'].median())

    _scatter = alt.Chart(enriched_track_df).mark_circle(size=60, opacity=0.6).encode(
        x=alt.X('popularity:Q', title='Spotify Popularity (0–100)'),
        y=alt.Y('times_played:Q', title='Times Played'),
        tooltip=['track_name', 'artist_name', 'popularity', 'times_played']
    )
    _vline = alt.Chart(pd.DataFrame({'x': [_pop_mid]})).mark_rule(strokeDash=[4, 4], color='gray').encode(x='x:Q')
    _hline = alt.Chart(pd.DataFrame({'y': [_plays_mid]})).mark_rule(strokeDash=[4, 4], color='gray').encode(y='y:Q')
    _labels = alt.Chart(pd.DataFrame([
        {'x': 75, 'y': enriched_track_df['times_played'].max() * 0.95, 'label': 'Mainstream faves'},
        {'x': 10, 'y': enriched_track_df['times_played'].max() * 0.95, 'label': 'Hidden gems'},
        {'x': 75, 'y': _plays_mid * 0.1,                               'label': 'Popular, not for you'},
        {'x': 10, 'y': _plays_mid * 0.1,                               'label': 'Undiscovered'},
    ])).mark_text(color='gray', fontSize=11, fontStyle='italic').encode(
        x='x:Q', y='y:Q', text='label:N'
    )
    pop_scatter = mo.ui.altair_chart(
        (_scatter + _vline + _hline + _labels).properties(title='Popularity vs. Your Play Count', height=350)
    )
    return (pop_scatter,)


@app.cell
def _(enriched_track_df, mo):
    decades = sorted(int(d) for d in enriched_track_df['decade'].unique())
    decade_selector = mo.ui.multiselect(options=decades, value=[decades[0]], label="Decade")
    return (decade_selector,)


@app.cell
def _(decade_selector, enriched_track_df):
    decade_tracks_df = (
        enriched_track_df[enriched_track_df['decade'].isin(decade_selector.value)]
        [['track_name', 'artist_name', 'decade', 'times_played', 'popularity']]
        .sort_values(by=['decade', 'times_played'], ascending=[True, False])
        .reset_index(drop=True)
    )
    return (decade_tracks_df,)


@app.cell
def _(alt, enriched_track_df, mo):
    def _bin(ms):
        mins = ms / 60000
        if mins < 3:
            return 'Short (<3 min)'
        elif mins < 5:
            return 'Medium (3–5 min)'
        return 'Long (>5 min)'

    _order = ['Short (<3 min)', 'Medium (3–5 min)', 'Long (>5 min)']
    _dur_agg = (
        enriched_track_df.assign(duration_bin=enriched_track_df['duration_ms'].apply(_bin))
        .groupby('duration_bin')
        .agg(total_plays=('times_played', 'sum'), track_count=('track_name', 'nunique'))
        .reset_index()
    )
    duration_chart = mo.ui.altair_chart(
        alt.Chart(_dur_agg).mark_bar().encode(
            x=alt.X('duration_bin:N', title='Track Length', sort=_order),
            y=alt.Y('total_plays:Q', title='Total Plays'),
            color=alt.Color('duration_bin:N', legend=None, sort=_order),
            tooltip=['duration_bin', 'total_plays', 'track_count']
        ).properties(title='Plays by Track Duration', height=250)
    )
    return (duration_chart,)


@app.cell
def _(timedelta):
    def get_listening_time(duration_column) -> str:
        total_seconds = int(duration_column.sum() / 1000)
        return str(timedelta(seconds=total_seconds))

    return (get_listening_time,)


@app.cell
def _(mo, track_df):
    number_of_days_listened = (track_df['played_at'].max() - track_df['played_at'].min()).days
    number_of_days = mo.ui.slider(1, number_of_days_listened, value=1, label="Number of Days")
    return (number_of_days,)


@app.cell
def _(
    datetime,
    get_listening_time,
    number_of_days,
    timedelta,
    timezone,
    track_df,
):
    current_date = datetime.now(timezone.utc)

    listened_this_week = track_df.iloc[track_df['played_at'] >= (current_date - timedelta(days=number_of_days.value))]

    weekly_listening_time = get_listening_time(listened_this_week['track_duration_ms'])
    return (weekly_listening_time,)


@app.cell
def _(alt, enriched_track_df, mo):
    _agg = (
        enriched_track_df.groupby('explicit')['times_played']
        .sum()
        .reset_index()
        .assign(label=lambda df: df['explicit'].map({True: 'Explicit', False: 'Clean'}))
    )
    explicit_chart = mo.ui.altair_chart(
        alt.Chart(_agg).mark_arc(innerRadius=50).encode(
            theta=alt.Theta('times_played:Q'),
            color=alt.Color('label:N', title='Content'),
            tooltip=['label', 'times_played']
        ).properties(title='Explicit vs Clean — Play Count', height=250)
    )
    return (explicit_chart,)


# ── Spotify tab: Artists ─────────────────────────────────────────────────────


@app.cell
def _(enriched_track_df):
    artist_df = (
        enriched_track_df.groupby('artist_name')
        .agg(
            times_played=('times_played', 'sum'),
            unique_tracks=('track_name', 'nunique'),
            avg_popularity=('popularity', 'mean'),
        )
        .round({'avg_popularity': 1})
        .sort_values('times_played', ascending=False)
        .reset_index()
    )
    return (artist_df,)


@app.cell
def _(artist_df, mo):
    artist_selector = mo.ui.dropdown(
        options=sorted(artist_df['artist_name'].tolist()),
        value=artist_df['artist_name'].iloc[0],
        label="Select artist"
    )
    return (artist_selector,)


@app.cell
def _(artist_selector, enriched_track_df, get_listening_time):
    _mask = enriched_track_df['artist_name'] == artist_selector.value
    artist_detail_df = (
        enriched_track_df[_mask]
        [['track_name', 'album_name', 'popularity', 'times_played', 'weekly_plays', 'monthly_plays']]
        .sort_values('times_played', ascending=False)
        .reset_index(drop=True)
    )
    time_listened = get_listening_time(enriched_track_df[_mask]['duration_ms'])
    return artist_detail_df, time_listened


# ── Spotify tab: Albums ──────────────────────────────────────────────────────


@app.cell
def _(enriched_track_df):
    album_df = (
        enriched_track_df.groupby(['album_name', 'artist_name'])
        .agg(
            times_played=('times_played', 'sum'),
            unique_tracks=('track_name', 'nunique'),
            total_tracks=('total_tracks', 'first'),
        )
        .sort_values('times_played', ascending=False)
        .reset_index()
    )
    return (album_df,)


@app.cell
def _(
    album_df,
    artist_detail_df,
    artist_df,
    artist_selector,
    decade_selector,
    decade_tracks_df,
    duration_chart,
    explicit_chart,
    metric,
    mo,
    number_of_days,
    pop_scatter,
    time_listened,
    top_n,
    top_tracks_df,
    weekly_listening_time,
):
    spotify_view = mo.ui.tabs({
        "Tracks": mo.vstack([
            mo.md("## Top Tracks"),
            mo.hstack([metric, top_n]),
            top_tracks_df,
            mo.md("## Popularity vs. Play Count"),
            pop_scatter,
            mo.md("## Plays by Track Duration"),
            duration_chart,
            mo.md("## Tracks by Decade"),
            decade_selector,
            decade_tracks_df,
            mo.md(f"## Listening Time Selector:"),
            mo.hstack([weekly_listening_time, number_of_days]),
        ]),
        "Artists": mo.vstack([
            mo.md("## Top Artists"),
            artist_df.head(20),
            mo.md("## Artist Deep Dive"),
            artist_selector,
            mo.md(f"**Total listening time:** {time_listened}"),
            artist_detail_df,
        ]),
        "Albums": mo.vstack([
            mo.md("## Album Leaderboard"),
            album_df.head(30),
            mo.md("## Explicit vs Clean"),
            explicit_chart,
        ]),
    })
    return (spotify_view,)


# ── Trakt tab ────────────────────────────────────────────────────────────────


@app.cell
def _(history_df, mo):
    media_type_filter = mo.ui.multiselect(
        options=sorted(history_df["media_type"].unique().tolist()),
        value=sorted(history_df["media_type"].unique().tolist()),
        label="Media type",
    )
    return (media_type_filter,)


@app.cell
def _(history_df, media_type_filter):
    filtered_history_df = (
        history_df[history_df["media_type"].isin(media_type_filter.value)]
        [["watched_at", "media_type", "title", "show_title", "season", "episode_number", "runtime_mins"]]
        .reset_index(drop=True)
    )
    return (filtered_history_df,)


@app.cell
def _(alt, history_df, mo):
    history_df["date"] = history_df["watched_at"].astype(str).str[:10]
    _daily = history_df.groupby("date").size().reset_index(name="count")
    activity_chart = mo.ui.altair_chart(
        alt.Chart(_daily).mark_bar().encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("count:Q", title="Items Watched"),
            tooltip=["date", "count"],
        ).properties(title="Daily Watch Activity", height=200)
    )
    return (activity_chart,)


@app.cell
def _(mo):
    movie_sort = mo.ui.dropdown(
        options={"Watch Count": "watch_count", "Runtime": "total_runtime_hours", "Rating": "rating"},
        value="Watch Count",
        label="Sort by",
    )
    movie_top_n = mo.ui.slider(5, 50, value=20, label="Top N")
    return movie_sort, movie_top_n


@app.cell
def _(movie_sort, movie_top_n, movies_df):
    top_movies_df = (
        movies_df[["title", "year", "rating", "runtime_mins", "watch_count", "total_runtime_hours", "last_watched_at"]]
        .sort_values(movie_sort.value, ascending=False)
        .head(movie_top_n.value)
        .reset_index(drop=True)
    )
    return (top_movies_df,)


@app.cell
def _(alt, mo, movies_df):
    _agg = movies_df[["rating"]].dropna()
    rating_hist = mo.ui.altair_chart(
        alt.Chart(_agg).mark_bar().encode(
            x=alt.X("rating:Q", bin=alt.Bin(step=0.5), title="Rating"),
            y=alt.Y("count():Q", title="Movies"),
            tooltip=["count()"],
        ).properties(title="Movie Rating Distribution", height=200)
    )
    return (rating_hist,)


@app.cell
def _(mo):
    show_sort = mo.ui.dropdown(
        options={"Episodes Watched": "episodes_watched", "Completion %": "completion_pct", "Rating": "show_rating"},
        value="Episodes Watched",
        label="Sort by",
    )
    show_top_n = mo.ui.slider(5, 50, value=20, label="Top N")
    return show_sort, show_top_n


@app.cell
def _(show_sort, show_top_n, shows_df):
    top_shows_df = (
        shows_df[["show_title", "show_year", "network", "content_type", "show_rating", "episodes_watched", "seasons_watched", "completion_pct", "total_runtime_hours"]]
        .sort_values(show_sort.value, ascending=False)
        .head(show_top_n.value)
        .reset_index(drop=True)
    )
    return (top_shows_df,)


@app.cell
def _(alt, genre_stats_df, mo):
    _top = genre_stats_df.head(15)
    genre_chart = mo.ui.altair_chart(
        alt.Chart(_top).mark_bar().encode(
            x=alt.X("title_count:Q", title="Titles"),
            y=alt.Y("genre:N", sort="-x", title="Genre"),
            color=alt.Color("media_type:N", title="Type"),
            tooltip=["genre", "media_type", "title_count", "total_runtime_mins"],
        ).properties(title="Top Genres by Title Count", height=350)
    )
    return (genre_chart,)


@app.cell
def _(
    activity_chart,
    filtered_history_df,
    genre_chart,
    genre_stats_df,
    media_type_filter,
    mo,
    movie_sort,
    movie_top_n,
    rating_hist,
    show_sort,
    show_top_n,
    top_movies_df,
    top_shows_df,
    watchlist_df,
):
    trakt_view = mo.ui.tabs({
        "Watch History": mo.vstack([
            mo.md("## Activity"),
            activity_chart,
            mo.md("## Timeline"),
            media_type_filter,
            filtered_history_df,
        ]),
        "Movies": mo.vstack([
            mo.md("## Top Movies"),
            mo.hstack([movie_sort, movie_top_n]),
            top_movies_df,
            mo.md("## Rating Distribution"),
            rating_hist,
        ]),
        "Shows": mo.vstack([
            mo.md("## Top Shows"),
            mo.hstack([show_sort, show_top_n]),
            top_shows_df,
        ]),
        "Watchlist": mo.vstack([
            mo.md("## Watchlist"),
            watchlist_df,
        ]),
        "Genres": mo.vstack([
            mo.md("## Genre Breakdown"),
            genre_chart,
            genre_stats_df,
        ]),
    })
    return (trakt_view,)


# ── Top-level assembly ───────────────────────────────────────────────────────


@app.cell
def _(combined_activity_chart, mo, overview_summary, spotify_view, trakt_view):
    mo.ui.tabs({
        "Overview": mo.vstack([
            overview_summary,
            combined_activity_chart,
        ]),
        "Spotify": spotify_view,
        "Trakt": trakt_view,
    })
    return


if __name__ == "__main__":
    app.run()
