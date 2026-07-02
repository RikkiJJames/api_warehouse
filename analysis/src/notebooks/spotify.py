import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Spotify Listening History

    Explore your Spotify listening data powered by the `intermediate.int_track_enriched` dbt model.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model Structure

    ```mermaid
    flowchart TD
        subgraph src["Raw (spotify schema)"]
            s_rp[(recently_played)]
            s_track[(track)]
            s_artist[(artist)]
            s_album[(album)]
        end

        subgraph stg["Staging"]
            stg_rp[recently_played]
            stg_track[track]
            stg_artist[artist]
            stg_album[album]
        end

        subgraph int["Intermediate"]
            int_te[int_track_enriched]
        end

        subgraph dims["Marts — Dimensions"]
            dim_t[dim_tracks]
            dim_ar[dim_artists]
            dim_al[dim_albums]
        end

        subgraph facts["Marts — Facts"]
            fct_ph[fct_play_history]
            fct_ts[fct_track_stats]
            fct_as[fct_artist_stats]
        end

        s_rp --> stg_rp
        s_track --> stg_track
        s_artist --> stg_artist
        s_album --> stg_album

        stg_track & stg_artist & stg_album & stg_rp --> int_te

        stg_track & stg_artist & stg_album --> dim_t
        stg_artist --> dim_ar
        stg_album --> dim_al

        stg_rp --> fct_ph
        stg_rp --> fct_ts
        dim_t --> fct_as
        fct_ts --> fct_as
    ```
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
    loaded=load_dotenv()
    return


@app.cell
def _(DATABASE_CONFIG, Database):
    db = Database(DATABASE_CONFIG)
    db.connect()
    return (db,)


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
def _(timedelta):
    def get_listening_time(duration_column) -> str:
        total_seconds = int(duration_column.sum() / 1000)
        return str(timedelta(seconds=total_seconds))

    return (get_listening_time,)


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
    mo.ui.tabs({
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
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
