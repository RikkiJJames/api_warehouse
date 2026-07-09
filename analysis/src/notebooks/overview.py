import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Media Overview

    A single pane of glass over everything I've listened to, watched, and
    read — pulled straight from my `api_warehouse` marts and refreshed
    every time this app runs.

    - **Spotify** — every track play, enriched with popularity, duration
      and per-track play counts across the last week, month, year and
      all-time.
    - **Trakt** — your movie and show watch history, ratings, watchlist
      and genre breakdown.
    - **Hardcover** — books finished, currently reading, and want-to-read,
      with yearly reading stats.

    Use the **Overview** tab for the cross-source summary below, or jump
    into **Spotify**, **Trakt**, or **Hardcover** for source-specific
    breakdowns, filters, and leaderboards.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    from datetime import timedelta, datetime, timezone
    from pathlib import Path

    return Path, alt, datetime, mo, pd, timedelta, timezone


@app.cell
def _():
    # import sys
    # ROOT_DIR = Path.cwd().resolve()
    # sys.path.insert(0, ROOT_DIR)
    return


@app.cell
def _():
    from analysis.src.loader.data_loader import DataLoader

    return (DataLoader,)


@app.cell
def _(Path):
    SRC_PATH = Path(__file__).parents[1]
    SQL_PATH = SRC_PATH / "sql"
    return (SQL_PATH,)


@app.cell
def _(DataLoader, SQL_PATH):
    data_loader = DataLoader()
    data = data_loader.load_data(file_dir=SQL_PATH)
    return (data,)


@app.cell
def _(data, pd):
    enriched_track_df = data['enriched_track']
    enriched_track_df['release_date'] = pd.to_datetime(enriched_track_df['release_date'], format='mixed')
    enriched_track_df['decade'] = (enriched_track_df['release_date'].dt.year // 10) * 10
    return (enriched_track_df,)


@app.cell
def _(data):
    track_df = data['track']
    return (track_df,)


@app.cell
def _(data):
    history_df = data['watch_history']
    return (history_df,)


@app.cell
def _(data):
    dim_movies_df = data['dim_movies']
    fct_movie_stats_df =data['fct_movie_stats']
    movies_df = dim_movies_df.merge(fct_movie_stats_df, on="trakt_movie_id", how="left")
    return (movies_df,)


@app.cell
def _(data):
    dim_shows_df = data['dim_shows']
    fct_show_stats_df = data['fct_show_stats']
    shows_df = dim_shows_df.merge(fct_show_stats_df, on="trakt_show_id", how="left")
    return (shows_df,)


@app.cell
def _(data):
    watchlist_df = data['watchlist']
    return (watchlist_df,)


@app.cell
def _(data):
    genre_stats_df = data['fct_genre_stats']
    return (genre_stats_df,)


@app.cell
def _(data, pd):
    # An empty result set comes back with zero columns (pd.DataFrame([])), which
    # breaks every downstream ["col"] lookup and Altair encoding — fall back to
    # a correctly-typed empty frame so the Hardcover tabs render (empty) instead
    # of erroring when no books have been synced/finished yet.
    reading_history_df = data['reading_history']
    if reading_history_df.empty:
        reading_history_df = pd.DataFrame({
            'user_book_id': pd.Series(dtype='int64'),
            'book_id': pd.Series(dtype='int64'),
            'title': pd.Series(dtype='object'),
            'pages': pd.Series(dtype='float64'),
            'my_rating': pd.Series(dtype='float64'),
            'read_started_at': pd.Series(dtype='datetime64[ns]'),
            'read_finished_at': pd.Series(dtype='datetime64[ns]'),
        })
    return (reading_history_df,)


@app.cell
def _(data, pd):
    reading_list_df = data['reading_list']
    if reading_list_df.empty:
        reading_list_df = pd.DataFrame({
            'user_book_id': pd.Series(dtype='int64'),
            'status': pd.Series(dtype='object'),
            'status_at': pd.Series(dtype='datetime64[ns]'),
            'book_id': pd.Series(dtype='int64'),
            'title': pd.Series(dtype='object'),
            'pages': pd.Series(dtype='float64'),
            'release_date': pd.Series(dtype='object'),
        })
    return (reading_list_df,)


@app.cell
def _(data, pd):
    reading_stats_df = data['fct_reading_stats']
    if reading_stats_df.empty:
        reading_stats_df = pd.DataFrame({
            'year': pd.Series(dtype='datetime64[ns]'),
            'books_read': pd.Series(dtype='int64'),
            'pages_read': pd.Series(dtype='int64'),
            'avg_rating': pd.Series(dtype='float64'),
            'avg_pages_per_book': pd.Series(dtype='float64'),
        })
    return (reading_stats_df,)


@app.cell
def _(history_df, mo, pd, reading_history_df, track_df):
    _spotify_since = track_df['played_at'].min()
    _trakt_since = history_df['watched_at'].min()
    _hardcover_since = reading_history_df['read_finished_at'].min()

    def _since_caption(ts, verb):
        if pd.isna(ts):
            return f"nothing {verb} yet"
        return f"since {ts:%b %d, %Y}"

    overview_stats = mo.hstack(
        [
            mo.stat(
                value=f"{len(track_df):,}",
                label="Spotify plays logged",
                caption=_since_caption(_spotify_since, "played"),
                bordered=True,
            ),
            mo.stat(
                value=f"{len(history_df):,}",
                label="Trakt items watched",
                caption=_since_caption(_trakt_since, "watched"),
                bordered=True,
            ),
            mo.stat(
                value=f"{len(reading_history_df):,}",
                label="Hardcover books read",
                caption=_since_caption(_hardcover_since, "finished"),
                bordered=True,
            ),
        ],
        gap=2,
    )

    overview_summary = mo.vstack(
        [
            mo.md("## At a Glance"),
            mo.md(
                "A quick pulse check across all three sources before diving into "
                "the tabs above — each card shows how much history has been "
                "captured so far and how far back it goes."
            ),
            overview_stats,
        ]
    )
    return (overview_summary,)


@app.cell
def _(alt, history_df, mo, pd, reading_history_df, track_df):
    _spotify_daily = (
        track_df.assign(date=pd.to_datetime(track_df['played_at']).dt.date.astype(str))
        .groupby('date').size().reset_index(name='count').assign(source='Spotify')
    )
    _trakt_daily = (
        history_df.assign(date=pd.to_datetime(history_df['watched_at']).dt.date.astype(str))
        .groupby('date').size().reset_index(name='count').assign(source='Trakt')
    )
    _hardcover_daily = (
        reading_history_df.dropna(subset=['read_finished_at'])
        .assign(date=pd.to_datetime(reading_history_df['read_finished_at']).dt.date.astype(str))
        .groupby('date').size().reset_index(name='count').assign(source='Hardcover')
    )
    _combined_daily = pd.concat([_spotify_daily, _trakt_daily, _hardcover_daily], ignore_index=True)

    combined_activity_chart = mo.ui.altair_chart(
        alt.Chart(_combined_daily).mark_line(point=True).encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('count:Q', title='Events'),
            color=alt.Color('source:N', title='Source'),
            tooltip=['date', 'source', 'count'],
        ).properties(title='Daily Activity — Spotify Plays, Trakt Watches & Hardcover Finishes', height=350)
    )
    return (combined_activity_chart,)


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
    number_of_days = mo.ui.slider(0, number_of_days_listened, value=0, label="Number of Days")
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
            mo.md("Rank every track you've played, ranked by whichever window matters to you right now."),
            mo.hstack([metric, top_n]),
            top_tracks_df,
            mo.md("## Popularity vs. Play Count"),
            mo.md(
                "Spotify's global popularity score against how often *you* "
                "actually play a track — the top-left quadrant is where your "
                "hidden gems live, top-right is where your taste lines up "
                "with the mainstream."
            ),
            pop_scatter,
            mo.md("## Plays by Track Duration"),
            mo.md("Total plays bucketed by track length, so you can see whether you gravitate towards short, medium, or long cuts."),
            duration_chart,
            mo.md("## Tracks by Decade"),
            mo.md("Filter your library down to one or more release decades and see which tracks from those eras get the most plays."),
            decade_selector,
            decade_tracks_df,
            mo.md("## Listening Time Selector"),
            mo.md("Drag the slider to set a lookback window and see total listening time logged within it."),
            mo.hstack([weekly_listening_time, number_of_days]),
        ]),
        "Artists": mo.vstack([
            mo.md("## Top Artists"),
            mo.md("Every artist you've listened to, ranked by total plays, with unique track count and average popularity."),
            artist_df.head(20),
            mo.md("## Artist Deep Dive"),
            mo.md("Pick an artist below to see every track of theirs you've played and your total listening time with them."),
            artist_selector,
            mo.md(f"**Total listening time:** {time_listened}"),
            artist_detail_df,
        ]),
        "Albums": mo.vstack([
            mo.md("## Album Leaderboard"),
            mo.md("Albums ranked by total plays across their tracks, alongside how much of each album you've actually explored."),
            album_df.head(30),
            mo.md("## Explicit vs Clean"),
            mo.md("Share of your total plays that come from explicit vs. clean tracks."),
            explicit_chart,
        ]),
    })
    return (spotify_view,)


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
            mo.md("Number of movies and episodes watched per day — a quick way to spot binge sessions."),
            activity_chart,
            mo.md("## Timeline"),
            mo.md("The full watch log, filterable by media type, most recent first."),
            media_type_filter,
            filtered_history_df,
        ]),
        "Movies": mo.vstack([
            mo.md("## Top Movies"),
            mo.md("Every movie you've watched, sortable by watch count, total runtime, or your rating."),
            mo.hstack([movie_sort, movie_top_n]),
            top_movies_df,
            mo.md("## Rating Distribution"),
            mo.md("How your personal movie ratings are spread out."),
            rating_hist,
        ]),
        "Shows": mo.vstack([
            mo.md("## Top Shows"),
            mo.md("Shows ranked by episodes watched, completion percentage, or rating."),
            mo.hstack([show_sort, show_top_n]),
            top_shows_df,
        ]),
        "Watchlist": mo.vstack([
            mo.md("## Watchlist"),
            mo.md("Movies and shows queued up but not yet watched."),
            watchlist_df,
        ]),
        "Genres": mo.vstack([
            mo.md("## Genre Breakdown"),
            mo.md("Which genres dominate your watch history, split by movies vs. shows."),
            genre_chart,
            genre_stats_df,
        ]),
    })
    return (trakt_view,)


@app.cell
def _(mo):
    book_sort = mo.ui.dropdown(
        options={"Finished Date": "read_finished_at", "Rating": "my_rating", "Pages": "pages"},
        value="Finished Date",
        label="Sort by",
    )
    book_top_n = mo.ui.slider(5, 50, value=20, label="Top N")
    return book_sort, book_top_n


@app.cell
def _(book_sort, book_top_n, reading_history_df):
    top_books_df = (
        reading_history_df[["title", "pages", "my_rating", "read_started_at", "read_finished_at"]]
        .sort_values(book_sort.value, ascending=False)
        .head(book_top_n.value)
        .reset_index(drop=True)
    )
    return (top_books_df,)


@app.cell
def _(alt, mo, reading_history_df):
    _agg = reading_history_df[["my_rating"]].dropna()
    book_rating_hist = mo.ui.altair_chart(
        alt.Chart(_agg).mark_bar().encode(
            x=alt.X("my_rating:Q", bin=alt.Bin(step=0.5), title="Rating"),
            y=alt.Y("count():Q", title="Books"),
            tooltip=["count()"],
        ).properties(title="Personal Rating Distribution", height=200)
    )
    return (book_rating_hist,)


@app.cell
def _(alt, mo, reading_stats_df):
    reading_stats_chart = mo.ui.altair_chart(
        alt.Chart(reading_stats_df).mark_bar().encode(
            x=alt.X("year:T", title="Year"),
            y=alt.Y("books_read:Q", title="Books Read"),
            tooltip=["year", "books_read", "pages_read", "avg_rating"],
        ).properties(title="Books Read per Year", height=250)
    )
    return (reading_stats_chart,)


@app.cell
def _(mo, reading_list_df):
    reading_list_status_filter = mo.ui.multiselect(
        options=sorted(reading_list_df["status"].unique().tolist()),
        value=sorted(reading_list_df["status"].unique().tolist()),
        label="Status",
    )
    return (reading_list_status_filter,)


@app.cell
def _(reading_list_df, reading_list_status_filter):
    filtered_reading_list_df = (
        reading_list_df[reading_list_df["status"].isin(reading_list_status_filter.value)]
        [["status", "status_at", "title", "pages", "release_date"]]
        .reset_index(drop=True)
    )
    return (filtered_reading_list_df,)


@app.cell
def _(
    book_rating_hist,
    book_sort,
    book_top_n,
    filtered_reading_list_df,
    mo,
    reading_list_status_filter,
    reading_stats_chart,
    reading_stats_df,
    top_books_df,
):
    hardcover_view = mo.ui.tabs({
        "Read Books": mo.vstack([
            mo.md("## Top Books"),
            mo.md("Every finished book, sortable by when you finished it, your rating, or page count."),
            mo.hstack([book_sort, book_top_n]),
            top_books_df,
            mo.md("## Rating Distribution"),
            mo.md("How your personal book ratings are spread out."),
            book_rating_hist,
        ]),
        "Reading List": mo.vstack([
            mo.md("## Currently Reading & Want to Read"),
            mo.md("Everything on deck — filter by status to see what's in progress vs. still on the list."),
            reading_list_status_filter,
            filtered_reading_list_df,
        ]),
        "Stats": mo.vstack([
            mo.md("## Books Read per Year"),
            mo.md("Books finished per calendar year, alongside pages and average rating."),
            reading_stats_chart,
            reading_stats_df,
        ]),
    })
    return (hardcover_view,)


@app.cell
def _(
    combined_activity_chart,
    hardcover_view,
    mo,
    overview_summary,
    spotify_view,
    trakt_view,
):
    mo.ui.tabs({
        "Overview": mo.vstack([
            overview_summary,
            mo.md("## Daily Activity Across Sources"),
            mo.md(
                "Every logged Spotify play, Trakt watch, and finished Hardcover "
                "book, plotted by day so you can spot binges, dry spells, and "
                "how the three habits overlap over time."
            ),
            combined_activity_chart,
            mo.callout(
                "Hover any point for the exact count, or switch to the "
                "Spotify, Trakt, or Hardcover tabs above for source-specific "
                "leaderboards and filters.",
                kind="info",
            ),
        ]),
        "Spotify": spotify_view,
        "Trakt": trakt_view,
        "Hardcover": hardcover_view,
    })
    return


if __name__ == "__main__":
    app.run()
