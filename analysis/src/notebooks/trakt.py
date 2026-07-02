import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Trakt Watch History

    Explore your watch history powered by the `marts.trakt` dbt models.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model Structure

    ```mermaid
    TD
        subgraph src["Raw (trakt schema)"]
            s_wm[(watched_movies)]
            s_we[(watched_episodes)]
            s_wlm[(watchlist_movies)]
            s_wls[(watchlist_shows)]
        end

        subgraph stg["Staging"]
            stg_wm[stg_watched_movies]
            stg_we[stg_watched_episodes]
            stg_wlm[stg_watchlist_movies]
            stg_wls[stg_watchlist_shows]
        end

        subgraph int["Intermediate"]
            int_m[int_movies]
            int_s[int_shows]
            int_ss[int_show_watch_stats]
        end

        subgraph dims["Marts — Dimensions"]
            dim_m[dim_movies]
            dim_s[dim_shows]
            dim_a[dim_anime]
            dim_gm[dim_genre_map]
        end

        subgraph facts["Marts — Facts"]
            fct_wh[fct_watch_history]
            fct_ms[fct_movie_stats]
            fct_ss[fct_show_stats]
            fct_wl[fct_watchlist]
            fct_gs[fct_genre_stats]
        end

        s_wm --> stg_wm
        s_we --> stg_we
        s_wlm --> stg_wlm
        s_wls --> stg_wls

        stg_wm --> int_m
        stg_we --> int_s
        stg_we --> int_ss

        int_m --> dim_m
        int_s --> dim_s
        dim_s --> dim_a
        dim_m & dim_s --> dim_gm

        stg_wm & stg_we --> fct_wh
        stg_wm --> fct_ms
        int_ss & dim_s --> fct_ss
        stg_wlm & stg_wls --> fct_wl
        dim_gm --> fct_gs
    ```
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    from dotenv import load_dotenv
    from src.db.core.db import Database, DATABASE_CONFIG

    return DATABASE_CONFIG, Database, alt, load_dotenv, mo, pd


@app.cell
def _(load_dotenv):
    load_dotenv()
    return


@app.cell
def _(DATABASE_CONFIG, Database):
    db = Database(DATABASE_CONFIG)
    db.connect()
    return (db,)


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
    mo.ui.tabs({
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
    return


if __name__ == "__main__":
    app.run()
